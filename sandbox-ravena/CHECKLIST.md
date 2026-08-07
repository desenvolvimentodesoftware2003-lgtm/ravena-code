# ============================================
# CHECKLIST - SANDBOX RAVENA
# ============================================

## Pré-requisitos

- [ ] Docker Desktop instalado e rodando
- [ ] Docker Compose instalado
- [ ] Python 3.8+ instalado
- [ ] pip instalado
- [ ] Portas disponíveis: 8080, 80, 3000, 5601, 9090, 9200, 5432, 6379

---

## Instalação

- [ ] Navegar até o diretório `sandbox-ravena`
- [ ] Executar `setup.bat` (Windows) ou `./setup.sh` (Linux/Mac)
- [ ] Aguardar conclusão da instalação
- [ ] Verificar se todos os containers estão rodando

---

## Verificação

- [ ] Executar `verify_sandbox.bat` ou `./verify_sandbox.sh`
- [ ] Verificar se todos os serviços estão respondendo:
  - [ ] Servidor Ravena: http://localhost:8080
  - [ ] Grafana: http://localhost:3000
  - [ ] Kibana: http://localhost:5601
  - [ ] Prometheus: http://localhost:9090
  - [ ] Elasticsearch: http://localhost:9200
- [ ] Verificar conexão com banco de dados
- [ ] Verificar se as credenciais funcionam

---

## Testes de Segurança

- [ ] Executar `python tests/security_tests.py`
- [ ] Analisar resultados dos testes
- [ ] Verificar se os ataques estão sendo bloqueados
- [ ] Revisar logs de ataque

---

## Monitoramento

- [ ] Acessar Grafana: http://localhost:3000
- [ ] Verificar dashboard de segurança
- [ ] Acessar Kibana: http://localhost:5601
- [ ] Verificar logs de ataque
- [ ] Verificar alertas configurados

---

## Documentação

- [ ] Ler `README.md`
- [ ] Ler `GUIA_COMPLETO.md`
- [ ] Ler `SCRIPTS_WINDOWS.md` (Windows)
- [ ] Ler `monitoring/README.md`

---

## Manutenção

- [ ] Exportar logs periodicamente: `python utils.py --export`
- [ ] Limpar logs antigos: `python utils.py` → Opção 6
- [ ] Verificar uso de disco
- [ ] Monitorar performance

---

## Backup

- [ ] Fazer backup dos dados importantes
- [ ] Verificar se os logs estão sendo salvos
- [ ] Testar restauração de backup

---

## Segurança

- [ ] Verificar se a sandbox está isolada
- [ ] Confirmar que não há acesso externo
- [ ] Revisar logs de acesso
- [ ] Verificar se os dados são fictícios

---

## Produção

- [ ] Implementar correções encontradas
- [ ] Re-executar testes após correções
- [ ] Documentar vulnerabilidades encontradas
- [ ] Criar plano de remediação

---

## Contato

Em caso de problemas:
1. Consulte a documentação
2. Execute scripts de diagnóstico
3. Verifique logs do Docker
4. Reinicie os serviços se necessário
