# Instalação do Arch Linux para Ambiente Ravena

## Opção 1: VirtualBox (Recomendado para teste)

### 1. Baixar Arch Linux ISO
- https://archlinux.org/download/
- Escolha: `archlinux-2026.08.01-x86_64.iso`

### 2. Criar VM no VirtualBox
```
Nome: Ravena-Arch
Tipo: Linux
Versão: Arch Linux (64-bit)
RAM: 4096 MB (mínimo 2048)
HD: 40 GB (virtual, tipo VDI)
```

### 3. Configurar VM
- Sistema → Processador: 2+ CPUs
- Rede → Adaptador 1: NAT (para internet)
- Estoque → ISO: selecionar o archlinux-*.iso

### 4. Boot e Instalação
Inicie a VM e siga as instruções abaixo.

---

## Opção 2: Instalação Bare Metal (Computador Físico)

### Pré-requisitos
- Pendrive 8GB+
- Outro computador para baixar o ISO
- Software Etcher ou Rufus para gravar

---

## Guia de Instalação do Arch Linux

Após bootar no ISO, execute os seguintes comandos:

### 1. Conectar à Internet
```bash
# Verificar se a rede está ativa
ip link
ping -c 3 archlinux.org

# Se usar WiFi:
iwctl station wlan0 connect "NOME_DA_REDE"
# Digitar senha quando solicitado

# Se usar cabo Ethernet (geralmente já funciona)
```

### 2. Atualizar relógio
```bash
timedatectl set-ntp true
```

### 3. Particionar o Disco
```bash
# Listar discos
lsblk

# Particionar (substitua /dev/sda pelo seu disco)
# Para uso simples com UEFI:
gdisk /dev/sda

# Dentro do gdisk:
# o        → criar nova tabela
# n        → nova partição (1) - 512MB -类型 EF00 (EFI)
# n        → nova partição (2) - resto - 类型 8300 (Linux)
# w        → salvar e sair

# Formatar
mkfs.fat -F32 /dev/sda1        # EFI
mkfs.ext4 /dev/sda2            # Root

# Montar
mount /dev/sda2 /mnt
mkdir -p /mnt/boot
mount /dev/sda1 /mnt/boot
```

### 4. Instalar Sistema Base
```bash
# Instalar pacotes essenciais
pacstrap /mnt base linux linux-firmware nano networkmanager sudo git base-devel python nodejs npm docker docker-compose nginx postgresql redis

# Gerar fstab
genfstab -U /mnt >> /mnt/etc/fstab

# Chroot
arch-chroot /mnt
```

### 5. Configurações Básicas
```bash
# Timezone
ln -sf /usr/share/timezone/America/Sao_Paulo /etc/localtime
hwclock --systohc

# Locale
echo "pt_BR.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen
echo "LANG=pt_BR.UTF-8" > /etc/locale.conf

# Hostname
echo "ravena-sandbox" > /etc/hostname

# Senha root
passwd
# Digite uma senha (ex: ravena123)

# Criar usuário
useradd -m -G wheel -s /bin/bash ravena
passwd ravena
# Digite senha para o usuário ravena
```

### 6. Configurar sudo
```bash
EDITOR=nano visudo
# Descomentar: %wheel ALL=(ALL) ALL
```

### 7. Instalar Bootloader (UEFI)
```bash
pacman -S --noconfirm efibootmgr
bootctl --path=/boot install
```

### 8. Habilitar Serviços
```bash
systemctl enable NetworkManager
systemctl enable docker
systemctl enable postgresql
systemctl enable redis
systemctl enable nginx
```

### 9. Sair e Reiniciar
```bash
exit
umount -R /mnt
reboot
```

---

## Após o Primeiro Boot

### 1. Login
```bash
# Login como root ou usuário ravena
# Conectar à internet (se WiFi):
nmcli device wifi connect "NOME_DA_REDE" password "SENHA"

# Verificar internet
ping -c 3 archlinux.org
```

### 2. Instalar Archiso (para compilar ISO)
```bash
sudo pacman -S --noconfirm archiso
```

### 3. Clonar Projeto Ravena
```bash
# Copiar os arquivos do projeto para o Arch Linux
# Opção A: Usar pendrive
# Opção B: SCP/SFTP
# Opção C: Git

# Exemplo com pendrive:
sudo mount /dev/sdb1 /mnt/usb
cp -r /mnt/usb/ravena-archiso /opt/
cd /opt/ravena-archiso
```

### 4. Compilar o ISO
```bash
cd /opt/ravena-archiso/archiso/configs/ravena

# Copiar perfil para /archiso/configs/
sudo cp -r . /usr/share/archiso/configs/ravena/

# OU compilar diretamente
sudo mkarchiso -v -w /tmp/archiso-work -C /usr/share/pacman.conf -D archiso -o /opt/ravena-archiso/out /usr/share/archiso/configs/ravena/
```

### 5. Testar ISO (QEMU)
```bash
sudo pacman -S --noconfirm qemu-full
./scripts/test_iso.sh
```

### 6. Gravar em Pendrive
```bash
# Identificar pendrive (CUIDADO para não errar o disco!)
lsblk

# Gravar (substitua /dev/sdX pelo pendrive correto)
sudo dd if=/opt/ravena-archiso/out/archlinux-*.iso of=/dev/sdX bs=4M status=progress
sync
```

---

## Alternativa: Instalação Automática

Execute o script `setup_ravena_env.sh` no Arch Linux já instalado:

```bash
cd /opt/ravena-archiso
chmod +x scripts/setup_ravena_env.sh
sudo ./scripts/setup_ravena_env.sh
```

---

## Solução de Problemas

### Sem internet
```bash
dhcpcd
# OU
systemctl start dhcpcd@eth0
```

### Pacman trava
```bash
rm /var/lib/pacman/db.lck
sudo pacman -Syyu
```

### Boot não aparece
```bash
# Reinstalar bootloader
bootctl --path=/boot install
```
