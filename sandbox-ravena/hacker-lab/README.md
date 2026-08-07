# LABORATÓRIO DO AGENTE HACKER

## Visão Geral
Este é o laboratório do agente hacker para testes de segurança na Sandbox Ravena.
O agente usa **ferramentas normais de sistema operacional** para executar testes.

## Ferramentas Disponíveis
- **nmap**: Varredura de portas e serviços
- **curl**: Requisições HTTP
- **python3**: Scripts de automação
- **netcat**: Testes de conexão
- **sqlmap**: SQL Injection automatizado
- **nikto**: Varredura web

## Como Usar

### 1. Navegar até o laboratório
```bash
cd ~/hacker-lab
```

### 2. Executar testes individualmente
```bash
./01_port_scan.sh      # Varredura de portas
./02_sql_injection.sh  # Teste de SQL Injection
./03_xss_test.sh       # Teste de XSS
./04_brute_force.sh    # Teste de Brute Force
./05_idor_test.sh      # Teste de IDOR
./06_path_traversal.sh # Teste de Path Traversal
./07_response_analysis.sh # Análise de resposta
```

### 3. Gerar relatório completo
```bash
./08_generate_report.sh
```

## Fluxo de Trabalho do Agente

```
1. Reconhecimento
   └─ ./01_port_scan.sh

2. Enumeração
   └─ ./07_response_analysis.sh

3. Exploração
   ├─ ./02_sql_injection.sh
   ├─ ./03_xss_test.sh
   ├─ ./04_brute_force.sh
   ├─ ./05_idor_test.sh
   └─ ./06_path_traversal.sh

4. Documentação
   └─ ./08_generate_report.sh
```

## Credenciais de Teste
- **Usuário:** attacker_001
- **Senha:** test123

## Alvos
- **App:** http://localhost:8080
- **Banco:** localhost:5432
- **Redis:** localhost:6379

## Nota Importante
Este laboratório é para **testes autorizados** apenas.
Use com responsabilidade e apenas em ambientes de teste.
