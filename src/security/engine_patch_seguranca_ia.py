"""
╔══════════════════════════════════════════════════════════════════════════╗
║  RAVENA AI — src/engine.py  [PATCH — Prioridade 3]                     ║
║  Adição da categoria seguranca_ia ao MockChromaCollection               ║
║  Versão: 2.1.0  |  Abril 2026  |  Arquiteto: Alexsander (LS)           ║
╚══════════════════════════════════════════════════════════════════════════╝

COMO APLICAR:
  Este arquivo documenta EXATAMENTE o que adicionar ao engine.py existente.
  Cada bloco está marcado com:

    ── ONDE INSERIR ──  →  localização exata no engine.py
    ── CÓDIGO NOVO   ──  →  trecho a ser colado

  Pré-requisito cumprido: cognitive_ingestion.py ✅ (Prioridade 1 concluída)

OBJETIVO (Prioridade 3 — Documento Consolidado V2.0):
  Adicionar categoria 'seguranca_ia' ao MockChromaCollection para que:
    1. A Ponte de Inteligência consulte regras de segurança de IA
    2. O orquestrador roteia queries de segurança para o agente correto
    3. O ToolManager valide ferramentas antes de executar (via auditor.py)
    4. O Lockdown V2.2 tenha base de conhecimento própria para validação
"""

# ══════════════════════════════════════════════════════════════════════════
#
#  PATCH 1 — MockChromaCollection
#  ONDE INSERIR: dentro da classe MockChromaCollection, no dicionário
#  self._documentos (ou equivalente) onde ficam as outras categorias.
#
#  Padrão atual esperado no engine.py:
#
#    self._documentos = {
#        "python":    [...],
#        "seguranca": [...],
#        "logica":    [...],
#    }
#
#  Adicionar a chave "seguranca_ia" abaixo das existentes:
#
# ══════════════════════════════════════════════════════════════════════════

