# Ravena AIM — Health Check Report

**Timestamp:** 2026-10-06T05:28:34.605752  
**Version:** v3.2.6  
**Environment:** unknown  
**Verdict:** HEALTHY

## Summary

| Metric | Value |
|--------|-------|
| Total | 22 |
| ✅ Passed | 19 |
| ⚠️ Warned | 2 |
| ❌ Failed | 1 |
| Time (s) | 18.1 |
| **Integridade do codigo** | **100.0%** (16/16 checks) |
| Prontidao do ambiente | 50.0% (6 checks) |

## Module Results

| # | Module | Status | Details | Time (ms) |
|---|--------|--------|---------|-----------|
| 1 | SecretsManager | ⚠️ WARN | Fonte: unknown | 0/17 secrets | ZT_KEY: MISSING | 3 |
| 2 | ZeroTrust Protocol | ✅ PASS | Token gerado e validado com sucesso | Token: 9eee3245ee2a8590b2fd0c172b8f5b... | 9127 |
| 3 | OmegaOrchestrator v3.2.6 | ✅ PASS | OmegaOrchestrator inicializado | 18 |
| 4 | Omega v3.2.6 | ✅ PASS | Omega v3.2.6 status=OPERACIONAL | 14 |
| 5 | Omega (legacy) | ✅ PASS | DiagnosticoMissao inicializado | 3 |
| 6 | Ravena Model | ❌ FAIL | OSError: AutoModelForCausalLM is designed to be instantiated using the `AutoModelForCausalLM.from_pretrained(pretrained_model_name_or_path)` or `AutoModelForCausalLM.from_config(config)` methods. | 1 |
| 7 | Auditor | ✅ PASS | AnalisadorEscopo inicializado | Métodos: ['analisar'] | 4 |
| 8 | Hacker Agent v3.2.7 | ✅ PASS | Agente: Ravena_Hacker_Elite v1.0.0 (v3.2.7 Integration) | 1 |
| 9 | Hacker Agent v3.2.8 Final | ✅ PASS | Hacker v3.2.8 Final: unknown | 1 |
| 10 | Security Core v3.2.7 | ✅ PASS | HackerAgent inicializado | 1 |
| 11 | RAG Advanced | ✅ PASS | ModuloRAGAvançado inicializado | Classes no módulo: 10 | 4 |
| 12 | RAG Advanced v3.2.6 | ✅ PASS | ModuloRAGAvançado inicializado | 8231 |
| 13 | Signal Bridge (funcional) | ✅ PASS | Módulo funcional OK | Funções-chave: ['process_signal', 'determine_suitability_mode', 'calculate_success_probability'] | 4 |
| 14 | Bybit Connector | ✅ PASS | BybitConnector inicializado | 672 |
| 15 | Trade Brain | ✅ PASS | RiskManager inicializado | 1 |
| 16 | Social Connector | ✅ PASS | ConectorSocialInstagram inicializado | 4 |
| 17 | Telegram Bot | ✅ PASS | TelegramBotRefinement inicializado | Threshold: 0.85 | 1 |
| 18 | Engine Patch Segurança | ✅ PASS | SegurancaIAIntegrator inicializado | 0 |
| 19 | External API Manager | ✅ PASS | ExternalAPIManager v3.2.6 inicializado | 1 |
| 20 | ZeroTrust → OmegaOrchestrator (Auth) | ✅ PASS | Zero Trust ↔ OmegaOrchestrator: comunicação autenticada OK | 2 |
| 21 | Secrets Audit (Conformidade) | ⚠️ WARN | Auditoria: 0/17 carregados | Faltando: ['RAVENA_ZERO_TRUST_SECRET', 'BYBIT_API_KEY', 'BYBIT_API_SECRET', 'OCI_COMPARTMENT_ID', 'QWEN_ENDPOINT_ID', 'KIMI_ENDPOINT_ID'] | 2 |
| 22 | RAG Ingestão + Consulta | ✅ PASS | RAG ingestão OK (consulta requer embeddings externos) | 4 |

---

*Generated at 2026-10-06T05:28:35.765670*