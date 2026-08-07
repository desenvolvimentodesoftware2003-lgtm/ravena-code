# Ravena Security Sandbox - Instruções de Compilação

## Visão Geral

Este projeto compila uma ISO personalizada do Arch Linux com o **Ravena Security Sandbox** pré-instalado. A ISO contém:

- Sistema operacional Arch Linux com hardening de segurança
- Desktop estilo eDEX-UI com Terra 3D
- Interface web estilo Manus AI (tema roxo e preto)
- Criptografia pós-quântica (CRYSTALS-Kyber, Dilithium, FALCON, SPHINCS+)
- TLS 1.3 exclusivamente
- Docker com todos os serviços (PostgreSQL, Redis, Nginx, etc.)
- Ferramentas de pentest e monitoramento

---

## Pré-requisitos

### Sistema Necessário

- **Arch Linux** (ou derivado como Manjaro, EndeavourOS)
- **Mínimo 4GB de RAM** (recomendado 8GB)
- **Mínimo 20GB de espaço livre** em disco
- **Acesso root** (sudo)

### Alternativa: VM

Se não tiver Arch Linux, use uma VM:

```bash
# Opção 1: VirtualBox
# Baixe Arch Linux de: https://archlinux.org/download/

# Opção 2: Docker (mais simples)
docker run -it -v $(pwd):/project archlinux:latest /bin/bash
```

---

## Passo a Passo

### 1. Preparar Ambiente

```bash
# Navegar até o diretório de scripts
cd ravena-archiso/scripts/

# Tornar scripts executáveis
chmod +x *.sh

# Preparar ambiente (instala dependências)
sudo ./build_env.sh
```

### 2. Gerar Senhas

```bash
# Gera senhas seguras para todos os serviços
./generate_passwords.sh
```

As senhas serão salvas em `.env.passwords` (não commit este arquivo!).

### 3. Compilar a ISO

```bash
# Compilação normal (recomendada)
sudo ./build_iso.sh

# Ou compilação rápida (ISO maior)
sudo ./build_iso.sh --fast

# Ou limpar e recompilar
sudo ./build_iso.sh --clean
```

**Tempo estimado:** 15-30 minutos dependendo do hardware.

### 4. Verificar Resultado

Após a compilação, o output estará em:

```
ravena-archiso/output/
├── ravena-archlinux-YYYY.MM.DD.iso
└── ravena-archlinux-YYYY.MM.DD.iso.sha256
```

---

## Gravar no Pendrive

### Opção 1: Linux (dd)

```bash
# Identificar o pendrive (CUIDADO para não errar o dispositivo!)
lsblk

# Gravar (substitua /dev/sdX pelo pendrive correto!)
sudo dd if=output/ravena-archlinux-*.iso of=/dev/sdX bs=4M status=progress
sync
```

### Opção 2: Windows (Etcher/Rufus)

1. Baixe [Etcher](https://www.balena.io/etcher/) ou [Rufus](https://rufus.ie/)
2. Selecione a ISO
3. Selecione o pendrive
4. Clique em "Flash!"

---

## Instalar no Computador

### 1. Boot pelo Pendrive

1. Reinicie o computador
2. Pressione **F12** (ou F2/Del) para acessar o boot menu
3. Selecione o pendrive
4. Aguarde o sistema carregar

### 2. A Ravena Já Estará Rodando!

- **Desktop:** Interface eDEX-UI com terminal e Terra 3D
- **Web:** Acesse `https://localhost` em outro dispositivo
- **Sem senha:** O desktop não pede senha (uso pessoal)
- **Web com senha:** Interface web tem autenticação

---

## Senhas Padrão

| Serviço | Usuário | Senha |
|---------|---------|-------|
| Sistema | ravena | (sem senha) |
| Web | admin | ravena2024 |
| Web | user | user2024 |
| PostgreSQL | ravena | (gerada em .env.passwords) |
| Redis | - | (gerada em .env.passwords) |
| Grafana | admin | (gerada em .env.passwords) |

**IMPORTANTE:** As senhas de serviços são geradas aleatoriamente. Consulte o arquivo `.env.passwords`.

---

## Estrutura do Projeto

```
ravena-archiso/
├── archiso/
│   └── configs/
│       └── ravena/
│           ├── profiledef.sh          # Definições da ISO
│           ├── packages.x86_64        # Pacotes instalados
│           ├── airootfs/
│           │   └── root/
│           │       ├── install_ravena.sh
│           │       ├── post_quantum_crypto.sh
│           │       ├── nginx_tls.sh
│           │       └── ...
│           └── boot/
│               └── grub/
│                   └── grub.cfg       # Configuração de boot
├── scripts/
│   ├── build_env.sh                   # Preparar ambiente
│   ├── build_iso.sh                   # Compilar ISO
│   ├── generate_passwords.sh          # Gerar senhas
│   ├── flash_iso.sh                   # Gravar no pendrive
│   └── install_archlinux.sh           # Instalar Arch
├── output/                            # ISO compilada (gerado)
└── README.md
```

---

## Solução de Problemas

### "mkarchiso não encontrado"

```bash
sudo pacman -S archiso
```

### "Erro de permissão"

```bash
# Execute como root
sudo ./build_iso.sh
```

### "ISO não gera"

Verifique os logs de erro. Possíveis causas:
- Espaço insuficiente em disco
- Pacotes faltando
- Conexão com internet (para baixar pacotes)

### "Pendrive não boota"

1. Verifique se a ISO foi gravada corretamente
2. Tente outro pendrive
3. No BIOS, desative "Secure Boot"
4. No BIOS, habilite "Legacy Boot" ou "CSM"

---

## Comandos Úteis

```bash
# Verificar tamanho da ISO
ls -lh output/*.iso

# Verificar integridade
sha256sum -c output/*.iso.sha256

# Limpar build anterior
sudo ./build_iso.sh --clean

# Compilar rápido (para testes)
sudo ./build_iso.sh --fast
```

---

## Suporte

Em caso de problemas, verifique:
1. Se está no Arch Linux
2. Se tem acesso root
3. Se as dependências estão instaladas
4. Se tem espaço suficiente em disco

---

**Feito com ❤️ pela Ravena Security Lab**
