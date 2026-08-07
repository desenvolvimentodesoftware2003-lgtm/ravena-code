import os
import json
import time
import logging
from typing import List, Optional, Iterator
from datetime import datetime

from src.core.alimentacao.parsers_externos.wikipedia_dump_parser import (
    WikipediaDumpParser, ArtigoWikipedia
)
from src.core.alimentacao.parsers_externos.wikipedia_parser import (
    WikipediaParser, ItemWikipedia
)
from src.core.alimentacao.alimentador import Alimentador

logger = logging.getLogger("ravena.alimentacao.wikipedia_pipeline")

SAIDA_PADRAO = "data/wikipedia"
ARQUIVO_JSONL = "artigos.jsonl"
ARQUIVO_MANIFEST = "manifest.json"
TAMANHO_MAX_ARQUIVO = 500 * 1024 * 1024

class WikipediaPipeline:
    def __init__(self, projeto_raiz: str, lingua: str = "pt"):
        self._projeto_raiz = projeto_raiz
        self._lingua = lingua
        self._dump_parser = WikipediaDumpParser(lingua=lingua)
        self._api_parser = WikipediaParser(lingua=lingua)
        self._saida = os.path.join(projeto_raiz, SAIDA_PADRAO, lingua)
        os.makedirs(self._saida, exist_ok=True)

    def info_dump(self) -> dict:
        dumps = self._dump_parser.listar_dumps_disponiveis()
        tamanho = self._dump_parser.estimar_tamanho_dump()
        return {
            "lingua": self._lingua,
            "dumps_disponiveis": len(dumps),
            "dump_principal": f"{self._lingua}wiki-latest-pages-articles.xml.bz2",
            "tamanho_estimado_bytes": tamanho,
            "tamanho_estimado_gb": round(tamanho / (1024**3), 2) if tamanho else None,
            "diretorio_saida": self._saida
        }

    def baixar_dump(self, forcar: bool = False) -> Optional[str]:
        caminho_dump = os.path.join(self._saida,
            f"{self._lingua}wiki-latest-pages-articles.xml.bz2")
        if os.path.exists(caminho_dump) and not forcar:
            logger.info(f"Dump ja existe: {caminho_dump}")
            return caminho_dump
        logger.info(f"Baixando dump {self._lingua}wiki...")
        caminho = self._dump_parser.baixar_dump(self._saida, self._lingua)
        return caminho

    def processar_artigos_para_jsonl(self, caminho_dump: str,
                                      max_artigos: Optional[int] = None,
                                      categorias_filtro: Optional[List[str]] = None,
                                      chunk_size: int = 1500) -> str:
        saida_jsonl = os.path.join(self._saida, ARQUIVO_JSONL)
        if os.path.exists(saida_jsonl):
            base, ext = os.path.splitext(ARQUIVO_JSONL)
            saida_jsonl = os.path.join(self._saida, f"{base}_{int(time.time())}{ext}")

        logger.info(f"Processando dump para JSONL: {saida_jsonl}")
        logger.info(f"Max artigos: {max_artigos or 'ilimitado'}")

        start = time.time()
        total_chunks = 0
        total_artigos = 0
        bytes_acumulados = 0
        arquivo_atual = 1

        def _abrir_arquivo(num):
            path = saida_jsonl.replace(".jsonl", f"_{num:03d}.jsonl")
            logger.info(f"Abrindo arquivo: {path}")
            return open(path, "w", encoding="utf-8"), path

        f, caminho_atual = _abrir_arquivo(arquivo_atual)

        try:
            for artigo in self._dump_parser.iterar_artigos(caminho_dump):
                if max_artigos and total_artigos >= max_artigos:
                    break
                if categorias_filtro and not any(
                    c in artigo.categorias for c in categorias_filtro
                ):
                    continue
                chunks = self._dump_parser.chunk_artigo(artigo)
                for pergunta, conteudo, metadados in chunks:
                    registro = {
                        "pergunta": pergunta,
                        "conteudo": conteudo,
                        "fonte": "wikipedia_dump",
                        "metadata": metadados,
                        "timestamp": datetime.now().isoformat()
                    }
                    linha = json.dumps(registro, ensure_ascii=False) + "\n"
                    f.write(linha)
                    total_chunks += 1
                    bytes_acumulados += len(linha.encode("utf-8"))
                    if bytes_acumulados >= TAMANHO_MAX_ARQUIVO:
                        f.close()
                        logger.info(f"Arquivo {caminho_atual} fechado ({bytes_acumulados / 1024**2:.1f} MB)")
                        arquivo_atual += 1
                        bytes_acumulados = 0
                        f, caminho_atual = _abrir_arquivo(arquivo_atual)
                total_artigos += 1
                if total_artigos % 1000 == 0:
                    duracao = time.time() - start
                    logger.info(f"{total_artigos} artigos, {total_chunks} chunks, {duracao:.0f}s")
        finally:
            f.close()

        duracao = time.time() - start
        manifest = {
            "lingua": self._lingua,
            "dump": caminho_dump,
            "total_artigos_processados": total_artigos,
            "total_chunks_gerados": total_chunks,
            "tamanho_total_bytes": bytes_acumulados,
            "duracao_segundos": round(duracao, 1),
            "chunks_por_segundo": round(total_chunks / duracao, 1) if duracao > 0 else 0,
            "timestamp": datetime.now().isoformat(),
            "max_artigos": max_artigos,
            "categorias_filtro": categorias_filtro
        }
        caminho_manifest = os.path.join(self._saida, ARQUIVO_MANIFEST)
        with open(caminho_manifest, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        logger.info(f"Processamento concluido: {total_artigos} artigos, {total_chunks} chunks")
        logger.info(f"Manifest: {caminho_manifest}")
        return saida_jsonl.replace(".jsonl", "_001.jsonl")

    def listar_jsonl_processados(self) -> List[str]:
        arquivos = []
        for f in sorted(os.listdir(self._saida)):
            if f.endswith(".jsonl"):
                arquivos.append(os.path.join(self._saida, f))
        return arquivos

    def carregar_manifest(self) -> Optional[dict]:
        caminho = os.path.join(self._saida, ARQUIVO_MANIFEST)
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def ingerir_jsonl_no_alimentador(self, alimentador: Alimentador,
                                       arquivo_jsonl: Optional[str] = None) -> int:
        from src.core.alimentacao.alimentador import Alimentador
        arquivos = [arquivo_jsonl] if arquivo_jsonl else self.listar_jsonl_processados()
        if not arquivos:
            logger.warning("Nenhum arquivo JSONL encontrado")
            return 0

        if not hasattr(alimentador, "_ensinado_fn") or not alimentador._ensinado_fn:
            logger.warning("Alimentador sem ensinar_fn. Conecte antes com conectar_pith()")
            return 0

        total = 0
        for caminho in arquivos:
            logger.info(f"Ingerindo {caminho} no Alimentador...")
            with open(caminho, "r", encoding="utf-8") as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha:
                        continue
                    try:
                        registro = json.loads(linha)
                    except json.JSONDecodeError:
                        continue
                    try:
                        alimentador._ensinado_fn(
                            pergunta=registro["pergunta"],
                            conteudo=registro["conteudo"],
                            fonte=registro.get("fonte", "wikipedia_dump"),
                            metadata=registro.get("metadata", {})
                        )
                        total += 1
                    except Exception as e:
                        logger.warning(f"Erro ao ingerir chunk: {e}")
            logger.info(f"Finalizado {caminho}: {total} chunks ingeridos ate agora")
        logger.info(f"Ingestao total: {total} chunks")
        return total

    def processar_e_ingerir(self, caminho_dump: str, alimentador: Alimentador,
                              max_artigos: Optional[int] = None) -> int:
        self.processar_artigos_para_jsonl(caminho_dump, max_artigos=max_artigos)
        return self.ingerir_jsonl_no_alimentador(alimentador)

    def buscar_e_processar_topicos_api(self, topicos: List[str],
                                         alimentador: Optional[Alimentador] = None) -> str:
        saida_jsonl = os.path.join(self._saida, f"api_{int(time.time())}.jsonl")
        total = 0
        with open(saida_jsonl, "w", encoding="utf-8") as f:
            for topico in topicos:
                item = self._api_parser.buscar_topico(topico)
                if not item:
                    continue
                pergunta, conteudo, metadados = self._api_parser.gerar_itens_para_pith(item)
                registro = {
                    "pergunta": pergunta,
                    "conteudo": conteudo,
                    "fonte": "wikipedia_api",
                    "metadata": metadados,
                    "timestamp": datetime.now().isoformat()
                }
                f.write(json.dumps(registro, ensure_ascii=False) + "\n")
                total += 1
                if alimentador and hasattr(alimentador, "_ensinado_fn") and alimentador._ensinado_fn:
                    try:
                        alimentador._ensinado_fn(
                            pergunta=pergunta, conteudo=conteudo,
                            fonte="wikipedia_api", metadata=metadados
                        )
                    except Exception as e:
                        logger.warning(f"Erro ao ingerir: {e}")
                time.sleep(0.5)
        logger.info(f"API: {total}/{len(topicos)} topicos salvos em {saida_jsonl}")
        return saida_jsonl
