# Ravena AIM — Health Check Report

**Timestamp:** 2026-10-06T05:23:50.725476  
**Version:** v3.2.6  
**Environment:** unknown  
**Verdict:** PARTIAL

## Summary

| Metric | Value |
|--------|-------|
| Total | 22 |
| ✅ Passed | 19 |
| ⚠️ Warned | 2 |
| ❌ Failed | 1 |
| Time (s) | 19.41 |
| Health Score | 86.4% |

## Module Results

| # | Module | Status | Details | Time (ms) |
|---|--------|--------|---------|-----------|
| 1 | SecretsManager | ⚠️ WARN | Fonte: unknown | 0/17 secrets | ZT_KEY: MISSING | 3 |
| 2 | ZeroTrust Protocol | ✅ PASS | Token gerado e validado com sucesso | Token: 97f1055213e1343f371444afffafa7... | 10144 |
| 3 | OmegaOrchestrator v3.2.6 | ✅ PASS | OmegaOrchestrator inicializado | 29 |
| 4 | Omega v3.2.6 | ✅ PASS | Omega v3.2.6 status=OPERACIONAL | 11 |
| 5 | Omega (legacy) | ✅ PASS | DiagnosticoMissao inicializado | 3 |
| 6 | Ravena Model | ❌ FAIL | OSError: AutoModelForCausalLM is designed to be instantiated using the `AutoModelForCausalLM.from_pretrained(pretrained_model_name_or_path)` or `AutoModelForCausalLM.from_config(config)` methods. | 2 |
| 7 | Auditor | ✅ PASS | AnalisadorEscopo inicializado | Métodos: ['analisar'] | 3 |
| 8 | Hacker Agent v3.2.7 | ✅ PASS | Agente: Ravena_Hacker_Elite v1.0.0 (v3.2.7 Integration) | 1 |
| 9 | Hacker Agent v3.2.8 Final | ✅ PASS | Hacker v3.2.8 Final: unknown | 1 |
| 10 | Security Core v3.2.7 | ✅ PASS | HackerAgent inicializado | 1 |
| 11 | RAG Advanced | ✅ PASS | ModuloRAGAvançado inicializado | Classes no módulo: 10 | 5 |
| 12 | RAG Advanced v3.2.6 | ✅ PASS | ModuloRAGAvançado inicializado | 8476 |
| 13 | Signal Bridge (funcional) | ✅ PASS | Módulo funcional OK | Funções-chave: ['process_signal', 'determine_suitability_mode', 'calculate_success_probability'] | 4 |
| 14 | Bybit Connector | ✅ PASS | BybitConnector inicializado | 711 |
| 15 | Trade Brain | ✅ PASS | RiskManager inicializado | 3 |
| 16 | Social Connector | ✅ PASS | ConectorSocialInstagram inicializado | 5 |
| 17 | Telegram Bot | ✅ PASS | TelegramBotRefinement inicializado | Threshold: 0.85 | 2 |
| 18 | Engine Patch Segurança | ✅ PASS | SegurancaIAIntegrator inicializado | 1 |
| 19 | External API Manager | ✅ PASS | ExternalAPIManager v3.2.6 inicializado | 3 |
| 20 | ZeroTrust → OmegaOrchestrator (Auth) | ✅ PASS | Zero Trust ↔ OmegaOrchestrator: comunicação autenticada OK | 1 |
| 21 | Secrets Audit (Conformidade) | ⚠️ WARN | Auditoria: 0/17 carregados | Faltando: ['RAVENA_ZERO_TRUST_SECRET', 'BYBIT_API_KEY', 'BYBIT_API_SECRET', 'OCI_COMPARTMENT_ID', 'QWEN_ENDPOINT_ID', 'KIMI_ENDPOINT_ID'] | 2 |
| 22 | RAG Ingestão + Consulta | ✅ PASS | RAG ingestão OK (consulta requer embeddings externos) | 3 |

---

*Generated at 2026-10-06T05:23:51.857285*