SEGURANCA_IA_DOCS = {
    "seguranca_ia": [

        # ── Bloco 1: Prompt Injection e Lockdown V2.2 ──────────────────
        {
            "id":        "sec_ia_001",
            "conteudo": (
                "Prompt Injection é o principal vetor de ataque contra sistemas LLM. "
                "Ocorre quando input do usuário sobrescreve o system prompt original. "
                "O Lockdown V2.2 da Ravena aplica filtro de saída obrigatório em todas "
                "as respostas antes de entregar ao usuário. "
                "Regra: nenhum output bypassa o JuizUniversal."
            ),
            "categoria":  "seguranca_ia",
            "subcategoria": "prompt_injection",
            "fonte":      "Lockdown V2.2 — Ravena AI",
            "confianca":  0.97,
            "tags":       ["prompt_injection", "lockdown", "juiz_universal"],
        },
        {
            "id":        "sec_ia_002",
            "conteudo": (
                "Jailbreak é a tentativa de fazer o modelo ignorar suas restrições "
                "via roleplay, framing alternativo ou injeção multilíngue. "
                "Defesas: validação semântica do input, comparação com padrões "
                "conhecidos de jailbreak no MockChromaCollection, e rejeição silenciosa "
                "sem expor o motivo ao usuário (não dar feedback ao atacante)."
            ),
            "categoria":  "seguranca_ia",
            "subcategoria": "jailbreak",
            "fonte":      "Lockdown V2.2 — Ravena AI",
            "confianca":  0.95,
            "tags":       ["jailbreak", "roleplay_attack", "lockdown"],
        },
        {
            "id":        "sec_ia_003",
            "conteudo": (
                "Exfiltração de dados via contexto ocorre quando o modelo é induzido "
                "a repetir conteúdo do system prompt, memória episódica ou chromadb. "
                "Prevenção: nunca retornar o system prompt diretamente; "
                "o JuizUniversal bloqueia respostas que contenham padrões de "
                "'{system}', '```', 'INSTRUÇÃO:', ou reprodução do prompt original."
            ),
            "categoria":  "seguranca_ia",
            "subcategoria": "exfiltracao",
            "fonte":      "Lockdown V2.2 — Ravena AI",
            "confianca":  0.96,
            "tags":       ["exfiltracao", "system_prompt", "lockdown"],
        },

        # ── Bloco 2: Parâmetros Anti-Alucinação ───────────────────────
        {
            "id":        "sec_ia_004",
            "conteudo": (
                "Parâmetros anti-alucinação configurados no motor Ravena V2.0: "
                "RepetitionPenalty=1.5 (inibe loops de tokens), "
                "Temperature=0.4 (saída determinística e técnica), "
                "NoRepeatNGram=3 (impede sequências repetitivas de 3 palavras). "
                "Esses valores são fixos — não alterar sem teste de regressão completo "
                "em /tests/."
            ),
            "categoria":  "seguranca_ia",
            "subcategoria": "anti_alucinacao",
            "fonte":      "Documento Consolidado V2.0 — Seção 2.2",
            "confianca":  0.99,
            "tags":       ["anti_alucinacao", "temperature", "parametros_motor"],
        },
        {
            "id":        "sec_ia_005",
            "conteudo": (
                "Alucinação em sistemas RAG ocorre quando o modelo gera informação "
                "não presente no contexto recuperado. A Ponte de Inteligência (PonteInteligencia) "
                "calcula score_conformidade comparando a resposta gerada com os documentos "
                "do ChromaDB. Se score_conformidade < SEMANTIC_THRESHOLD, a resposta "
                "é marcada como não confiável e o JuizUniversal solicita reformulação."
            ),
            "categoria":  "seguranca_ia",
            "subcategoria": "anti_alucinacao",
            "fonte":      "engine.py — PonteInteligencia",
            "confianca":  0.94,
            "tags":       ["alucinacao", "rag", "ponte_inteligencia", "score_conformidade"],
        },

        # ── Bloco 3: Auditoria de Ferramentas Externas ────────────────
        {
            "id":        "sec_ia_006",
            "conteudo": (
                "Ferramentas externas integradas ao ToolManager (SerpAPI, AwesomeAPI, "
                "Sandbox Python) representam superfície de ataque. "
                "Protocolo obrigatório antes de integrar qualquer nova ferramenta: "
                "1) executar auditor.py com análise estática + sandbox; "
                "2) verificar domínios na whitelist; "
                "3) resultado deve ser APROVADA ou APROVADA_COM_RESTRICOES. "
                "Trade Claw (link 29) está BLOQUEADO até auditoria completa."
            ),
            "categoria":  "seguranca_ia",
            "subcategoria": "auditoria_ferramentas",
            "fonte":      "auditor.py — Ravena AI",
            "confianca":  0.98,
            "tags":       ["auditoria", "tool_manager", "trade_claw", "whitelist"],
        },
        {
            "id":        "sec_ia_007",
            "conteudo": (
                "Sandbox Python do ToolManager executa código com timeout de 10 segundos "
                "e isolamento de processo. Arquivos: acesso permitido apenas em "
                "./ravena_tools_sandbox/. Rede: apenas domínios da whitelist. "
                "Qualquer tentativa de acesso a .env, chroma_db/, seguranca/ ou "
                "tokens é bloqueada e registrada em logs/auditoria/."
            ),
            "categoria":  "seguranca_ia",
            "subcategoria": "sandbox",
            "fonte":      "auditor.py + ToolManager — Ravena AI",
            "confianca":  0.97,
            "tags":       ["sandbox", "timeout", "isolamento", "tool_manager"],
        },

        # ── Bloco 4: Segurança de Infraestrutura ──────────────────────
        {
            "id":        "sec_ia_008",
            "conteudo": (
                "Windows 7 sem suporte de segurança desde janeiro de 2020. "
                "Qualquer serviço da Ravena exposto à internet nesse ambiente "
                "representa superfície de ataque não remediável via patch. "
                "Ação imediata: migrar serviços críticos para instância Oracle Cloud "
                "ou container isolado. PC de 2009 deve ser tratado como ponto único "
                "de falha — Oracle Cloud como backup ativo, não passivo."
            ),
            "categoria":  "seguranca_ia",
            "subcategoria": "infraestrutura",
            "fonte":      "Documento Consolidado V2.0 — Seção 6.2",
            "confianca":  0.96,
            "tags":       ["windows7", "oracle_cloud", "infraestrutura", "ponto_falha"],
        },
        {
            "id":        "sec_ia_009",
            "conteudo": (
                "Monitoramento de rede com Wireshark para detectar processos drenando "
                "banda do ambiente Ravena. Upload alto constante (24h) pode indicar: "
                "sincronização de nuvem mal configurada, vazamento de dados, ou "
                "processo malicioso em segundo plano. "
                "Prioridade de banda deve ser garantida para o processo ravena_modular_main.py."
            ),
            "categoria":  "seguranca_ia",
            "subcategoria": "infraestrutura",
            "fonte":      "Documento Consolidado V2.0 — Seção 5 + Bloco 03 dos links",
            "confianca":  0.89,
            "tags":       ["wireshark", "rede", "banda", "monitoramento"],
        },

        # ── Bloco 5: Memória e Privacidade ────────────────────────────
        {
            "id":        "sec_ia_010",
            "conteudo": (
                "Manipulação de memória de curto prazo (deque em memoria.py): "
                "um atacante pode tentar saturar a janela de contexto com informação "
                "falsa para influenciar respostas futuras da Ravena. "
                "Proteção: JuizUniversal valida consistência entre memória episódica "
                "(episodios_dev.json) e a resposta atual antes de armazenar. "
                "Entradas com score_conformidade < 0.65 não são persistidas."
            ),
            "categoria":  "seguranca_ia",
            "subcategoria": "memoria",
            "fonte":      "memoria.py + juiz_universal.py — Ravena AI",
            "confianca":  0.93,
            "tags":       ["memoria", "deque", "juiz_universal", "episodios"],
        },
    ]
}


