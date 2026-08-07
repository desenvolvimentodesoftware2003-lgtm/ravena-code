# Ravena CODE

Código-fonte oficial do **Ravena OS** — remaster de Arch Linux para trading na B3, terminal-only.

## Componentes

| Módulo | Descrição |
|---|---|
| `ravena-archiso/` | Build system da ISO (build_iso.sh, flash_iso.sh, grub.cfg, airootfs, security maps) |
| `ravena-ai/` | Bots multi-plataforma (Discord/Telegram/WhatsApp) + Agent Orchestrator (141 testes) |
| `MobCrypt/` | Projeto Kotlin (Android + desktop) |
| `sandbox-ravena/` | Sandbox de segurança, monitoramento, nginx, web |
| `src/` | Núcleo do Ravena AIM (monitoramento, agentes) |
| `scripts/` | Scripts de build/teste (chroot LLM, airLLM Qwen, usbboot tests, provision BIOS) |
| `tools/` | Ferramentas (XiaomiFRPTool, etc.) |
| `tests/` | Suíte de testes |
| `config/` | Configurações (`config_v3.json`) |
| `deploy/` + `docker/` | Deploy e containers |

## Pipeline LLM local (airLLM)

1. Download dos shards safetensors (ex.: `Qwen3.6-27B`, 12 shards, ~55.6GB)
2. Conversão text-only via `scripts/bios/convert_qwen35_textonly.py`
3. Split por layer (airLLM) — carregamento incremental em RAM limitada
4. Inferência no chroot com binds obrigatórios (`/dev`, `/proc`)

**Validado:** Qwen3.5-4B convertido gerou texto real (80 tokens em ~1245s, cold cache).

## Desenvolvimento

```bash
pip install -e .
pytest tests/
python main.py
```
