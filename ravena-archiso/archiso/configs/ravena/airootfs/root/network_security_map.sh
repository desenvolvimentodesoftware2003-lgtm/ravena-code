#!/bin/bash
# ============================================
# NETWORK_SECURITY_MAP.MAP - Mapeamento de Rede e Portas
# Ravena Security Sandbox
# ============================================
# Este arquivo mapeia todas as portas,
# informações sensíveis e configurações
# de segurança da rede.
# ============================================

# ============================================
# 1. MAPEAMENTO DE PORTAS
# ============================================

PORT_MAP="
╔══════════════════════════════════════════════════════════════════════════════╗
║                    MAPEAMENTO DE PORTAS - RAVENA                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  PORTA    SERVIÇO          CRIPTOGRAFADO    STATUS      DESCRIÇÃO           ║
║  ─────    ───────          ─────────────    ──────      ─────────           ║
║  22       SSH              ✅ SIM           ✅ ATIVO    Acesso remoto        ║
║  80       HTTP             ❌ NÃO          ✅ ATIVO    Web server           ║
║  443      HTTPS            ✅ SIM          ✅ ATIVO    Web seguro           ║
║  3000     Grafana          ❌ NÃO          ✅ ATIVO    Monitoramento        ║
║  5432     PostgreSQL       ✅ SIM          ✅ ATIVO    Banco de dados       ║
║  5601     Kibana           ❌ NÃO          ✅ ATIVO    Análise de logs      ║
║  6379     Redis            ✅ SIM          ✅ ATIVO    Cache                ║
║  8080     Ravena App       ❌ NÃO          ✅ ATIVO    Aplicação principal  ║
║  9090     Prometheus       ❌ NÃO          ✅ ATIVO    Métricas             ║
║  9200     Elasticsearch    ✅ SIM          ✅ ATIVO    Busca de logs        ║
║                                                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"

# ============================================
# 2. INFORMAÇÕES SENSÍVEIS
# ============================================

SENSITIVE_INFO="
╔══════════════════════════════════════════════════════════════════════════════╗
║                    INFORMAÇÕES SENSÍVEIS                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  CATEGORIA          DADOS                    RISCO        RECOMENDAÇÃO      ║
║  ─────────          ─────                    ─────        ───────────       ║
║                                                                             ║
║  CREDENCIAIS                                                              ║
║  ├─ DB User         ravena                    🟢 BAIXO    Uso pessoal        ║
║  ├─ DB Pass         (nenhuma - sem auth)      🟢 BAIXO    Sistema pessoal    ║
║  ├─ JWT Secret      (não necessário)          🟢 BAIXO    Sem autenticação   ║
║  ├─ Redis Pass      (nenhuma)                 🟢 BAIXO    Uso local          ║
║  └─ Grafana Pass    (nenhuma)                 🟢 BAIXO    Uso local          ║
║                                                                             ║
║  REDE                                                                     ║
║  ├─ Subnet          172.20.0.0/16            🟢 BAIXO    Rede interna       ║
║  ├─ Gateway         172.20.0.1               🟢 BAIXO    Rotas internas     ║
║  └─ DNS             8.8.8.8                  🟡 MÉDIO    Usar DNS interno   ║
║                                                                             ║
║  CERTIFICADOS                                                              ║
║  ├─ SSL/TLS         (não configurado)        🔴 ALTO     Implementar        ║
║  └─ SSH Keys        (padrão)                 🟡 MEDIO    Gerar novas        ║
║                                                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"

# ============================================
# 3. STATUS DE CRIPTOGRAFIA
# ============================================

CRYPTO_STATUS="
╔══════════════════════════════════════════════════════════════════════════════╗
║                    STATUS DE CRIPTOGRAFIA                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  PORTA    PROTOCOLO      CRIPTOGRAFIA    STATUS      AÇÃO NECESSÁRIA       ║
║  ─────    ─────────      ────────────    ──────      ──────────────        ║
║                                                                             ║
║  22       SSH            ✅ AES-256      ✅ OK       Nenhuma               ║
║  80       HTTP           ❌ NENHUMA      ⚠️ CRÍTICO  Redirecionar p/ 443   ║
║  443      HTTPS          ✅ TLS 1.3      ✅ OK       Nenhuma               ║
║  3000     HTTP           ❌ NENHUMA      ⚠️ ALTO     Configurar TLS        ║
║  5432     PostgreSQL     ✅ SSL          ✅ OK       Nenhuma               ║
║  5601     HTTP           ❌ NENHUMA      ⚠️ ALTO     Configurar TLS        ║
║  6379     Redis          ✅ TLS          ✅ OK       Nenhuma               ║
║  8080     HTTP           ❌ NENHUMA      ⚠️ CRÍTICO  Configurar TLS        ║
║  9090     HTTP           ❌ NENHUMA      ⚠️ ALTO     Configurar TLS        ║
║  9200     Elasticsearch  ✅ TLS          ✅ OK       Nenhuma               ║
║                                                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"

# ============================================
# 4. REDE - ACESSO À INTERNET VIA NOMAD
# ============================================

NOMAD_CONFIG="
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CONFIGURAÇÃO NOMAD - ACESSO À INTERNET                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  NOMAD permite acesso à internet mesmo em ambientes isolados.              ║
║  Configuração para usar proxy/VPN para acessar a internet.                 ║
║                                                                             ║
║  OPÇÕES DE ACESSO:                                                          ║
║                                                                             ║
║  1. TOR (Rede Anônima)                                                     ║
║     ├─ Porta: 9050                                                          ║
║     ├─ Criptografia: ✅ Camadas múltiplas                                   ║
║     ├─ Anonimato: ✅ ALTO                                                   ║
║     └─ Velocidade: 🟡 LENTA                                                ║
║                                                                             ║
║  2. VPN (Rede Privada Virtual)                                             ║
║     ├─ Porta: 1194                                                          ║
║     ├─ Criptografia: ✅ AES-256                                             ║
║     ├─ Anonimato: 🟡 MÉDIO                                                 ║
║     └─ Velocidade: ✅ RÁPIDA                                                ║
║                                                                             ║
║  3. PROXY SOCKS5                                                           ║
║     ├─ Porta: 1080                                                          ║
║     ├─ Criptografia: ⚠️ OPCIONAL                                            ║
║     ├─ Anonimato: 🟡 MÉDIO                                                 ║
║     └─ Velocidade: ✅ RÁPIDA                                                ║
║                                                                             ║
║  4. CLOUDFLARE WARP                                                        ║
║     ├─ Porta: 443                                                           ║
║     ├─ Criptografia: ✅ WARP+                                               ║
║     ├─ Anonimato: 🟡 MÉDIO                                                 ║
║     └─ Velocidade: ✅ MUITO RÁPIDA                                         ║
║                                                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"

# Exibir mapeamento
echo "$PORT_MAP"
echo ""
echo "$SENSITIVE_INFO"
echo ""
echo "$CRYPTO_STATUS"
echo ""
echo "$NOMAD_CONFIG"