# ══════════════════════════════════════════════════════════════════════════
#
#  PATCH 2 — ROTEAMENTO DO ORQUESTRADOR
#  ONDE INSERIR: em src/subagentes_especializados.py, na função/dict
#  que mapeia palavras-chave para agentes especializados.
#
#  Adicionar as palavras-chave que disparam o agente de segurança_ia:
#
# ══════════════════════════════════════════════════════════════════════════

KEYWORDS_SEGURANCA_IA = [
    # Ataques
    "prompt injection", "jailbreak", "bypass", "injeção",
    "exfiltração", "vazamento", "ataque", "exploit",
    # Defesa
    "lockdown", "auditoria", "sandox", "whitelist", "bloqueio",
    # Parâmetros
    "temperatura", "temperature", "alucinação", "alucinacao",
    "repetition penalty", "conformidade",
    # Infraestrutura
    "windows 7", "oracle cloud", "wireshark", "banda",
    # Ferramentas
    "trade claw", "serpapi", "tool_manager", "ferramenta externa",
]

ROTEAMENTO_SEGURANCA_IA = {
    "agente":         "seguranca_ia",
    "descricao":      "Consultas sobre segurança do sistema Ravena e proteção contra ataques de IA",
    "collection":     "seguranca_ia",      # busca nesta subcategoria do ChromaDB
    "keywords":       KEYWORDS_SEGURANCA_IA,
    "modelo_lora":    "security",          # adaptador LoRA específico (já existente)
    "fallback_agente": "logica",           # se não houver match claro
}


# ══════════════════════════════════════════════════════════════════════════
#
#  PATCH 3 — INTEGRAÇÃO AUDITOR + TOOL MANAGER
#  ONDE INSERIR: dentro da classe ToolManager em engine.py,
#  no método que registra ou executa ferramentas externas.
#
#  Adicionar chamada ao auditor.py antes de qualquer execução:
#
# ══════════════════════════════════════════════════════════════════════════

PATCH_TOOL_MANAGER = '''
# ── Adicionar no início do método executar_ferramenta() ou registrar() ──

from auditor import Auditor as _Auditor

_auditor_instance = _Auditor()  # singleton — instanciar uma vez na classe

def _validar_antes_executar(self, nome_ferramenta: str, codigo: str) -> bool:
    """
    Validação obrigatória antes de executar qualquer ferramenta externa.
    Retorna True se aprovada, False se reprovada.
    Integra o auditor.py ao fluxo do ToolManager.
    """
    resultado = _auditor_instance.validacao_rapida(codigo, nome_ferramenta)
    if not resultado["aprovado"]:
        import logging
        logging.getLogger("ravena.engine").warning(
            f"[ToolManager] Ferramenta '{nome_ferramenta}' BLOQUEADA pelo auditor. "
            f"Alertas: {resultado['alertas']}"
        )
        return False
    return True
'''


