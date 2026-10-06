"""Gera .env.example a partir do REGISTRO do SecretsManager.

Nao listas chaves na mao: o arquivo sai do dicionario de
`secrets_manager.py`, entao nao diverge quando um segredo novo e
adicionado. As variaveis de configuracao (host, porta, flag) vem de um
scan por `os.getenv` no repo, porque o registro so cobre segredo.

Regra dura: NENHUM valor real entra no arquivo. Vazio e placeholder.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(r"C:\Users\DELL\dev\ravena-aim")
SECRETS_PY = REPO / "src/core/secrets_manager.py"

# variaveis de configuracao ja vistas no scan, com o que va no placeholder.
# Secret NAO entra aqui: segredo vai no bloco de credenciais.
CONFIG: dict[str, tuple[str, str]] = {
    "LLM_MAX_NEW_TOKENS": ("treino", "teto de tokens por resposta"),
    "LLM_PORT": ("llm", "porta do servico local de LLM"),
    "USE_LOCAL_LLM": ("llm", "true para usar o modelo local"),
    "BYBIT_ENV": ("trading/bybit_connector", "mainnet | testnet"),
    "BYBIT_MODE": ("trading/bybit_connector", "live | paper"),
    "CLARIVIDENCIA_MOCK_MODE": ("utils", "true para mockar (nunca em producao)"),
    "FALLBACK_TO_EXTERNAL": ("global", "true para cair no provedor externo"),
    "DISPLAY": ("sandbox", "display X11, se rodar interface grafica"),
    "HF_HUB_DISABLE_PROGRESS_BARS": ("global", "true silencia barra de progresso"),
    "TRANSFORMERS_NO_ADVISORY_WARNINGS": ("global", "true silencia aviso do transformers"),
    "API_HOST": ("api", "host do backend"),
    "API_PORT": ("api", "porta do backend"),
    "RAVENA_WEB_HOST": ("web", "host do painel"),
    "RAVENA_WEB_PORT": ("web", "porta do painel"),
    "DB_HOST": ("db", "host do Postgres"),
    "DB_PORT": ("db", "porta do Postgres"),
    "DB_NAME": ("db", "nome do banco"),
    "DB_USER": ("db", "usuario do banco"),
    "DB_PASS": ("db", "senha do banco"),
    "DATABASE_URL": ("db", "postgresql://user:pass@host:5432/db"),
    "REDIS_URL": ("cache", "redis://host:6379/0"),
    "OCI_VAULT_ID": ("oci", "id do cofre OCI"),
    "SCIPHI_API_BASE": ("agentsearch", "base URL do AgentSearch"),
    "RAVENA_TLS_CERT": ("tls", "caminho do certificado"),
    "RAVENA_TLS_KEY": ("tls", "caminho da chave"),
}

# `RAVENA_ENV`, `LLM_MODE`, `RAVENA_SOBERANIA` e `RAVENA_CONFIG_PATH`
# aparecem no registro como segredo de severidade LOW, mas sao flag de
# configuracao, nao credencial. O bloco de credenciais ja as emite, entao
# sao removidas daqui para nao sair duplicadas no .env.example — em .env
# a ultima atribuicao vence, e um arquivo com a mesma chave duas vezes
# e um arquivo que ninguem consegue ler direito.

# segredos lidos no repo mas fora do registro: entram no bloco de credenciais
EXTRA_SECRET = {
    "JWT_SECRET": ("MEDIUM", "api", "segredo de assinatura de token"),
    "CRYPTOPANIC_API_TOKEN": ("MEDIUM", "trading", "token do CryptoPanic"),
    "RAVENA_SECRET_KEY": ("CRITICAL", "core/omega", "chave mestra do sistema"),
}


def registro(secrets_py: Path) -> dict[str, dict]:
    tree = ast.parse(secrets_py.read_bytes().decode("utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        nomes = [
            k.value
            for k in node.keys
            if isinstance(k, ast.Constant) and isinstance(k.value, str) and k.value.isupper() and "_" in k.value
        ]
        if len(nomes) != len(node.keys) or len(nomes) < 5:
            continue
        out = {}
        for i, k in enumerate(node.keys):
            meta: dict = {}
            v = node.values[i]
            if isinstance(v, ast.Dict):
                for mk, mv in zip(v.keys, v.values):
                    if isinstance(mk, ast.Constant) and isinstance(mv, ast.Constant):
                        meta[mk.value] = mv.value
            out[k.value] = meta
        return out
    raise SystemExit("registro de segredos nao encontrado")


def main() -> None:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO
    secrets_py = repo / "src/core/secrets_manager.py"
    if not secrets_py.exists():
        raise SystemExit(f"registro nao encontrado em {secrets_py}")
    reg = registro(secrets_py)
    # Se um nome estiver no registro E na lista de configuracao, ele e'
    # emitido uma vez so, no bloco de credenciais. Sem este filtro o
    # arquivo sai com a mesma chave duas vezes, e em .env a ultima
    # atribuicao vence — resultado silenciosamente errado.
    config = {k: v for k, v in CONFIG.items() if k not in reg}
    ordem = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    segredos = sorted(reg.items(), key=lambda kv: (ordem.get(kv[1].get("severity", "LOW"), 9), kv[0]))

    segreDos = segredos
    L: list[str] = []
    a = L.append
    a("# ─────────────────────────────────────────────────────────────────")
    a("# Ravena — variaveis de ambiente")
    a("#")
    a("# Copie para .env e preencha.   cp .env.example .env")
    a("#")
    a("# O .env esta no .gitignore e NUNCA deve ser commitado. Este arquivo")
    a("# vai junto no git de proposito: e o contrato do que o sistema espera.")
    a("#")
    a("# As variaveis de credencial sao geradas a partir do registro de")
    a("# src/core/secrets_manager.py. Ao adicionar um segredo la, este")
    a("# arquivo precisa ser regerado:")
    a("#     python tools/gerar_env_example.py")
    a("#")
    a("# Nenhum valor real aqui: vazio e placeholder.")
    a("# ─────────────────────────────────────────────────────────────────")
    a("")
    a("# ═══════════════════════════════════════════════════════════════════")
    a("# CREDENCIAIS — preencha com o valor real")
    a("# ═══════════════════════════════════════════════════════════════════")
    a("#   CRITICAL  sistema nao sobe sem isso")
    a("#   HIGH      comeca a subir, mas trading e recusado")
    a("#   MEDIUM    opcional, liga funcionalidade")
    a("")

    for nome, meta in segredos:
        sev = meta.get("severity", "LOW")
        req = meta.get("required", False)
        mod = meta.get("module", "?")
        desc = (meta.get("description") or "").replace("\n", " ").strip()
        a(f"# [{sev}] {mod}" + ("" if req else "  (opcional)"))
        a(f"# {desc}")
        a(f"{nome}=")
        a("")

    extras = [(n, v) for n, v in EXTRA_SECRET.items() if n not in reg]
    if extras:
        a("# ── Segredos lidos no codigo, fora do registro ─────────────────")
        for nome, (sev, mod, desc) in sorted(extras, key=lambda x: ordem.get(x[1][0], 9)):
            a(f"# [{sev}] {mod}")
            a(f"# {desc}")
            a(f"{nome}=")
            a("")

    a("")
    a("# ═══════════════════════════════════════════════════════════════════")
    a("# CONFIGURACAO — nao e segredo, tem valor padrao")
    a("# ═══════════════════════════════════════════════════════════════════")
    for nome, (mod, placeholder) in sorted(config.items()):
        a(f"# {mod} — {placeholder.split(':')[0]}")
        a(f"{nome}=")
        a("")

    destino = repo / ".env.example"
    destino.write_bytes("\n".join(L).encode("utf-8"))
    print(
        f"{repo.name}/{destino.name}: {len(L)} linhas — "
        f"{len(segreDos)} credenciais do registro + "
        f"{len(EXTRA_SECRET)} extras + {len(config)} de configuracao"
    )


if __name__ == "__main__":
    main()
