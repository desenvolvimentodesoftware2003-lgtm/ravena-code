import os
import sys
import time
import json
import logging
import importlib.util
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

_projeto_raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _projeto_raiz not in sys.path:
    sys.path.insert(0, _projeto_raiz)

_CONFIG_PADRAO = {
    "omega_version": "4.0.0-RAVENA-CORE",
    "core": {"verbose": True, "fallback_inteligente": True, "max_ciclos_pensamento": 3, "confianca_minima": 0.3, "modo_soberano": True},
    "log": {"nivel": "INFO", "formato": "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s", "caminho_jsonl": "data/cognitive_treino.jsonl"},
    "conhecimento": {"ativo": True, "max_resultados": 5, "similaridade_minima": 0.6, "autoridade_minima": 0.3},
    "seguranca": {"separado": True, "lockdown_block": 0.60},
    "sensores_cognitivos": {"ativo": True, "capturar_raciocinio": True, "capturar_fonte": True},
    "visao": {"ativo": False, "mouse_click": True}
}

def _importar_de_arquivo(nome_modulo: str, caminho_arquivo: str):
    spec = importlib.util.spec_from_file_location(nome_modulo, caminho_arquivo)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nome_modulo] = modulo
    spec.loader.exec_module(modulo)
    return modulo

@dataclass
class DiagnosticoMissao:
    origem: str = "usuario"
    confianca: float = 0.0
    fonte: str = ""
    estado_crenca: str = "ativo"
    authority_score: float = 0.0
    score_ameaca: float = 0.0
    modulos_usados: List[str] = field(default_factory=list)
    ciclos_pensamento: int = 0
    tempo_total_ms: float = 0.0

@dataclass
class ResultadoMissao:
    sucesso: bool = False
    resposta: str = ""
    raciocinio: str = ""
    diagnostico: DiagnosticoMissao = field(default_factory=DiagnosticoMissao)
    erro: Optional[str] = None
    sugestao: Optional[str] = None