# ══════════════════════════════════════════════════════════════════════════
#
#  PATCH 4 — CONFIGURAÇÕES GLOBAIS
#  ONDE INSERIR: no bloco de constantes globais do engine.py,
#  junto de SEMANTIC_THRESHOLD, GLOBAL_MATCH_THRESHOLD, PESOS etc.
#
# ══════════════════════════════════════════════════════════════════════════

# Constantes a adicionar no engine.py
LIMITE_CONFIANCA_SEGURANCA_IA  = 0.90   # mais restritivo que o padrão (0.75)
PONTUACAO_MIN_SEGURANCA_IA     = 0.85   # score mínimo para respostas de segurança
CATEGORIA_SEGURANCA_IA         = "seguranca_ia"
SUBCATEGORIAS_SEGURANCA_IA     = [
    "prompt_injection",
    "jailbreak",
    "exfiltracao",
    "anti_alucinacao",
    "auditoria_ferramentas",
    "sandbox",
    "infraestrutura",
    "memoria",
]


# ══════════════════════════════════════════════════════════════════════════
#  CLASSE DE INTEGRAÇÃO — Aplica os 4 patches no engine.py existente
# ══════════════════════════════════════════════════════════════════════════

class SegurancaIAIntegrator:
    """
    Integra a categoria seguranca_ia ao sistema Ravena.

    Pode ser usado de duas formas:

    A) Standalone — popula o ChromaDB real via cognitive_ingestion.py:
        integrator = SegurancaIAIntegrator()
        integrator.popular_chromadb()

    B) Injeção em runtime — adiciona ao MockChromaCollection em memória:
        integrator.injetar_mock_collection(mock_instance)

    C) Verificação — checa se a categoria já está presente:
        integrator.verificar_instalacao()
    """

    def __init__(self):
        self.docs = SEGURANCA_IA_DOCS["seguranca_ia"]
        self.keywords = KEYWORDS_SEGURANCA_IA

    # ── A) Popular ChromaDB real via cognitive_ingestion ──────────────
    def popular_chromadb(self) -> dict:
        """
        Ingere os documentos de seguranca_ia no ChromaDB real.
        Requer cognitive_ingestion.py instalado (Prioridade 1 ✅).
        """
        try:
            from cognitive_ingestion import CognitiveIngestion
        except ImportError:
            return {
                "status": "erro",
                "motivo": "cognitive_ingestion.py não encontrado — Prioridade 1 deve estar concluída",
            }

        pipeline = CognitiveIngestion()
        total_ok = 0

        for doc in self.docs:
            resultado = pipeline.ingerir_texto(
                texto=doc["conteudo"],
                categoria=doc["categoria"],
                confianca=doc["confianca"],
                origem=doc["fonte"],
                tags=doc["tags"],
            )
            if resultado.get("status") == "ok":
                total_ok += 1

        return {
            "status":           "ok",
            "docs_ingeridos":   total_ok,
            "total_docs":       len(self.docs),
            "categoria":        CATEGORIA_SEGURANCA_IA,
            "subcategorias":    SUBCATEGORIAS_SEGURANCA_IA,
        }

    # ── B) Injetar no MockChromaCollection em runtime ─────────────────
    def injetar_mock_collection(self, mock_instance) -> None:
        """
        Adiciona seguranca_ia ao MockChromaCollection do engine.py
        sem precisar editar o arquivo diretamente.

        Uso no engine.py:
            from engine_patch_seguranca_ia import SegurancaIAIntegrator
            integrator = SegurancaIAIntegrator()
            integrator.injetar_mock_collection(mock_chroma)
        """
        # Tenta detectar a estrutura do MockChromaCollection
        if hasattr(mock_instance, "_documentos"):
            mock_instance._documentos["seguranca_ia"] = self.docs
        elif hasattr(mock_instance, "documentos"):
            mock_instance.documentos["seguranca_ia"] = self.docs
        elif hasattr(mock_instance, "_data"):
            mock_instance._data["seguranca_ia"] = self.docs
        else:
            # Força via __dict__ como último recurso
            for attr in vars(mock_instance):
                val = getattr(mock_instance, attr)
                if isinstance(val, dict) and any(
                    k in val for k in ("python", "seguranca", "logica")
                ):
                    val["seguranca_ia"] = self.docs
                    break

        print(
            f"[SegurancaIA] {len(self.docs)} documentos injetados no MockChromaCollection. "
            f"Subcategorias: {SUBCATEGORIAS_SEGURANCA_IA}"
        )

    # ── C) Verificar instalação ────────────────────────────────────────
    def verificar_instalacao(self) -> dict:
        """
        Verifica se seguranca_ia já está presente no ChromaDB real.
        """
        try:
            import chromadb
            from chromadb.config import Settings
            client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=Settings(anonymized_telemetry=False),
            )
            colecoes = [c.name for c in client.list_collections()]

            instalado = False
            total_docs = 0
            for nome_col in colecoes:
                col = client.get_collection(nome_col)
                res = col.get(where={"categoria": CATEGORIA_SEGURANCA_IA})
                if res and res.get("ids"):
                    instalado = True
                    total_docs += len(res["ids"])

            return {
                "instalado":     instalado,
                "total_docs":    total_docs,
                "colecoes":      colecoes,
                "categoria":     CATEGORIA_SEGURANCA_IA,
            }

        except Exception as e:
            return {"instalado": False, "erro": str(e)}

    # ── Resumo dos patches ────────────────────────────────────────────
    def resumo_patches(self) -> str:
        linhas = [
            "\n" + "="*60,
            "  PATCHES PARA engine.py — Prioridade 3",
            "="*60,
            f"  PATCH 1: {len(self.docs)} docs → MockChromaCollection['seguranca_ia']",
            f"  PATCH 2: {len(self.keywords)} keywords → subagentes_especializados.py",
            "  PATCH 3: auditor.py → ToolManager._validar_antes_executar()",
            "  PATCH 4: 4 constantes globais → engine.py (topo do arquivo)",
            "="*60,
            "  Subcategorias adicionadas:",
        ]
        for sub in SUBCATEGORIAS_SEGURANCA_IA:
            linhas.append(f"    • {sub}")
        linhas.append("="*60 + "\n")
        return "\n".join(linhas)


