# Configuração do MobCrypt com Orbot

## Pré-requisitos
- Android 8.0+ (API 26)
- [Orbot](https://play.google.com/store/apps/details?id=org.torproject.android) instalado

## Passo 1: Configurar o Orbot

1. **Abra o Orbot** no celular
2. **Toque nos 3 pontinhos** (menu) → **Settings**
3. Ative **"VPN Mode"** (Modo VPN)
4. Ative **"Allow Background"** (Permitir em segundo plano)
5. Anote a porta do proxy SOCKS5 (padrão: `9050`)
6. Deixe o Orbot rodando em background ao conectar

## Passo 2: Conectar ao Orbot

O Orbot expõe um proxy SOCKS5 em:
- **Host:** `127.0.0.1`
- **Porta:** `9050` (padrão)

O MobCrypt se conecta automaticamente a esse proxy para rotear o tráfego de autenticação via Tor.

## Passo 3: Instalar o MobCrypt

1. Faça o download do APK mais recente na seção [Releases](https://github.com/seu-usuario/MobCrypt/releases) ou faça o build local
2. No celular, vá em **Configurações → Segurança → Instalar apps desconhecidas**
3. Ative a instalação do gerenciador de arquivos
4. Abra o APK baixado e instale

## Passo 4: Primeira execução

1. **Abra o MobCrypt**
2. **Ative o toggle "VPN Segura"** — ele vai pedir permissão de VPN (confirme)
3. **Toque em "Escanear QR Code"** para escanear QR codes de autenticação
4. O app detecta automaticamente se é um QR de login e ativa a proteção Tor

## Permissões necessárias

| Permissão | Motivo |
|-----------|--------|
| Câmera | Escanear QR codes |
| VPN | Roteamento via Tor |
| Notificações | Status do serviço |
| Sobreposição | Overlay flutuante (opcional) |

## Verificar se está funcionando

1. Com o MobCrypt ativo, acesse [check.torproject.org](https://check.torproject.org) no navegador
2. Deve aparecer: *"Congratulations. This browser is configured to use Tor."*
3. No MobCrypt, o status muda para **"Protegido via Tor"**

## Solução de problemas

**"Não consigo ativar a VPN"**
- Vá em Configurações do Android → VPN → Remova outras VPNs
- O MobCrypt precisa ser a única VPN ativa

**"QR Code não é detectado"**
- Certifique-se de que o Orbot está rodando
- Verifique se o QR realmente contém uma URL de autenticação

**"Orbot não está disponível"**
- Instale pelo Google Play ou F-Droid
- Após instalar, abra o Orbot pelo menos uma vez antes de usar o MobCrypt
