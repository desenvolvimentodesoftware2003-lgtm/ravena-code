# Ravena AIM — Health Check Report

**Timestamp:** 2026-10-06T05:53:34.196016  
**Version:** v3.2.6  
**Environment:** unknown  
**Verdict:** HEALTHY

## Summary

| Metric | Value |
|--------|-------|
| Total | 22 |
| ✅ Passed | 20 |
| ⚠️ Warned | 2 |
| ❌ Failed | 0 |
| Time (s) | 19.03 |
| **Integridade do codigo** | **100.0%** (16/16 checks) |
| Prontidao do ambiente | 66.7% (6 checks) |

## Module Results

| # | Module | Status | Details | Time (ms) |
|---|--------|--------|---------|-----------|
| 1 | SecretsManager | ⚠️ WARN | Fonte: unknown | 0/19 secrets | ZT_KEY: MISSING | 5 |
| 2 | ZeroTrust Protocol | ✅ PASS | Token gerado e validado com sucesso | Token: 423299cb889da4832821c7250ad7d1... | 9737 |
| 3 | OmegaOrchestrator v3.2.6 | ✅ PASS | OmegaOrchestrator inicializado | 16 |
| 4 | Omega v3.2.6 | ✅ PASS | Omega v3.2.6 status=OPERACIONAL | 13 |
| 5 | Omega (legacy) | ✅ PASS | DiagnosticoMissao inicializado | 3 |
| 6 | Ravena Model | ✅ PASS | RavenaModel inicializado | 2 |
| 7 | Auditor | ✅ PASS | AnalisadorEscopo inicializado | Métodos: ['analisar'] | 2 |
| 8 | Hacker Agent v3.2.7 | ✅ PASS | Agente: Ravena_Hacker_Elite v1.0.0 (v3.2.7 Integration) | 1 |
| 9 | Hacker Agent v3.2.8 Final | ✅ PASS | Hacker v3.2.8 Final: unknown | 1 |
| 10 | Security Core v3.2.7 | ✅ PASS | SecurityCore inicializado | 0 |
| 11 | RAG Advanced | ✅ PASS | ModuloRAGAvançado inicializado | Classes no módulo: 10 | 5 |
| 12 | RAG Advanced v3.2.6 | ✅ PASS | ModuloRAGAvançado inicializado | 8497 |
| 13 | Signal Bridge (funcional) | ✅ PASS | Módulo funcional OK | Funções-chave: ['process_signal', 'determine_suitability_mode', 'calculate_success_probability'] | 6 |
| 14 | Bybit Connector | ✅ PASS | BybitConnector inicializado | 724 |
| 15 | Trade Brain | ✅ PASS | RiskManager inicializado | 1 |
| 16 | Social Connector | ✅ PASS | ConectorSocialInstagram inicializado | 6 |
| 17 | Telegram Bot | ✅ PASS | TelegramBotRefinement inicializado | Threshold: 0.85 | 0 |
| 18 | Engine Patch Segurança | ✅ PASS | SegurancaIAIntegrator inicializado | 2 |
| 19 | External API Manager | ✅ PASS | ExternalAPIManager v3.2.6 inicializado | 0 |
| 20 | ZeroTrust → OmegaOrchestrator (Auth) | ✅ PASS | Zero Trust ↔ OmegaOrchestrator: comunicação autenticada OK | 1 |
| 21 | Secrets Audit (Conformidade) | ⚠️ WARN | Auditoria: 0/19 carregados | Faltando: ['RAVENA_ZERO_TRUST_SECRET', 'BYBIT_API_KEY', 'BYBIT_API_SECRET', 'OCI_COMPARTMENT_ID', 'QWEN_ENDPOINT_ID', 'KIMI_ENDPOINT_ID'] | 1 |
| 22 | RAG Ingestão + Consulta | ✅ PASS | RAG ingestão OK (consulta requer embeddings externos) | 3 |

---

*Generated at 2026-10-06T05:53:35.235041*