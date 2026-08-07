"""
MÓDULO DE CONECTOR SOCIAL — Ravena AI (Prioridade 4)
=====================================================
Integração com a API do Instagram (Graph API) para publicação,
monitoramento e análise de conteúdo social.

Responsabilidades:
  - Autenticação via token de acesso (Instagram Graph API)
  - Publicação de posts (imagem + legenda)
  - Agendamento de publicações
  - Coleta de métricas de engajamento (curtidas, comentários, alcance)
  - Monitoramento de menções e hashtags
  - Relatório de desempenho de conteúdo

Padrões de Segurança (Soberania Digital):
  - Tokens nunca são logados em texto claro
  - Todas as chamadas externas são auditadas
  - Modo Soberano: em OFFLINE_TOTAL, o conector é desabilitado
  - Rate limiting respeitado conforme limites da Graph API

Referências:
  - https://developers.facebook.com/docs/instagram-api
  - https://developers.facebook.com/docs/instagram-api/guides/content-publishing
"""

import os
import json
import time
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import urllib.request
import urllib.parse
import urllib.error

# ── Logging ──────────────────────────────────────────────────
logger = logging.getLogger("ravena.social_connector")

# ── Constantes ───────────────────────────────────────────────
INSTAGRAM_GRAPH_API_BASE = "https://graph.instagram.com/v19.0"
FACEBOOK_GRAPH_API_BASE  = "https://graph.facebook.com/v19.0"

# Limites de rate da Graph API (por hora)
RATE_LIMIT_PUBLICACOES_HORA = 25
RATE_LIMIT_CONSULTAS_HORA   = 200

# Tamanho máximo da legenda (caracteres)
MAX_LEGENDA_CHARS = 2200


# ============================================================
# ENUMS
# ============================================================

class StatusConexao(Enum):
    """Estado da conexão com a API do Instagram"""
    DESCONECTADO   = "desconectado"
    CONECTADO      = "conectado"
    ERRO_TOKEN     = "erro_token"
    RATE_LIMITED   = "rate_limited"
    OFFLINE_TOTAL  = "offline_total"


class TipoMidia(Enum):
    """Tipos de mídia suportados pela Instagram Graph API"""
    IMAGEM         = "IMAGE"
    VIDEO          = "VIDEO"
    CARROSSEL      = "CAROUSEL_ALBUM"
    REELS          = "REELS"
    STORIES        = "STORIES"


class StatusPublicacao(Enum):
    """Estado de uma publicação"""
    RASCUNHO       = "rascunho"
    AGENDADA       = "agendada"
    PUBLICANDO     = "publicando"
    PUBLICADA      = "publicada"
    FALHA          = "falha"
    CANCELADA      = "cancelada"


class NivelAlerta(Enum):
    """Nível de alerta para monitoramento"""
    INFO    = "info"
    AVISO   = "aviso"
    CRITICO = "critico"


# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class CredenciaisInstagram:
    """
    Credenciais de acesso à Instagram Graph API.
    Nunca persistir em texto claro — use variáveis de ambiente.
    """
    access_token: str
    instagram_account_id: str
    app_id: str = ""
    app_secret: str = ""

    def token_hash(self) -> str:
        """Retorna hash do token para logging seguro (nunca o token em si)."""
        return hashlib.sha256(self.access_token.encode()).hexdigest()[:16]

    @classmethod
    def from_env(cls) -> "CredenciaisInstagram":
        """Carrega credenciais a partir de variáveis de ambiente."""
        token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
        account_id = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")
        app_id = os.environ.get("INSTAGRAM_APP_ID", "")
        app_secret = os.environ.get("INSTAGRAM_APP_SECRET", "")
        if not token or not account_id:
            raise ValueError(
                "Variáveis de ambiente INSTAGRAM_ACCESS_TOKEN e "
                "INSTAGRAM_ACCOUNT_ID são obrigatórias."
            )
        return cls(
            access_token=token,
            instagram_account_id=account_id,
            app_id=app_id,
            app_secret=app_secret,
        )


