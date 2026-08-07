import os
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from src.core.alimentacao.manifest import ManifestIngestao
from src.core.alimentacao.validador import ValidadorRegra1
from src.core.alimentacao.parser import ParserArquivo, ItemParseado
from src.core.alimentacao.chunker import Chunker
from src.core.alimentacao.templates import GeradorPergunta

logger = logging.getLogger("ravena.alimentacao.ingestao")

@dataclass
class ResultadoIngestao:
    arquivo: str
    tema: str
    status: str
    itens_gerados: int
    itens_rejeitados: int
    erro: Optional[str] = None

class PipelineIngestao:
    def __init__(self, caminho_manifesto: str):
        self._manifest = ManifestIngestao(caminho_manifesto)
        self._validador = ValidadorRegra1()
        self._parser = ParserArquivo()
        self._chunker = Chunker()
        self._gerador = GeradorPergunta()

    def executar(self, caminho: str, tema: str,
                 ensinar_fn: Optional[Callable] = None,
                 modo_chunk: str = "hierarquico",
                 forcar: bool = False) -> ResultadoIngestao:
        if not os.path.isfile(caminho):
            return ResultadoIngestao(
                arquivo=caminho, tema=tema,
                status="erro", itens_gerados=0, itens_rejeitados=0,
                erro="arquivo_nao_encontrado"
            )

        if not forcar:
            existente = self._manifest.verificar(caminho)
            if existente and existente.get("status") == "ingerido":
                logger.info(f"Arquivo ja ingerido: {caminho} (hash identico)")
                return ResultadoIngestao(
                    arquivo=caminho, tema=tema,
                    status="pulado", itens_gerados=0, itens_rejeitados=0,
                    erro="ja_ingerido"
                )

        try:
            itens_parseados = self._parser.parsear(caminho)
        except Exception as e:
            logger.warning(f"Erro ao parsear {caminho}: {e}")
            self._manifest.registrar(caminho, tema, "erro", motivo_pulo=str(e))
            return ResultadoIngestao(
                arquivo=caminho, tema=tema,
                status="erro", itens_gerados=0, itens_rejeitados=0,
                erro=str(e)
            )

        if not itens_parseados:
            self._manifest.registrar(caminho, tema, "pulado",
                                      motivo_pulo="sem_itens_extraidos")
            return ResultadoIngestao(
                arquivo=caminho, tema=tema,
                status="pulado", itens_gerados=0, itens_rejeitados=0,
                erro="sem_itens_extraidos"
            )

        itens_validados = []
        itens_rejeitados = 0
        for item in itens_parseados:
            valido, motivo = self._validador.validar_item(item.pergunta, item.conteudo)
            if valido:
                itens_validados.append(item)
            else:
                itens_rejeitados += 1
                logger.debug(f"Item rejeitado de {caminho}: {motivo}")

        if not itens_validados:
            self._manifest.registrar(caminho, tema, "pulado",
                                      motivo_pulo="todos_itens_rejeitados")
            return ResultadoIngestao(
                arquivo=caminho, tema=tema,
                status="pulado", itens_gerados=0,
                itens_rejeitados=itens_rejeitados,
                erro="todos_itens_rejeitados"
            )

        itens_para_ensinar = self._aplicar_chunking(itens_validados, modo_chunk)

        if ensinar_fn:
            itens_ensinados = 0
            for item in itens_para_ensinar:
                try:
                    grupo = self._classificar_grupo(item.pergunta, item.conteudo)
                    ensinar_fn(
                        pergunta=item.pergunta,
                        conteudo=item.conteudo,
                        fonte="alimentacao",
                        metadata={**item.metadados, "fonte_original": item.fonte},
                        grupo=grupo
                    )
                    itens_ensinados += 1
                except Exception as e:
                    logger.warning(f"Erro ao ensinar item de {caminho}: {e}")
            itens_gerados = itens_ensinados
        else:
            itens_gerados = len(itens_para_ensinar)

        self._manifest.registrar(caminho, tema, "ingerido",
                                  itens_gerados=itens_gerados)

        return ResultadoIngestao(
            arquivo=caminho, tema=tema,
            status="ingerido",
            itens_gerados=itens_gerados,
            itens_rejeitados=itens_rejeitados
        )

    def _aplicar_chunking(self, itens: List[ItemParseado],
                           modo: str) -> List[ItemParseado]:
        if modo == "nenhum":
            return itens

        resultado = []
        for item in itens:
            chunks = self._chunker.chunk(item.conteudo, modo)
            if not chunks:
                continue
            for titulo_chunk, conteudo_chunk in chunks:
                pergunta = self._gerador.gerar(
                    titulo_chunk,
                    tipo=item.metadados.get("tipo", "md_section"),
                    nome_arquivo=item.metadados.get("arquivo")
                )
                resultado.append(ItemParseado(
                    pergunta=pergunta or item.pergunta,
                    conteudo=conteudo_chunk,
                    grupo=item.grupo,
                    fonte=item.fonte,
                    hash_item=item.hash_item,
                    metadados={**item.metadados, "chunk_de": item.pergunta}
                ))
        return resultado or itens

    def _classificar_grupo(self, pergunta: str, conteudo: str) -> str:
        try:
            from src.core.conhecimento import _GRUPOS_PADRAO
            import re
            palavras_texto = set(re.findall(r'\w+', f"{pergunta} {conteudo}".lower()))
            melhor_grupo = "geral"
            melhor_pontuacao = 0
            for grupo, config in _GRUPOS_PADRAO.items():
                if not config["palavras"]:
                    continue
                pontuacao = sum(1 for p in config["palavras"] if p in palavras_texto)
                if pontuacao > melhor_pontuacao:
                    melhor_pontuacao = pontuacao
                    melhor_grupo = grupo
            return melhor_grupo
        except ImportError:
            return "geral"

    def estatisticas(self) -> Dict[str, Any]:
        return self._manifest.estatisticas()
