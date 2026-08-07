# ============================================
# RAVENA ARCHISO
# Arch Linux Personalizado com Ravena
# ============================================

## Visão Geral

Este projeto cria uma **ISO personalizada do Arch Linux** com a **Ravena Security Sandbox** pré-instalada. Ao bootar pelo pendrive, a Ravena já está rodando na RAM, pronta para testes de segurança.

```
Pendrive com ISO → Boot → Ravena já rodando na RAM
```

## Características

- **Sistema mínimo**: Apenas o necessário para rodar a Ravena
- **Boot rápido**: Sistema carrega na RAM em segundos
- **Proteção de RAM**: Monitoramento e proteção contra estouro
- **Pronto para uso**: A Ravena já inicia automaticamente
- **Migração fácil**: Script para migrar para Oracle Cloud

## Estrutura do Projeto

```
ravena-archiso/
├── archiso/
│   └── configs/
│       └── ravena/
│           ├── profiledef.sh           # Definição do perfil
│           ├── packages.x86_64         # Pacotes instalados
│           └── airootfs/
│               └── root/
│                   ├── install_ravena.sh    # Instalação
│                   └── auto_start.sh       # Boot automático
├── scripts/
│   ├── build_iso.sh                    # Compilar ISO
│   ├── test_iso.sh                     # Testar em VM
│   └── flash_iso.sh                    # Gravar no pendrive
└── README.md
```

## Pré-requisitos

### Para compilar a ISO:
- Arch Linux (ou derivatives)
- 10GB de espaço livre
- Conexão com internet

### Para usar a ISO:
- Pendrive de 4GB+
- PC com UEFI ou Legacy BIOS
- 2GB de RAM mínimo

## Instalação

### 1. Compilar a ISO

```bash
# No Arch Linux
cd ravena-archiso
chmod +x scripts/build_iso.sh
./scripts/build_iso.sh
```

### 2. Testar em VM (Opcional)

```bash
chmod +x scripts/test_iso.sh
./scripts/test_iso.sh
```

### 3. Gravar no Pendrive

```bash
# Como root
chmod +x scripts/flash_iso.sh
sudo ./flash_iso.sh
```

## Uso

### Bootar pelo Pendrive

1. Insira o pendrive no PC
2. Reinicie o PC
3. Aperte **F12** para selecionar boot
4. Selecione o pendrive
5. Aguarde o sistema inicializar
6. A Ravena estará rodando em **http://localhost:8080**

### Comandos Disponíveis

Após o boot, os seguintes comandos estão disponíveis:

```bash
# Iniciar a Ravena
ravena-start

# Parar a Ravena
ravena-stop

# Ver status
ravena-status

# Ver logs
ravena-logs

# Monitorar RAM
ram-monitor

# Configurar proteção de RAM
ram-protect

# Migrar para Oracle Cloud
migrate-cloud
```

## Proteção de RAM

O sistema inclui proteção contra estouro de memória:

### Limites Configurados:
- **Limite máximo de RAM**: 80%
- **Intervalo de verificação**: 5 segundos
- **Ação automática**: Limpa cache e mata processos

### Monitorar RAM:

```bash
# Ver status atual
ram-monitor status

# Ver logs
ram-monitor log

# Ver alertas
ram-monitor alerts
```

### Configurar Proteção:

```bash
# Configurar swappiness
ram-protect configure

# Limpar cache manualmente
ram-protect clear

# Ver status
ram-protect status
```

## Migração para Oracle Cloud

Quando tiver um servidor dedicado no Oracle Cloud:

### 1. Configurar Variáveis de Ambiente

```bash
export ORACLE_CLOUD_IP="seu-ip-aqui"
export ORACLE_CLOUD_USER="ubuntu"
export ORACLE_CLOUD_KEY="~/.ssh/id_rsa"
```

### 2. Criar Backup

```bash
migrate-cloud backup
```

### 3. Migrar

```bash
migrate-cloud migrate
```

### 4. Verificar Status

```bash
migrate-cloud status
```

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                  PENDRIVE / ISO                      │
├─────────────────────────────────────────────────────┤
│  Arch Linux Mínimo                                   │
│  ├── Kernel Linux                                    │
│  ├── Systemd                                         │
│  ├── Docker                                          │
│  ├── Python + Dependências                           │
│  └── Ravena Security Sandbox                         │
│      ├── App (Flask)                                 │
│      ├── Skills de Segurança                         │
│      ├── Scripts de Monitoramento                    │
│      └── Scripts de Proteção de RAM                  │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                    BOOT (RAM)                        │
├─────────────────────────────────────────────────────┤
│  1. Sistema carrega na RAM                           │
│  2. Docker inicia automaticamente                    │
│  3. Ravena inicia automaticamente                    │
│  4. Monitoramento de RAM ativo                       │
│  5. Pronto para uso em http://localhost:8080         │
└─────────────────────────────────────────────────────┘
```

## Serviços SystemD

O sistema cria os seguintes serviços:

| Serviço | Descrição |
|---------|-----------|
| `ravena.service` | Aplicação principal |
| `ravena-ram-monitor.service` | Monitoramento de RAM |
| `ravena-ram-protector.service` | Proteção de RAM |

### Gerenciar Serviços:

```bash
# Ver status
systemctl status ravena

# Iniciar
sudo systemctl start ravena

# Parar
sudo systemctl stop ravena

# Habilitar no boot
sudo systemctl enable ravena
```

## Solução de Problemas

### ISO não boota

1. Verifique se o pendrive está no modo correto (UEFI/Legacy)
2. Tente regravar a ISO
3. Verifique se o BIOS está configurado para boot externo

### Ravena não inicia

```bash
# Ver logs
journalctl -u ravena

# Reiniciar serviço
sudo systemctl restart ravena
```

### RAM esgotando

```bash
# Ver status da RAM
ram-monitor status

# Limpar cache
ram-protect clear

# Aumentar limite (edite o script)
sudo nano /opt/ravena/scripts/ram_monitor.sh
```

## Configurações

### Editar Limites de RAM

Edite `/opt/ravena/scripts/ram_monitor.sh`:

```bash
MAX_RAM_PERCENT=80          # Limite máximo de RAM (%)
CHECK_INTERVAL=5            # Intervalo de verificação (segundos)
```

### Editar Portas

Edite `/opt/ravena/app/app.py`:

```python
app.run(host='0.0.0.0', port=8080, debug=True)
```

## Licença

Este projeto é para uso educacional e testes de segurança autorizados.

## Autor

Ravena Security Lab