@dataclass
class PublicacaoInstagram:
    """Representa uma publicação a ser enviada ao Instagram"""
    legenda: str
    url_midia: str
    tipo_midia: TipoMidia = TipoMidia.IMAGEM
    hashtags: List[str] = field(default_factory=list)
    agendamento: Optional[datetime] = None
    id_publicacao: Optional[str] = None
    status: StatusPublicacao = StatusPublicacao.RASCUNHO
    criado_em: datetime = field(default_factory=datetime.utcnow)
    publicado_em: Optional[datetime] = None
    erro: Optional[str] = None

    def legenda_completa(self) -> str:
        """Retorna a legenda com hashtags concatenadas."""
        tags = " ".join(f"#{h.lstrip('#')}" for h in self.hashtags)
        texto = f"{self.legenda}\n\n{tags}".strip()
        if len(texto) > MAX_LEGENDA_CHARS:
            logger.warning(
                f"Legenda excede {MAX_LEGENDA_CHARS} caracteres "
                f"({len(texto)}). Será truncada."
            )
            texto = texto[:MAX_LEGENDA_CHARS]
        return texto

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_publicacao": self.id_publicacao,
            "legenda": self.legenda[:80] + "..." if len(self.legenda) > 80 else self.legenda,
            "tipo_midia": self.tipo_midia.value,
            "status": self.status.value,
            "criado_em": self.criado_em.isoformat(),
            "publicado_em": self.publicado_em.isoformat() if self.publicado_em else None,
            "erro": self.erro,
        }


@dataclass
class MetricasPublicacao:
    """Métricas de engajamento de uma publicação"""
    id_publicacao: str
    curtidas: int = 0
    comentarios: int = 0
    compartilhamentos: int = 0
    salvamentos: int = 0
    alcance: int = 0
    impressoes: int = 0
    engajamento_total: int = 0
    taxa_engajamento: float = 0.0
    coletado_em: datetime = field(default_factory=datetime.utcnow)

    def calcular_taxa(self, seguidores: int) -> float:
        """Calcula taxa de engajamento em relação ao número de seguidores."""
        if seguidores <= 0:
            return 0.0
        self.engajamento_total = (
            self.curtidas + self.comentarios +
            self.compartilhamentos + self.salvamentos
        )
        self.taxa_engajamento = round(
            (self.engajamento_total / seguidores) * 100, 2
        )
        return self.taxa_engajamento

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_publicacao": self.id_publicacao,
            "curtidas": self.curtidas,
            "comentarios": self.comentarios,
            "compartilhamentos": self.compartilhamentos,
            "salvamentos": self.salvamentos,
            "alcance": self.alcance,
            "impressoes": self.impressoes,
            "engajamento_total": self.engajamento_total,
            "taxa_engajamento": self.taxa_engajamento,
            "coletado_em": self.coletado_em.isoformat(),
        }


@dataclass
class AlertaMonitoramento:
    """Alerta gerado pelo sistema de monitoramento"""
    nivel: NivelAlerta
    mensagem: str
    dado_relacionado: Optional[Dict[str, Any]] = None
    gerado_em: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nivel": self.nivel.value,
            "mensagem": self.mensagem,
            "dado_relacionado": self.dado_relacionado,
            "gerado_em": self.gerado_em.isoformat(),
        }


@dataclass
class ResultadoOperacao:
    """Resultado padronizado de qualquer operação do conector"""
    sucesso: bool
    mensagem: str
    dados: Optional[Dict[str, Any]] = None
    erro_codigo: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sucesso": self.sucesso,
            "mensagem": self.mensagem,
            "dados": self.dados,
            "erro_codigo": self.erro_codigo,
        }


# ============================================================
# CLIENTE HTTP LEVE (sem dependências externas)
# ============================================================

