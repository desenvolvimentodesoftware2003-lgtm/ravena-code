"""
MEMORY_CORE — Memoria Episodica e Semantica (v3.2.6)
======================================================
Ravena AIM | Modulo: cognicao e persistencia
Responsabilidades:
  - Memoria episodica: historico de conversas e eventos
  - Memoria semantica: fatos e conhecimento estruturado
  - Persistencia em JSON com auto-prune
  - Integracao com RAG para contexto enriquecido
"""

import os
import json
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

logger = logging.getLogger("ravena.memory")

MEMORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
os.makedirs(MEMORY_DIR, exist_ok=True)

EPISODIC_FILE = os.path.join(MEMORY_DIR, "memoria_episodica.json")
SEMANTIC_FILE = os.path.join(MEMORY_DIR, "memoria_semantica.json")
MAX_EPISODES = 500
MAX_SEMANTIC = 1000
PRUNE_AFTER_DAYS = 30


@dataclass
class Episodio:
    usuario: str
    pergunta: str
    resposta: str
    timestamp: float = field(default_factory=time.time)
    modulo: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FatoSemantico:
    chave: str
    valor: str
    fonte: str = ""
    confianca: float = 1.0
    timestamp: float = field(default_factory=time.time)
    categoria: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EpisodicMemory:
    """Memoria de curto prazo: historico de interacoes."""

    def __init__(self, filepath: str = EPISODIC_FILE):
        self.filepath = filepath
        self._episodios: List[Episodio] = []
        self._carregar()

    def _carregar(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                self._episodios = [Episodio(**e) for e in dados]
            except Exception as e:
                logger.warning(f"Erro ao carregar memoria episodica: {e}")

    def _salvar(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in self._episodios], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar memoria episodica: {e}")

    def adicionar(self, usuario: str, pergunta: str, resposta: str, modulo: str = "") -> Episodio:
        ep = Episodio(usuario=usuario, pergunta=pergunta, resposta=resposta, modulo=modulo)
        self._episodios.append(ep)
        self._prune()
        self._salvar()
        return ep

    def recuperar(self, limite: int = 10, usuario: str = "") -> List[Episodio]:
        epis = self._episodios
        if usuario:
            epis = [e for e in epis if e.usuario == usuario]
        return epis[-limite:]

    def buscar(self, termo: str, limite: int = 5) -> List[Episodio]:
        t = termo.lower()
        resultados = [e for e in self._episodios if t in e.pergunta.lower() or t in e.resposta.lower()]
        return resultados[-limite:]

    def _prune(self):
        if len(self._episodios) <= MAX_EPISODES:
            return
        self._episodios = self._episodios[-MAX_EPISODES:]

    def limpar(self):
        self._episodios = []
        self._salvar()

    @property
    def total(self) -> int:
        return len(self._episodios)


class SemanticMemory:
    """Memoria de longo prazo: fatos e conhecimento estruturado."""

    def __init__(self, filepath: str = SEMANTIC_FILE):
        self.filepath = filepath
        self._fatos: Dict[str, FatoSemantico] = {}
        self._carregar()

    def _carregar(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                for item in dados:
                    fato = FatoSemantico(**item)
                    self._fatos[fato.chave] = fato
            except Exception as e:
                logger.warning(f"Erro ao carregar memoria semantica: {e}")

    def _salvar(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump([f.to_dict() for f in self._fatos.values()], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar memoria semantica: {e}")

    def adicionar(self, chave: str, valor: str, fonte: str = "", confianca: float = 1.0, categoria: str = ""):
        fato = FatoSemantico(chave=chave, valor=valor, fonte=fonte, confianca=confianca, categoria=categoria)
        self._fatos[chave] = fato
        if len(self._fatos) > MAX_SEMANTIC:
            chaves_remover = sorted(self._fatos.keys(), key=lambda k: self._fatos[k].timestamp)[:-MAX_SEMANTIC]
            for k in chaves_remover:
                del self._fatos[k]
        self._salvar()

    def obter(self, chave: str) -> Optional[FatoSemantico]:
        return self._fatos.get(chave)

    def buscar(self, termo: str, limite: int = 10) -> List[FatoSemantico]:
        t = termo.lower()
        resultados = [f for f in self._fatos.values() if t in f.chave.lower() or t in f.valor.lower()]
        resultados.sort(key=lambda x: x.confianca, reverse=True)
        return resultados[:limite]

    def listar_categoria(self, categoria: str) -> List[FatoSemantico]:
        return [f for f in self._fatos.values() if f.categoria == categoria]

    def limpar(self):
        self._fatos = {}
        self._salvar()

    @property
    def total(self) -> int:
        return len(self._fatos)


class MemoryManager:
    """Interface unificada para acesso a memoria."""

    def __init__(self):
        self.episodica = EpisodicMemory()
        self.semantica = SemanticMemory()
        logger.info(f"MemoryManager: {self.episodica.total} episodios, {self.semantica.total} fatos")

    def registrar_interacao(self, usuario: str, pergunta: str, resposta: str, modulo: str = ""):
        self.episodica.adicionar(usuario, pergunta, resposta, modulo)

    def lembrar(self, chave: str) -> Optional[str]:
        fato = self.semantica.obter(chave)
        return fato.valor if fato else None

    def aprender(self, chave: str, valor: str, fonte: str = "", confianca: float = 1.0, categoria: str = ""):
        self.semantica.adicionar(chave, valor, fonte, confianca, categoria)

    def contexto_recente(self, usuario: str = "", limite: int = 5) -> str:
        epis = self.episodica.recuperar(limite=limite, usuario=usuario)
        if not epis:
            return ""
        linhas = []
        for e in epis:
            linhas.append(f"[{e.usuario}] {e.pergunta} -> {e.resposta[:100]}")
        return "\n".join(linhas)

    def diagnostic(self) -> Dict[str, Any]:
        return {
            "episodios": self.episodica.total,
            "fatos": self.semantica.total,
            "episodic_file": EPISODIC_FILE,
            "semantic_file": SEMANTIC_FILE,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mem = MemoryManager()
    mem.registrar_interacao("Alex", "Ola Ravena", "Ola! Como posso ajudar?")
    mem.aprender("versao_sistema", "3.2.6", fonte="CHANGELOG", categoria="sistema")
    mem.aprender("brutality_threshold", "0.52", fonte="config_v3.json", categoria="trading")
    print("Contexto:", mem.contexto_recente("Alex"))
    print("Lembranca:", mem.lembrar("versao_sistema"))
    print("Diagnostico:", mem.diagnostic())
