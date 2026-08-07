#!/bin/bash
# ============================================
# ENCRYPTED_PORTS_MAP.MAP - Mapa de Portas Criptografadas
# Ravena Security Sandbox
# ============================================
# Mostra todas as portas criptografadas
# com TLS/SSL pós-quântico.
# ============================================

MAP="
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                    MAPA DE PORTAS CRIPTOGRAFADAS - RAVENA                         ║
╠══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                     ║
║  PORTA    SERVIÇO          PROTOCOLO      CRIPTOGRAFIA        STATUS               ║
║  ─────    ───────          ─────────      ────────────        ──────               ║
║                                                                                     ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐    ║
║  │                          PORTAS CRIPTOGRAFADAS                             │    ║
║  ├─────────────────────────────────────────────────────────────────────────────┤    ║
║  │                                                                             │    ║
║  │  ✅ 22      SSH              TCP           AES-256-GCM       ✅ SEGURO       │    ║
║  │  ✅ 443     HTTPS            TCP           TLS 1.3           ✅ SEGURO       │    ║
║  │  ✅ 3443    Grafana HTTPS    TCP           TLS 1.3           ✅ SEGURO       │    ║
║  │  ✅ 5432    PostgreSQL       TCP           SSL               ✅ SEGURO       │    ║
║  │  ✅ 5643    Kibana HTTPS     TCP           TLS 1.3           ✅ SEGURO       │    ║
║  │  ✅ 6379    Redis            TCP           TLS               ✅ SEGURO       │    ║
║  │  ✅ 9443    Prometheus HTTPS TCP           TLS 1.3           ✅ SEGURO       │    ║
║  │  ✅ 9200    Elasticsearch    TCP           TLS               ✅ SEGURO       │    ║
║  │                                                                             │    ║
║  └─────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                     ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐    ║
║  │                          PORTAS REDIRECIONADAS                             │    ║
║  ├─────────────────────────────────────────────────────────────────────────────┤    ║
║  │                                                                             │    ║
║  │  🔄 80      HTTP             TCP           REDIRECIONA p/ 443              │    ║
║  │  🔄 3000    Grafana HTTP     TCP           REDIRECIONA p/ 3443            │    ║
║  │  🔄 5601    Kibana HTTP      TCP           REDIRECIONA p/ 5643            │    ║
║  │  🔄 8080    Ravena App HTTP  TCP           REDIRECIONA p/ 443             │    ║
║  │  🔄 9090    Prometheus HTTP  TCP           REDIRECIONA p/ 9443            │    ║
║  │                                                                             │    ║
║  └─────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                     ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐    ║
║  │                          ALGORITMOS PÓS-QUÂNTICOS                          │    ║
║  ├─────────────────────────────────────────────────────────────────────────────┤    ║
║  │                                                                             │    ║
║  │  🔐 CRYSTALS-Kyber    - Troca de chaves (Key Exchange)                    │    ║
║  │  🔐 CRYSTALS-Dilithium - Assinatura digital                                │    ║
║  │  🔐 FALCON            - Assinatura digital compacta                        │    ║
║  │  🔐 SPHINCS+          - Assinatura baseada em hash                         │    ║
║  │                                                                             │    ║
║  │  Híbrido: RSA 4096 + ECDSA P-384 + Ed25519 + Pós-Quântico                │    ║
║  │                                                                             │    ║
║  └─────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                     ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐    ║
║  │                          CERTIFICADOS                                      │    ║
║  ├─────────────────────────────────────────────────────────────────────────────┤    ║
║  │                                                                             │    ║
║  │  📁 /etc/ssl/ravena/                                                       │    ║
║  │  ├── certs/                      # Certificados                            │    ║
║  │  │   ├── ca.crt                  # Certificado CA                          │    ║
║  │  │   ├── http.crt                # Certificado HTTP                        │    ║
║  │  │   ├── grafana.crt             # Certificado Grafana                     │    ║
║  │  │   ├── kibana.crt              # Certificado Kibana                      │    ║
║  │  │   ├── ravena-app.crt          # Certificado Ravena App                  │    ║
║  │  │   └── prometheus.crt          # Certificado Prometheus                  │    ║
║  │  ├── private/                    # Chaves privadas                         │    ║
║  │  │   ├── ca.key                  # Chave CA                                │    ║
║  │  │   ├── ca-ec.key               # Chave ECDSA                             │    ║
║  │  │   ├── ca-ed25519.key          # Chave Ed25519                           │    ║
║  │  │   ├── http.key                # Chave HTTP                              │    ║
║  │  │   ├── grafana.key             # Chave Grafana                           │    ║
║  │  │   ├── kibana.key              # Chave Kibana                            │    ║
║  │  │   ├── ravena-app.key          # Chave Ravena App                        │    ║
║  │  │   └── prometheus.key          # Chave Prometheus                        │    ║
║  │  └── csr/                        # Certificate Signing Requests            │    ║
║  │                                                                             │    ║
║  └─────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                     ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"

echo "$MAP"
