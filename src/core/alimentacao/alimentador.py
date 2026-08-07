import os
import logging
from typing import List, Dict, Any, Optional, Callable

from src.core.alimentacao.manifest import ManifestIngestao
from src.core.alimentacao.validador import ValidadorRegra1
from src.core.alimentacao.parser import ParserArquivo, ItemParseado
from src.core.alimentacao.chunker import Chunker
from src.core.alimentacao.templates import GeradorPergunta
from src.core.alimentacao.ingestao import PipelineIngestao, ResultadoIngestao
from src.core.alimentacao.estrategica import Estrategica

logger = logging.getLogger("ravena.alimentacao")

_EXTENSOES_PADRAO = {".md", ".py", ".txt", ".json", ".pdf"}

_TEMAS_PADRAO = {
    "ravena_core": {
        "diretorios": ["src/core"],
        "extensoes": {".py", ".md"},
        "modo_chunk": "hierarquico",
        "descricao": "P1 - Ravena Core (scripts, logica, estrutura)"
    },
    "docs_pessoais": {
        "diretorios": ["."],
        "extensoes": {".md", ".py", ".txt", ".json"},
        "modo_chunk": "hierarquico",
        "descricao": "P2 - Docs Pessoais (Oracle Cloud, bot trade, versionamento)"
    },
    "base_tecnica": {
        "diretorios": ["docs"],
        "extensoes": {".md", ".txt", ".pdf"},
        "modo_chunk": "hierarquico",
        "descricao": "P3 - Base Tecnica (APIs, criptografia, unix)"
    },
    "corpus_medio": {
        "diretorios": [],
        "extensoes": {".md", ".txt", ".pdf"},
        "modo_chunk": "resumo",
        "descricao": "P4 - Corpus Medio (papers, artigos)"
    },
    "corpus_grande": {
        "diretorios": [],
        "extensoes": {".txt"},
        "modo_chunk": "cluster",
        "descricao": "P5 - Corpus Grande (dados brutos, mercado)"
    },
    "nomad_wikipedia": {
        "diretorios": [],
        "extensoes": {".txt", ".md"},
        "modo_chunk": "cluster",
        "descricao": "P6 - Protocolo Nomad / Wikipedia"
    }
}

class Alimentador:
    def __init__(self, projeto_raiz: str,
                 caminho_manifesto: Optional[str] = None):
        self._projeto_raiz = projeto_raiz
        caminho_manifesto = caminho_manifesto or os.path.join(
            projeto_raiz, "data", "manifest_ingestao.json"
        )
        self._pipeline = PipelineIngestao(caminho_manifesto)
        self._estrategica = Estrategica()
        self._ensinado_fn: Optional[Callable] = None

    def conectar_pith(self, pith_instance) -> bool:
        try:
            self._ensinado_fn = pith_instance.ensinar
            logger.info("Alimentador conectado ao Pith")
            return True
        except Exception as e:
            logger.warning(f"Erro ao conectar Pith: {e}")
            return False

    def conectar_ensinado(self, funcao: Callable):
        self._ensinado_fn = funcao

    def ingerir_arquivo(self, caminho: str, tema: str,
                        modo_chunk: str = "hierarquico",
                        forcar: bool = False) -> ResultadoIngestao:
        return self._pipeline.executar(
            caminho=caminho,
            tema=tema,
            ensinar_fn=self._ensinado_fn,
            modo_chunk=modo_chunk,
            forcar=forcar
        )

    def ingerir_diretorio(self, diretorio: str, tema: str,
                           extensoes: Optional[set] = None,
                           modo_chunk: str = "hierarquico",
                           recursivo: bool = True,
                           forcar: bool = False) -> List[ResultadoIngestao]:
        extensoes = extensoes or _EXTENSOES_PADRAO
        if not os.path.isdir(diretorio):
            logger.warning(f"Diretorio nao encontrado: {diretorio}")
            return []

        resultados = []
        if recursivo:
            for raiz, _, arquivos in os.walk(diretorio):
                for arquivo in sorted(arquivos):
                    ext = os.path.splitext(arquivo)[1].lower()
                    if ext in extensoes:
                        caminho = os.path.join(raiz, arquivo)
                        resultado = self.ingerir_arquivo(caminho, tema, modo_chunk, forcar)
                        resultados.append(resultado)
        else:
            for arquivo in sorted(os.listdir(diretorio)):
                caminho = os.path.join(diretorio, arquivo)
                if os.path.isfile(caminho):
                    ext = os.path.splitext(arquivo)[1].lower()
                    if ext in extensoes:
                        resultado = self.ingerir_arquivo(caminho, tema, modo_chunk, forcar)
                        resultados.append(resultado)

        return resultados

    def ingerir_tema(self, tema: str, base_dir: Optional[str] = None,
                      forcar: bool = False) -> List[ResultadoIngestao]:
        config = _TEMAS_PADRAO.get(tema)
        if not config:
            logger.warning(f"Tema desconhecido: {tema}")
            return []

        base = base_dir or self._projeto_raiz
        resultados = []
        for subdir in config["diretorios"]:
            dir_path = os.path.join(base, subdir)
            if os.path.isdir(dir_path):
                logger.info(f"Ingerindo tema '{tema}' de {dir_path}")
                r = self.ingerir_diretorio(
                    dir_path, tema,
                    extensoes=config["extensoes"],
                    modo_chunk=config["modo_chunk"],
                    forcar=forcar
                )
                resultados.extend(r)
            else:
                logger.warning(f"Diretorio nao encontrado para tema '{tema}': {dir_path}")

        return resultados

    def ingerir_todos_temas(self, base_dir: Optional[str] = None) -> Dict[str, List[ResultadoIngestao]]:
        resultados_por_tema = {}
        for tema in _TEMAS_PADRAO:
            if tema in ("corpus_medio", "corpus_grande", "nomad_wikipedia"):
                continue
            resultados = self.ingerir_tema(tema, base_dir)
            resultados_por_tema[tema] = resultados
            logger.info(f"Tema '{tema}': {sum(r.itens_gerados for r in resultados)} itens gerados")
        return resultados_por_tema

    def ingerir_estrategica(self, textos: List[str],
                             prefixo_pergunta: str = "topicos") -> int:
        representantes = self._estrategica.selecionar_representantes(textos)
        itens_gerados = 0
        for pergunta, conteudo in representantes:
            if self._ensinado_fn:
                try:
                    pergunta_final = f"{prefixo_pergunta}: {pergunta.lower()}"
                    self._ensinado_fn(
                        pergunta=pergunta_final,
                        conteudo=conteudo,
                        fonte="alimentacao:estrategica",
                        metadata={"tipo": "cluster", "prefixo": prefixo_pergunta}
                    )
                    itens_gerados += 1
                except Exception as e:
                    logger.warning(f"Erro ao ensinar item estrategico: {e}")
        return itens_gerados

    def verificar_similaridade(self, texto_novo: str,
                                textos_existentes: List[str]) -> float:
        return self._estrategica.verificar_similaridade(texto_novo, textos_existentes)

    def estatisticas(self) -> Dict[str, Any]:
        return self._pipeline.estatisticas()

    def listar_temas_disponiveis(self) -> Dict[str, str]:
        return {k: v["descricao"] for k, v in _TEMAS_PADRAO.items()}

    def resetar_manifesto(self):
        caminho_manifesto = self._pipeline._manifest._caminho
        if os.path.exists(caminho_manifesto):
            os.remove(caminho_manifesto)
            logger.info(f"Manifesto resetado: {caminho_manifesto}")
            self._pipeline._manifest = ManifestIngestao(caminho_manifesto)