# ══════════════════════════════════════════════════════════════════════════
#  DEMO — Execução direta para validação
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🟣 RAVENA — Patch Prioridade 3: seguranca_ia → engine.py\n")

    integrator = SegurancaIAIntegrator()

    # Mostra resumo dos patches
    print(integrator.resumo_patches())

    # Verifica se ChromaDB já tem a categoria
    print("🔍 Verificando instalação no ChromaDB...")
    status = integrator.verificar_instalacao()

    if status.get("instalado"):
        print(f"  ✅ Categoria já instalada — {status['total_docs']} docs encontrados.")
    else:
        print("  ⚠  Categoria não encontrada. Populando ChromaDB...")
        resultado = integrator.popular_chromadb()
        if resultado["status"] == "ok":
            print(
                f"  ✅ {resultado['docs_ingeridos']}/{resultado['total_docs']} "
                f"documentos ingeridos com sucesso."
            )
        else:
            print(f"  ❌ Erro: {resultado.get('motivo')}")

    # Demonstra injeção no MockChromaCollection simulado
    print("\n🔧 Testando injeção no MockChromaCollection...")

    class MockChromaSimulado:
        """Simula o MockChromaCollection do engine.py."""
        def __init__(self):
            self._documentos = {
                "python":    [{"id": "py_001", "conteudo": "Sintaxe Python..."}],
                "seguranca": [{"id": "sec_001", "conteudo": "Firewalls..."}],
                "logica":    [{"id": "log_001", "conteudo": "Lógica formal..."}],
            }

    mock = MockChromaSimulado()
    print(f"  Antes: categorias = {list(mock._documentos.keys())}")
    integrator.injetar_mock_collection(mock)
    print(f"  Depois: categorias = {list(mock._documentos.keys())}")
    print(f"  Docs em seguranca_ia: {len(mock._documentos['seguranca_ia'])}")

    print("\n✅ engine_patch_seguranca_ia.py operacional.")
    print("   Próximo passo (Prioridade 4): src/social_connector.py\n")