class Omega:
    _instancia = None

    def __new__(cls, *args, **kwargs):
        if cls._instancia is None:
            cls._instancia = super(Omega, cls).__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    def __init__(self, config_path: Optional[str] = None):
        if self._inicializado:
            return

        self.config = self._carregar_config(config_path)
        self.logger_console = self._configurar_logger_console()
        self._garantir_diretorio_data()

        self._dados_perfis = {}  # raw do perfis_config.json
        self._perfil_nome = "intermediaria"
        self._carregar_perfil()

        self.conhecimento = None
        self.cognitive_sensors = None
        self.tools = None
        self.lockdown = None
        self.ml_pipeline = None
        self.inteligencia_propria = None
        self.contextualidade = None
        self.fallback_inteligente = None
        self.ravena_model = None
        self.intencao = None
        self.visao = None

        self._carregar_modulos_disponiveis()
        self._inicializado = True
        self.logger_console.info("Omega v4.0.0 inicializado — nucleo unificado pronto")

    def _carregar_config(self, config_path: Optional[str] = None) -> dict:
        caminhos = [
            config_path,
            os.path.join(_projeto_raiz, "config", "omega_config.json"),
            os.path.join(_projeto_raiz, "config_v3.json")
        ]
        for caminho in caminhos:
            if caminho and os.path.exists(caminho):
                try:
                    with open(caminho, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    config["_origem"] = caminho
                    return config
                except Exception as e:
                    print(f"[Omega] Erro ao carregar config de {caminho}: {e}")
        return dict(_CONFIG_PADRAO)

    def _configurar_logger_console(self) -> logging.Logger:
        logger = logging.getLogger("ravena.omega")
        logger.propagate = False
        nivel = getattr(logging, self.config.get("log", {}).get("nivel", "INFO"), logging.INFO)
        logger.setLevel(nivel)
        if not logger.handlers:
            formato = self.config.get("log", {}).get("formato", "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(formato))
            logger.addHandler(handler)
        return logger

    def _garantir_diretorio_data(self):
        caminho_jsonl = self.config.get("log", {}).get("caminho_jsonl", "data/cognitive_treino.jsonl")
        dir_data = os.path.join(_projeto_raiz, os.path.dirname(caminho_jsonl))
        os.makedirs(dir_data, exist_ok=True)

    def _carregar_perfil(self):
        caminho_perfis = os.path.join(_projeto_raiz, "data", "perfis_config.json")
        if os.path.exists(caminho_perfis):
            try:
                with open(caminho_perfis, "r", encoding="utf-8") as f:
                    self._dados_perfis = json.load(f)
                self._perfil_nome = self._dados_perfis.get("perfil_ativo", "intermediaria")
                perfil = self._dados_perfis.get("perfis", {}).get(self._perfil_nome, {})
                if perfil:
                    for secao, valores in perfil.items():
                        if secao in ("label", "descricao"):
                            continue
                        if secao in self.config:
                            self.config[secao].update(valores)
                        else:
                            self.config[secao] = dict(valores)
                    self.logger_console.info(f"Perfil aplicado: {self._perfil_nome} ({perfil.get('label', self._perfil_nome)})")
            except Exception as e:
                self.logger_console.warning(f"Erro ao carregar perfil: {e}")
        else:
            self.logger_console.info("perfis_config.json nao encontrado — usando config padrao")

    def _salvar_perfil_ativo(self):
        caminho_perfis = os.path.join(_projeto_raiz, "data", "perfis_config.json")
        if self._dados_perfis:
            self._dados_perfis["perfil_ativo"] = self._perfil_nome
            try:
                with open(caminho_perfis, "w", encoding="utf-8") as f:
                    json.dump(self._dados_perfis, f, indent=2, ensure_ascii=False)
            except Exception as e:
                self.logger_console.warning(f"Erro ao salvar perfil ativo: {e}")

    def aplicar_perfil(self, nome: str) -> bool:
        if not self._dados_perfis:
            self._carregar_perfil()
        perfis = self._dados_perfis.get("perfis", {})
        if nome not in perfis:
            self.logger_console.warning(f"Perfil '{nome}' nao encontrado. Disponiveis: {list(perfis.keys())}")
            return False
        self._perfil_nome = nome
        perfil = perfis[nome]
        for secao, valores in perfil.items():
            if secao in ("label", "descricao"):
                continue
            if secao in self.config:
                self.config[secao].update(valores)
            else:
                self.config[secao] = dict(valores)

        self._salvar_perfil_ativo()
        self.logger_console.info(f"Perfil alterado para: {nome} ({perfil.get('label', nome)})")
        return True

    def listar_perfis(self) -> dict:
        if not self._dados_perfis:
            self._carregar_perfil()
        return {
            "perfil_atual": self._perfil_nome,
            "perfis_disponiveis": {
                k: {"label": v.get("label", k), "descricao": v.get("descricao", "")}
                for k, v in self._dados_perfis.get("perfis", {}).items()
            }
        }

    def _carregar_modulos_disponiveis(self):
        importacao_realizada = False

        try:
            from src.core.conhecimento import ConhecimentoPith
            self.conhecimento = ConhecimentoPith()
            importacao_realizada = True
        except ImportError:
            self.logger_console.info("conhecimento.py ainda nao existe — hook vazio")

        try:
            from src.core.lockdown import Lockdown
            self.lockdown = Lockdown()
            importacao_realizada = True
        except ImportError:
            self.logger_console.info("lockdown.py ainda nao existe — hook vazio")

        try:
            from src.core.cognitive_sensors import CognitiveSensor
            self.cognitive_sensors = CognitiveSensor()
            importacao_realizada = True
        except ImportError:
            self.logger_console.info("cognitive_sensors.py ainda nao existe — hook vazio")

        try:
            from src.core.ravena_tools import RavenaTools
            self.tools = RavenaTools()
            importacao_realizada = True
        except ImportError:
            self.logger_console.info("ravena_tools.py ainda nao existe — hook vazio")

        try:
            from src.core.ml_pipeline import MLPipeline
            self.ml_pipeline = MLPipeline()
        except ImportError:
            pass

        caminho_jsonl = os.path.join(_projeto_raiz, self.config.get("log", {}).get("caminho_jsonl", "data/cognitive_treino.jsonl"))

        try:
            from src.core.inteligencia_propria import InteligenciaPropria
            ip = InteligenciaPropria()
            if os.path.exists(caminho_jsonl):
                total = ip.carregar_dados(caminho_jsonl)
                if total >= 2:
                    ip.treinar(epochs=10)
            self.inteligencia_propria = ip
            importacao_realizada = True
        except ImportError:
            pass

        try:
            from src.core.contextualidade import Contextualidade
            self.contextualidade = Contextualidade()
            importacao_realizada = True
        except ImportError:
            pass

        try:
            from src.core.intencao import ClassificadorIntencao
            self.intencao = ClassificadorIntencao()
            importacao_realizada = True
        except ImportError:
            self.intencao = None

        try:
            from src.core.fallback_inteligente import FallbackInteligente
            caminho_templates = os.path.join(_projeto_raiz, "data", "fallback_templates.json")
            self.fallback_inteligente = FallbackInteligente(caminho_templates)
            importacao_realizada = True
        except ImportError:
            pass

        try:
            from src.core.ravena_model import RavenaModel
            self.ravena_model = RavenaModel(modelo="gguf")
            importacao_realizada = True
        except ImportError:
            self.ravena_model = None

        if not importacao_realizada:
            self.logger_console.info("Omega em modo essencial — nenhum modulo adicional encontrado")

    def _escrever_log_jsonl(self, pergunta: str, raciocinio: str, resposta: str,
                            confianca: float, fonte: str, estado_crenca: str,
                            authority_score: float, origem: str = "usuario",
                            score_ameaca: float = 0.0):
        caminho_rel = self.config.get("log", {}).get("caminho_jsonl", "data/cognitive_treino.jsonl")
        caminho_abs = os.path.join(_projeto_raiz, caminho_rel)
        entrada = {
            "timestamp": datetime.now().isoformat(),
            "pergunta": pergunta,
            "raciocinio": raciocinio,
            "resposta": resposta,
            "confianca": round(confianca, 4),
            "fonte": fonte,
            "estado_crenca": estado_crenca,
            "authority_score": round(authority_score, 4),
            "origem": origem,
            "score_ameaca": round(score_ameaca, 4)
        }
        try:
            with open(caminho_abs, "a", encoding="utf-8") as f:
                f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger_console.warning(f"Erro ao escrever JSONL: {e}")

    def pensar(self, pergunta: str, conhecimento: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, float, str, str, float]:
        inicio = time.time()

        if conhecimento:
            trechos = [c for c in conhecimento if c.get("authority_score", 0) >= self.config.get("conhecimento", {}).get("autoridade_minima", 0.3)]
            if trechos:
                melhor = max(trechos, key=lambda x: x.get("authority_score", 0))
                raciocinio = f"Contexto recuperado de {melhor.get('fonte', 'desconhecida')}: {melhor.get('conteudo', '')[:200]}"
                confianca = melhor.get("authority_score", 0.5)
                fonte = melhor.get("fonte", "conhecimento")
                estado = melhor.get("estado_crenca", "ativo")
                authority = melhor.get("authority_score", 0.5)
                self.logger_console.info(f"Pensar: raciocinio baseado em {fonte} (confianca: {confianca:.2f})")
                return raciocinio, confianca, fonte, estado, authority

        raciocinio = f"Raciocinio baseado em conhecimento interno: {pergunta[:100]}..."
        confianca = 0.5
        fonte = "conhecimento_interno"
        estado = "ativo"
        authority = 0.5
        self.logger_console.info(f"Pensar: sem contexto externo, usando conhecimento interno (confianca: {confianca:.2f})")
        return raciocinio, confianca, fonte, estado, authority

    def _sugerir_correcao(self, entrada: str) -> Optional[str]:
        if not self.config.get("core", {}).get("fallback_inteligente", True):
            return None
        if not entrada or not isinstance(entrada, str):
            return None
        palavras_esperadas = {
            "qual": ["qual", "qual", "qual"],
            "capital": ["capital", "capital"],
            "brasil": ["brasil", "brasil"]
        }
        return None

    _CORRECOES_CONHECIDAS = [
        (r"qu[em]\s+descobriu\s+o\s+brasil",
         "Nota: Quem descobriu o Brasil foi Pedro Alvares Cabral em 1500, nao Cristovao Colombo."),
        (r"brasil\s+fica\s+na\s+america",
         "Nota: O Brasil fica na America do Sul."),
    ]

    @staticmethod
    def _injetar_correcoes(pergunta: str) -> str:
        import re
        pergunta_lower = pergunta.lower()
        correcoes = []
        for padrao, correcao in Omega._CORRECOES_CONHECIDAS:
            if re.search(padrao, pergunta_lower):
                correcoes.append(correcao)
        if correcoes:
            return "\n".join(correcoes) + "\n" + pergunta
        return pergunta

    def executar(self, pergunta: str, contexto: Optional[Dict[str, Any]] = None) -> ResultadoMissao:
        inicio = time.time()
        contexto = contexto or {}
        origem = contexto.get("origem", "usuario")
        resultado = ResultadoMissao()
        resultado.diagnostico.origem = origem
        resultado.diagnostico.modulos_usados = []

        if not pergunta or not pergunta.strip():
            resultado.erro = "PERGUNTA_VAZIA"
            resultado.sugestao = "Por favor, digite uma pergunta valida."
            resultado.diagnostico.tempo_total_ms = round((time.time() - inicio) * 1000, 2)
            return resultado

        # ── Classificador de intencao (antes do Lockdown) ──
        intent = None
        if self.intencao:
            intent = self.intencao.classificar(pergunta)
            resultado.diagnostico.modulos_usados.append(f"intencao_{intent['tipo']}")
            if intent["tipo"] in ("saudacao", "vazio"):
                resultado.resposta = intent["resposta"]
                resultado.sucesso = intent["payload"].get("sucesso", True) if intent["payload"] else True
                if intent["tipo"] == "vazio":
                    resultado.erro = intent["payload"].get("erro", "") if intent["payload"] else ""
                    resultado.sugestao = intent["payload"].get("sugestao", "") if intent["payload"] else ""
                resultado.diagnostico.tempo_total_ms = round((time.time() - inicio) * 1000, 2)
                self._ultima_intencao = intent
                return resultado
            if intent["tipo"] == "ambigua":
                self.logger_console.info(f"Intencao ambigua para: '{pergunta[:40]}...'")
                # Continua para Lockdown e conhecimento (fallback pode tratar)
        self._ultima_intencao = intent

        if self.lockdown:
            avaliacao = self.lockdown.avaliar(pergunta)
            score_ameaca = avaliacao.get("score", 0.0)
            bloqueado = avaliacao.get("bloqueado", False)
            resultado.diagnostico.score_ameaca = score_ameaca
            resultado.diagnostico.modulos_usados.append("lockdown")
            if bloqueado:
                resultado.erro = "LOCKDOWN_ATIVO"
                resultado.sugestao = avaliacao.get("mensagem", "Comando bloqueado pelo protocolo de seguranca.")
                resultado.diagnostico.tempo_total_ms = round((time.time() - inicio) * 1000, 2)
                if self.cognitive_sensors:
                    self.cognitive_sensors.capturar(pergunta, "", "", 0.0, "", "contestado", 0.0, origem, score_ameaca)
                else:
                    self._escrever_log_jsonl(pergunta, "", "", 0.0, "", "contestado", 0.0, origem, score_ameaca)
                return resultado

        # ── Ambigua → Fallback pede clareza ──
        if self.fallback_inteligente and intent and intent["tipo"] == "ambigua":
            self.logger_console.info(f"Intencao ambigua para: '{pergunta[:40]}...'")
            decisao = self.fallback_inteligente.decidir(repetido=self.fallback_inteligente.ciclo_ambiguidade > 1)
            resultado.resposta = decisao["resposta"]
            resultado.sucesso = False
            resultado.erro = decisao["erro"]
            resultado.sugestao = decisao["sugestao"]
            resultado.diagnostico.modulos_usados.append("fallback_ambiguo")
            resultado.diagnostico.tempo_total_ms = round((time.time() - inicio) * 1000, 2)
            return resultado

        # ── Correcao de alucinacoes conhecidas ──
        pergunta_corrigida = self._injetar_correcoes(pergunta)
        if pergunta_corrigida != pergunta:
            self.logger_console.info("Correcao de alucinacao injetada no prompt")

        # ── Pergunta legitima → RavenaModel (LLM real) ──
        self.logger_console.info(f"Usando RavenaModel para: '{pergunta[:50]}...'")
        if self.ravena_model:
            try:
                resposta = self.ravena_model.gerar_resposta(pergunta_corrigida, max_tokens=120, temperatura=0.1)
                resultado.resposta = resposta
                resultado.sucesso = True
                resultado.diagnostico.modulos_usados.append("ravena_llm")
                resultado.raciocinio = f"Resposta gerada pelo modelo de linguagem local"
                resultado.diagnostico.confianca = 0.7
                resultado.diagnostico.fonte = "llm_local"
                resultado.diagnostico.estado_crenca = "ativo"
                resultado.diagnostico.authority_score = 0.7
            except Exception as e:
                self.logger_console.warning(f"Falha no RavenaModel: {e}")
                resultado.resposta = "Erro ao processar sua pergunta com o modelo de linguagem."
                resultado.sucesso = False
                resultado.erro = "LLM_ERROR"
                resultado.sugestao = "O modelo de linguagem esta temporariamente indisponivel."
        else:
            resultado.resposta = "Modulo de inteligencia nao disponivel."
            resultado.sucesso = False
            resultado.erro = "LLM_NAO_CARREGADO"
            resultado.sugestao = "O modelo de linguagem nao foi carregado."

        resultado.diagnostico.tempo_total_ms = round((time.time() - inicio) * 1000, 2)
        diagnostico_extra = {
            "modulos_usados": resultado.diagnostico.modulos_usados,
            "tempo_total_ms": resultado.diagnostico.tempo_total_ms,
        }

        if self.cognitive_sensors and self.config.get("sensores_cognitivos", {}).get("ativo", True):
            try:
                self.cognitive_sensors.capturar(
                    pergunta=pergunta,
                    raciocinio=resultado.raciocinio,
                    resposta=resultado.resposta,
                    confianca=resultado.diagnostico.confianca,
                    fonte=resultado.diagnostico.fonte,
                    estado_crenca=resultado.diagnostico.estado_crenca,
                    authority_score=resultado.diagnostico.authority_score,
                    origem=origem,
                    score_ameaca=resultado.diagnostico.score_ameaca,
                    diagnostico_extra=diagnostico_extra
                )
                resultado.diagnostico.modulos_usados.append("cognitive_sensors")
            except Exception as e:
                self.logger_console.warning(f"Falha no cognitive_sensors: {e}")
        else:
            self._escrever_log_jsonl(
                pergunta=pergunta,
                raciocinio=resultado.raciocinio,
                resposta=resultado.resposta,
                confianca=resultado.diagnostico.confianca,
                fonte=resultado.diagnostico.fonte,
                estado_crenca=resultado.diagnostico.estado_crenca,
                authority_score=resultado.diagnostico.authority_score,
                origem=origem,
                score_ameaca=resultado.diagnostico.score_ameaca
            )
        return resultado

    def obter_diagnostico(self) -> Dict[str, Any]:
        cx_status = None
        if self.contextualidade:
            cx_status = self.contextualidade.obter_diagnostico()
        fb_status = None
        if self.fallback_inteligente:
            fb_status = self.fallback_inteligente.obter_diagnostico()
        return {
            "versao": self.config.get("omega_version", "4.0.0-RAVENA-CORE"),
            "modulos_disponiveis": [
                nome for nome in ["conhecimento", "cognitive_sensors", "tools", "lockdown", "ml_pipeline", "inteligencia_propria", "contextualidade", "fallback_inteligente", "ravena_model", "intencao", "visao"]
                if getattr(self, nome) is not None
            ],
            "config_origem": self.config.get("_origem", "padrao_interno"),
            "modo_soberano": self.config.get("core", {}).get("modo_soberano", True),
            "perfil_ativo": self._perfil_nome,
            "contextualidade": cx_status,
            "fallback_inteligente": fb_status,
            "timestamp": datetime.now().isoformat()
        }

def obter_omega(config_path: Optional[str] = None) -> Omega:
    return Omega(config_path)

if __name__ == "__main__":
    core = obter_omega()
    print(json.dumps(core.obter_diagnostico(), indent=2, ensure_ascii=False))
    print()
    resultado = core.executar("qual e a capital do Brasil?")
    print(json.dumps({
        "sucesso": resultado.sucesso,
        "resposta": resultado.resposta,
        "raciocinio": resultado.raciocinio[:80] + "...",
        "diagnostico": {
            "confianca": resultado.diagnostico.confianca,
            "fonte": resultado.diagnostico.fonte,
            "estado_crenca": resultado.diagnostico.estado_crenca,
            "modulos": resultado.diagnostico.modulos_usados,
            "tempo_ms": resultado.diagnostico.tempo_total_ms
        }
    }, indent=2, ensure_ascii=False))