class ClienteGraphAPI:
    """
    Cliente HTTP minimalista para a Instagram/Facebook Graph API.
    Usa apenas a biblioteca padrão do Python (urllib) para manter
    a soberania digital sem dependências externas obrigatórias.
    """

    def __init__(self, credenciais: CredenciaisInstagram, timeout: int = 30):
        self.credenciais = credenciais
        self.timeout = timeout
        self._historico_chamadas: List[float] = []

    # ── Rate limiting interno ─────────────────────────────────

    def _registrar_chamada(self) -> None:
        agora = time.time()
        self._historico_chamadas.append(agora)
        # Mantém apenas chamadas da última hora
        self._historico_chamadas = [
            t for t in self._historico_chamadas if agora - t < 3600
        ]

    def _verificar_rate_limit(self, limite: int) -> bool:
        agora = time.time()
        chamadas_hora = [t for t in self._historico_chamadas if agora - t < 3600]
        return len(chamadas_hora) < limite

    # ── Requisições HTTP ──────────────────────────────────────

    def _requisicao(
        self,
        metodo: str,
        url: str,
        params: Optional[Dict] = None,
        dados: Optional[Dict] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Executa uma requisição HTTP e retorna (sucesso, resposta_json)."""
        try:
            if params:
                url = f"{url}?{urllib.parse.urlencode(params)}"

            corpo = None
            headers = {"Content-Type": "application/json"}
            if dados:
                corpo = json.dumps(dados).encode("utf-8")

            req = urllib.request.Request(
                url, data=corpo, headers=headers, method=metodo
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                conteudo = resp.read().decode("utf-8")
                self._registrar_chamada()
                return True, json.loads(conteudo)

        except urllib.error.HTTPError as e:
            corpo_erro = e.read().decode("utf-8") if e.fp else "{}"
            try:
                erro_json = json.loads(corpo_erro)
            except Exception:
                erro_json = {"mensagem_raw": corpo_erro}
            logger.error(
                f"[GraphAPI] HTTPError {e.code}: {erro_json}"
            )
            return False, {"error": erro_json, "http_status": e.code}

        except urllib.error.URLError as e:
            logger.error(f"[GraphAPI] URLError: {e.reason}")
            return False, {"error": {"message": str(e.reason)}}

        except Exception as e:
            logger.error(f"[GraphAPI] Erro inesperado: {e}")
            return False, {"error": {"message": str(e)}}

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Tuple[bool, Dict]:
        url = f"{INSTAGRAM_GRAPH_API_BASE}/{endpoint}"
        params = params or {}
        params["access_token"] = self.credenciais.access_token
        return self._requisicao("GET", url, params=params)

    def post(self, endpoint: str, dados: Optional[Dict] = None) -> Tuple[bool, Dict]:
        url = f"{INSTAGRAM_GRAPH_API_BASE}/{endpoint}"
        dados = dados or {}
        dados["access_token"] = self.credenciais.access_token
        return self._requisicao("POST", url, dados=dados)

    def post_facebook(self, endpoint: str, dados: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """Usa a base da Facebook Graph API (necessário para algumas operações)."""
        url = f"{FACEBOOK_GRAPH_API_BASE}/{endpoint}"
        dados = dados or {}
        dados["access_token"] = self.credenciais.access_token
        return self._requisicao("POST", url, dados=dados)


# ============================================================
# PUBLICADOR DE CONTEÚDO
# ============================================================

class PublicadorInstagram:
    """
    Responsável por criar e publicar conteúdo no Instagram via Graph API.
    Fluxo de publicação em duas etapas:
      1. Criar container de mídia (obtém media_id)
      2. Publicar o container (torna o post visível)
    """

    def __init__(self, cliente: ClienteGraphAPI):
        self.cliente = cliente
        self._fila_publicacoes: List[PublicacaoInstagram] = []

    # ── Etapa 1: Criar container ──────────────────────────────

    def _criar_container_imagem(self, publicacao: PublicacaoInstagram) -> Optional[str]:
        """Cria um container de mídia para imagem e retorna o creation_id."""
        account_id = self.cliente.credenciais.instagram_account_id
        dados = {
            "image_url": publicacao.url_midia,
            "caption": publicacao.legenda_completa(),
        }
        sucesso, resposta = self.cliente.post(
            f"{account_id}/media", dados=dados
        )
        if sucesso and "id" in resposta:
            logger.info(f"[Publicador] Container criado: {resposta['id']}")
            return resposta["id"]
        logger.error(f"[Publicador] Falha ao criar container: {resposta}")
        return None

    def _criar_container_reels(self, publicacao: PublicacaoInstagram) -> Optional[str]:
        """Cria um container de Reels e retorna o creation_id."""
        account_id = self.cliente.credenciais.instagram_account_id
        dados = {
            "media_type": "REELS",
            "video_url": publicacao.url_midia,
            "caption": publicacao.legenda_completa(),
        }
        sucesso, resposta = self.cliente.post(
            f"{account_id}/media", dados=dados
        )
        if sucesso and "id" in resposta:
            logger.info(f"[Publicador] Container Reels criado: {resposta['id']}")
            return resposta["id"]
        logger.error(f"[Publicador] Falha ao criar container Reels: {resposta}")
        return None

    # ── Etapa 2: Publicar container ───────────────────────────

    def _publicar_container(self, creation_id: str) -> Optional[str]:
        """Publica o container e retorna o media_id final."""
        account_id = self.cliente.credenciais.instagram_account_id
        dados = {"creation_id": creation_id}
        sucesso, resposta = self.cliente.post(
            f"{account_id}/media_publish", dados=dados
        )
        if sucesso and "id" in resposta:
            logger.info(f"[Publicador] Post publicado: {resposta['id']}")
            return resposta["id"]
        logger.error(f"[Publicador] Falha ao publicar container: {resposta}")
        return None

    # ── Fluxo principal ───────────────────────────────────────

    def publicar(self, publicacao: PublicacaoInstagram) -> ResultadoOperacao:
        """
        Executa o fluxo completo de publicação no Instagram.
        Retorna ResultadoOperacao com sucesso/falha e detalhes.
        """
        if not self.cliente._verificar_rate_limit(RATE_LIMIT_PUBLICACOES_HORA):
            publicacao.status = StatusPublicacao.FALHA
            publicacao.erro = "Rate limit de publicações atingido (25/hora)."
            return ResultadoOperacao(
                sucesso=False,
                mensagem=publicacao.erro,
                erro_codigo="RATE_LIMIT",
            )

        publicacao.status = StatusPublicacao.PUBLICANDO
        logger.info(
            f"[Publicador] Iniciando publicação — tipo: {publicacao.tipo_midia.value}"
        )

        # Seleciona o criador de container conforme o tipo de mídia
        creation_id = None
        if publicacao.tipo_midia == TipoMidia.IMAGEM:
            creation_id = self._criar_container_imagem(publicacao)
        elif publicacao.tipo_midia == TipoMidia.REELS:
            creation_id = self._criar_container_reels(publicacao)
        else:
            publicacao.status = StatusPublicacao.FALHA
            publicacao.erro = f"Tipo de mídia '{publicacao.tipo_midia.value}' ainda não suportado nesta versão."
            return ResultadoOperacao(
                sucesso=False,
                mensagem=publicacao.erro,
                erro_codigo="TIPO_NAO_SUPORTADO",
            )

        if not creation_id:
            publicacao.status = StatusPublicacao.FALHA
            publicacao.erro = "Falha ao criar container de mídia na Graph API."
            return ResultadoOperacao(
                sucesso=False,
                mensagem=publicacao.erro,
                erro_codigo="CONTAINER_FALHOU",
            )

        # Aguarda processamento de vídeo se necessário
        if publicacao.tipo_midia in (TipoMidia.VIDEO, TipoMidia.REELS):
            logger.info("[Publicador] Aguardando processamento de vídeo (15s)...")
            time.sleep(15)

        media_id = self._publicar_container(creation_id)
        if not media_id:
            publicacao.status = StatusPublicacao.FALHA
            publicacao.erro = "Falha ao publicar container na Graph API."
            return ResultadoOperacao(
                sucesso=False,
                mensagem=publicacao.erro,
                erro_codigo="PUBLICACAO_FALHOU",
            )

        publicacao.id_publicacao = media_id
        publicacao.status = StatusPublicacao.PUBLICADA
        publicacao.publicado_em = datetime.utcnow()

        return ResultadoOperacao(
            sucesso=True,
            mensagem=f"Post publicado com sucesso! ID: {media_id}",
            dados=publicacao.to_dict(),
        )

    def agendar(self, publicacao: PublicacaoInstagram) -> ResultadoOperacao:
        """
        Adiciona uma publicação à fila de agendamento interno.
        A publicação será enviada quando `processar_fila()` for chamado.
        """
        if publicacao.agendamento is None:
            return ResultadoOperacao(
                sucesso=False,
                mensagem="Data/hora de agendamento não definida.",
                erro_codigo="SEM_AGENDAMENTO",
            )
        publicacao.status = StatusPublicacao.AGENDADA
        self._fila_publicacoes.append(publicacao)
        logger.info(
            f"[Publicador] Publicação agendada para: "
            f"{publicacao.agendamento.isoformat()}"
        )
        return ResultadoOperacao(
            sucesso=True,
            mensagem=f"Publicação agendada para {publicacao.agendamento.isoformat()}.",
            dados=publicacao.to_dict(),
        )

    def processar_fila(self) -> List[ResultadoOperacao]:
        """
        Processa publicações agendadas cujo horário já chegou.
        Deve ser chamado periodicamente (ex.: a cada minuto).
        """
        agora = datetime.utcnow()
        resultados: List[ResultadoOperacao] = []
        pendentes = []

        for pub in self._fila_publicacoes:
            if pub.agendamento and pub.agendamento <= agora:
                logger.info(
                    f"[Publicador] Processando publicação agendada: "
                    f"{pub.agendamento.isoformat()}"
                )
                resultado = self.publicar(pub)
                resultados.append(resultado)
            else:
                pendentes.append(pub)

        self._fila_publicacoes = pendentes
        return resultados


# ============================================================
# MONITOR DE MÉTRICAS
# ============================================================

class MonitorInstagram:
    """
    Coleta métricas de engajamento e monitora menções/hashtags.
    """

    def __init__(self, cliente: ClienteGraphAPI):
        self.cliente = cliente
        self._alertas: List[AlertaMonitoramento] = []

    # ── Métricas de publicação ────────────────────────────────

    def coletar_metricas(self, id_publicacao: str) -> ResultadoOperacao:
        """
        Coleta métricas de uma publicação específica via Graph API.
        Campos: like_count, comments_count, reach, impressions, saved.
        """
        if not self.cliente._verificar_rate_limit(RATE_LIMIT_CONSULTAS_HORA):
            return ResultadoOperacao(
                sucesso=False,
                mensagem="Rate limit de consultas atingido (200/hora).",
                erro_codigo="RATE_LIMIT",
            )

        campos = "like_count,comments_count,media_type,timestamp"
        sucesso, resposta = self.cliente.get(
            id_publicacao,
            params={"fields": campos},
        )

        if not sucesso:
            return ResultadoOperacao(
                sucesso=False,
                mensagem="Falha ao consultar métricas básicas.",
                dados=resposta,
                erro_codigo="API_ERRO",
            )

        metricas = MetricasPublicacao(id_publicacao=id_publicacao)
        metricas.curtidas = resposta.get("like_count", 0)
        metricas.comentarios = resposta.get("comments_count", 0)

        # Insights (alcance, impressões, salvamentos) — requer permissão instagram_manage_insights
        sucesso_ins, resposta_ins = self.cliente.get(
            f"{id_publicacao}/insights",
            params={"metric": "reach,impressions,saved"},
        )
        if sucesso_ins and "data" in resposta_ins:
            for item in resposta_ins["data"]:
                nome = item.get("name", "")
                valor = item.get("values", [{}])[0].get("value", 0)
                if nome == "reach":
                    metricas.alcance = valor
                elif nome == "impressions":
                    metricas.impressoes = valor
                elif nome == "saved":
                    metricas.salvamentos = valor

        metricas.engajamento_total = (
            metricas.curtidas + metricas.comentarios + metricas.salvamentos
        )

        # Gerar alerta se engajamento for muito baixo
        if metricas.alcance > 0 and metricas.engajamento_total == 0:
            self._gerar_alerta(
                NivelAlerta.AVISO,
                f"Post {id_publicacao} tem alcance {metricas.alcance} mas zero engajamento.",
                metricas.to_dict(),
            )

        return ResultadoOperacao(
            sucesso=True,
            mensagem="Métricas coletadas com sucesso.",
            dados=metricas.to_dict(),
        )

    def listar_publicacoes(self, limite: int = 10) -> ResultadoOperacao:
        """Lista as publicações mais recentes da conta."""
        account_id = self.cliente.credenciais.instagram_account_id
        campos = "id,caption,media_type,timestamp,like_count,comments_count"
        sucesso, resposta = self.cliente.get(
            f"{account_id}/media",
            params={"fields": campos, "limit": limite},
        )
        if not sucesso:
            return ResultadoOperacao(
                sucesso=False,
                mensagem="Falha ao listar publicações.",
                dados=resposta,
                erro_codigo="API_ERRO",
            )
        return ResultadoOperacao(
            sucesso=True,
            mensagem=f"{len(resposta.get('data', []))} publicações encontradas.",
            dados=resposta,
        )

    def perfil_conta(self) -> ResultadoOperacao:
        """Retorna informações básicas do perfil da conta."""
        account_id = self.cliente.credenciais.instagram_account_id
        campos = "id,username,name,biography,followers_count,follows_count,media_count,profile_picture_url"
        sucesso, resposta = self.cliente.get(
            account_id,
            params={"fields": campos},
        )
        if not sucesso:
            return ResultadoOperacao(
                sucesso=False,
                mensagem="Falha ao obter perfil da conta.",
                dados=resposta,
                erro_codigo="API_ERRO",
            )
        return ResultadoOperacao(
            sucesso=True,
            mensagem="Perfil obtido com sucesso.",
            dados=resposta,
        )

    # ── Alertas ───────────────────────────────────────────────

    def _gerar_alerta(
        self,
        nivel: NivelAlerta,
        mensagem: str,
        dado: Optional[Dict] = None,
    ) -> None:
        alerta = AlertaMonitoramento(
            nivel=nivel, mensagem=mensagem, dado_relacionado=dado
        )
        self._alertas.append(alerta)
        log_fn = logger.warning if nivel == NivelAlerta.AVISO else logger.critical
        log_fn(f"[Monitor] ALERTA {nivel.value.upper()}: {mensagem}")

    def obter_alertas(self, nivel: Optional[NivelAlerta] = None) -> List[Dict]:
        """Retorna alertas gerados, opcionalmente filtrados por nível."""
        alertas = self._alertas
        if nivel:
            alertas = [a for a in alertas if a.nivel == nivel]
        return [a.to_dict() for a in alertas]

    def limpar_alertas(self) -> None:
        self._alertas.clear()
        logger.info("[Monitor] Alertas limpos.")


# ============================================================
# CONECTOR SOCIAL PRINCIPAL (Orquestrador)
# ============================================================

class ConectorSocialInstagram:
    """
    Orquestrador principal do módulo social.
    Integra autenticação, publicação e monitoramento em uma
    interface unificada compatível com o ecossistema Ravena.

    Respeita o Modo Soberano:
      - OFFLINE_TOTAL → todas as operações retornam erro controlado
      - HÍBRIDO       → operações externas permitidas com auditoria
    """

    def __init__(
        self,
        credenciais: Optional[CredenciaisInstagram] = None,
        modo_offline: bool = False,
    ):
        self.modo_offline = modo_offline
        self._status = StatusConexao.DESCONECTADO
        self._auditoria: List[Dict[str, Any]] = []
        self.cliente: Optional[ClienteGraphAPI] = None
        self.publicador: Optional[PublicadorInstagram] = None
        self.monitor: Optional[MonitorInstagram] = None

        if modo_offline:
            self._status = StatusConexao.OFFLINE_TOTAL
            logger.info("[ConectorSocial] Modo OFFLINE_TOTAL ativo — API desabilitada.")
            return

        if credenciais:
            self._inicializar(credenciais)
        else:
            try:
                creds = CredenciaisInstagram.from_env()
                self._inicializar(creds)
            except ValueError as e:
                logger.warning(f"[ConectorSocial] Credenciais não configuradas: {e}")
                self._status = StatusConexao.ERRO_TOKEN

    def _inicializar(self, credenciais: CredenciaisInstagram) -> None:
        """Inicializa os componentes internos com as credenciais fornecidas."""
        self.cliente = ClienteGraphAPI(credenciais)
        self.publicador = PublicadorInstagram(self.cliente)
        self.monitor = MonitorInstagram(self.cliente)
        self._status = StatusConexao.CONECTADO
        logger.info(
            f"[ConectorSocial] Conectado — token hash: "
            f"{credenciais.token_hash()}"
        )

    # ── Verificações ──────────────────────────────────────────

    def _verificar_disponibilidade(self) -> Optional[ResultadoOperacao]:
        """Retorna erro se o conector não estiver disponível."""
        if self.modo_offline or self._status == StatusConexao.OFFLINE_TOTAL:
            return ResultadoOperacao(
                sucesso=False,
                mensagem="Conector Social desabilitado em modo OFFLINE_TOTAL.",
                erro_codigo="OFFLINE_TOTAL",
            )
        if self._status == StatusConexao.ERRO_TOKEN:
            return ResultadoOperacao(
                sucesso=False,
                mensagem="Token de acesso inválido ou não configurado.",
                erro_codigo="ERRO_TOKEN",
            )
        if self._status != StatusConexao.CONECTADO:
            return ResultadoOperacao(
                sucesso=False,
                mensagem=f"Conector não disponível. Status: {self._status.value}",
                erro_codigo="NAO_CONECTADO",
            )
        return None

    def _auditar(self, operacao: str, resultado: ResultadoOperacao) -> None:
        """Registra cada operação no log de auditoria interno."""
        entrada = {
            "operacao": operacao,
            "sucesso": resultado.sucesso,
            "mensagem": resultado.mensagem,
            "erro_codigo": resultado.erro_codigo,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._auditoria.append(entrada)
        logger.info(
            f"[Auditoria] {operacao} — "
            f"{'OK' if resultado.sucesso else 'FALHA'}: {resultado.mensagem}"
        )

    # ── Interface pública ─────────────────────────────────────

    def publicar_post(
        self,
        legenda: str,
        url_midia: str,
        hashtags: Optional[List[str]] = None,
        tipo_midia: TipoMidia = TipoMidia.IMAGEM,
    ) -> ResultadoOperacao:
        """
        Publica um post imediatamente no Instagram.

        Args:
            legenda:    Texto do post (até 2.200 caracteres).
            url_midia:  URL pública da imagem ou vídeo.
            hashtags:   Lista de hashtags (sem o '#').
            tipo_midia: Tipo de mídia (IMAGE, REELS, etc.).

        Returns:
            ResultadoOperacao com id_publicacao em caso de sucesso.
        """
        erro = self._verificar_disponibilidade()
        if erro:
            return erro

        pub = PublicacaoInstagram(
            legenda=legenda,
            url_midia=url_midia,
            tipo_midia=tipo_midia,
            hashtags=hashtags or [],
        )
        resultado = self.publicador.publicar(pub)
        self._auditar("publicar_post", resultado)
        return resultado

    def agendar_post(
        self,
        legenda: str,
        url_midia: str,
        agendamento: datetime,
        hashtags: Optional[List[str]] = None,
        tipo_midia: TipoMidia = TipoMidia.IMAGEM,
    ) -> ResultadoOperacao:
        """
        Agenda um post para publicação futura.

        Args:
            agendamento: Data/hora UTC da publicação.
        """
        erro = self._verificar_disponibilidade()
        if erro:
            return erro

        pub = PublicacaoInstagram(
            legenda=legenda,
            url_midia=url_midia,
            tipo_midia=tipo_midia,
            hashtags=hashtags or [],
            agendamento=agendamento,
        )
        resultado = self.publicador.agendar(pub)
        self._auditar("agendar_post", resultado)
        return resultado

    def processar_agendamentos(self) -> List[ResultadoOperacao]:
        """Processa publicações agendadas cujo horário chegou."""
        erro = self._verificar_disponibilidade()
        if erro:
            return [erro]
        resultados = self.publicador.processar_fila()
        for r in resultados:
            self._auditar("processar_agendamento", r)
        return resultados

    def obter_metricas(self, id_publicacao: str) -> ResultadoOperacao:
        """Coleta métricas de engajamento de um post específico."""
        erro = self._verificar_disponibilidade()
        if erro:
            return erro
        resultado = self.monitor.coletar_metricas(id_publicacao)
        self._auditar("obter_metricas", resultado)
        return resultado

    def listar_posts(self, limite: int = 10) -> ResultadoOperacao:
        """Lista os posts mais recentes da conta."""
        erro = self._verificar_disponibilidade()
        if erro:
            return erro
        resultado = self.monitor.listar_publicacoes(limite)
        self._auditar("listar_posts", resultado)
        return resultado

    def obter_perfil(self) -> ResultadoOperacao:
        """Retorna dados do perfil da conta Instagram conectada."""
        erro = self._verificar_disponibilidade()
        if erro:
            return erro
        resultado = self.monitor.perfil_conta()
        self._auditar("obter_perfil", resultado)
        return resultado

    def status(self) -> Dict[str, Any]:
        """Retorna o status atual do conector."""
        return {
            "status_conexao": self._status.value,
            "modo_offline": self.modo_offline,
            "total_operacoes_auditadas": len(self._auditoria),
            "alertas_ativos": len(self.monitor.obter_alertas()) if self.monitor else 0,
            "fila_agendamentos": (
                len(self.publicador._fila_publicacoes) if self.publicador else 0
            ),
        }

    def historico_auditoria(self, ultimos: int = 20) -> List[Dict[str, Any]]:
        """Retorna as últimas entradas do log de auditoria."""
        return self._auditoria[-ultimos:]


# ============================================================
# FACTORY — integração com o ecossistema Ravena
# ============================================================

def criar_conector_social(modo_offline: bool = False) -> ConectorSocialInstagram:
    """
    Factory function para criar o ConectorSocialInstagram.
    Detecta automaticamente o modo de operação pelo ambiente.

    Em modo OFFLINE_TOTAL (variável LLM_MODE=local e USE_LOCAL_LLM=True),
    o conector é instanciado desabilitado para preservar a soberania digital.
    """
    # Verificar modo soberano via variáveis de ambiente
    llm_mode = os.environ.get("LLM_MODE", "hibrido").lower()
    use_local = os.environ.get("USE_LOCAL_LLM", "False").lower() == "true"
    fallback_externo = os.environ.get("FALLBACK_TO_EXTERNAL", "True").lower() == "true"

    if llm_mode == "local" and use_local and not fallback_externo:
        logger.info(
            "[ConectorSocial] Modo OFFLINE_TOTAL detectado via env — "
            "conector instanciado em modo offline."
        )
        return ConectorSocialInstagram(modo_offline=True)

    if modo_offline:
        return ConectorSocialInstagram(modo_offline=True)

    return ConectorSocialInstagram()


# ── Instância padrão (lazy) ───────────────────────────────────
_conector_padrao: Optional[ConectorSocialInstagram] = None


def obter_conector() -> ConectorSocialInstagram:
    """Retorna a instância singleton do conector social."""
    global _conector_padrao
    if _conector_padrao is None:
        _conector_padrao = criar_conector_social()
    return _conector_padrao


# ── Log de carregamento ───────────────────────────────────────
logger.info("MÓDULO social_connector.py — Conector Social Instagram carregado (Prioridade 4).")
print("PRIORIDADE 4 — CONECTOR SOCIAL INSTAGRAM (social_connector.py) carregado.")
