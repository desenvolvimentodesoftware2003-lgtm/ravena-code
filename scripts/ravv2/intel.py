#!/usr/bin/env python3
# RAVENA INTEL - Monitor de noticias geopoliticas (WarWatch) p/ analise de mercado
# Uso:
#   intel                 - top 30 noticias (CRITICAL + HIGH), prioridade primeiro
#   intel top             - so CRITICAL (risco maximo)
#   intel regiao <nome>   - filtra por regiao (ex: Iran, Russia, Middle East, Asia)
#   intel tipo <tipo>     - filtra por tipo (Ground, Aerial, Naval, Cyber, Nuclear/Missile, Political...)
#   intel mercado         - filtra noticias com impacto em mercado (energia, petroleo, ouro, guerra, sancao...)
#   intel buscar <palavra>- busca por palavra-chave no titulo/resumo
#   intel 24h             - noticias das ultimas 24h
#   intel ao vivo         - modo monitor (atualiza a cada 3 min)
#   intel link <id>       - abre a noticia no navegador (w3m)
import sys, json, time, urllib.request, urllib.parse, re, os

API = "https://www.war-watch.com/api/articles"
TIMEOUT = 25

C = {
    "red": "\033[0;31m", "yel": "\033[0;33m", "grn": "\033[0;32m",
    "cyn": "\033[0;36m", "dim": "\033[2m", "bld": "\033[1m", "rst": "\033[0m",
}

SPAM_SOURCES = ("Clash Report",)
SPAM_PAT = re.compile(r"^(Trump|trump|clash report)[\s:]*$", re.I)

def fetch(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "RavenaOS/1.0 (trading-monitor)"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))

def time_ago(iso):
    try:
        import datetime
        t = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        d = datetime.datetime.now(datetime.timezone.utc) - t
        s = int(d.total_seconds())
        if s < 0: s = 0
        if s < 3600: return f"{s//60}m"
        if s < 86400: return f"{s//3600}h"
        return f"{s//86400}d"
    except Exception:
        return "?"

MARKET_KW = re.compile(r"\b(energy|oil|petro|gas|commodit|gold|dollar|sanction|tariff|war|missile|nuclear|naval|shipping|supply|market|stock|debt|inflation|export|import|trade|bank|rate|bond|barrel)\b", re.I)

def clean(articles, drop_spam=True):
    out = []
    for a in articles:
        src = (a.get("source") or "")
        title = (a.get("title") or "")
        if drop_spam and src in SPAM_SOURCES and SPAM_PAT.match(title):
            continue
        out.append(a)
    return out

def show(articles, link_mode=False, src=True):
    if not articles:
        print(f"{C['dim']}nenhuma noticia encontrada.{C['rst']}")
        return 0
    n = 0
    for a in articles:
        prio = (a.get("priority") or "LOW").upper()
        col = C["red"] if prio == "CRITICAL" else C["yel"] if prio == "HIGH" else C["grn"]
        tag = "CRITICAL" if prio == "CRITICAL" else "HIGH" if prio == "HIGH" else prio
        reg = a.get("region") or "?"
        typ = a.get("conflictType") or "?"
        ag = time_ago(a.get("publishedAt") or "")
        aid = (a.get("id") or "")[:8]
        if link_mode:
            print(f"[{aid}] {col}{tag:8}{C['rst']} {C['cyn']}{ag}{C['rst']} {C['bld']}{(a.get('title','') or '')[:110]}{C['rst']}")
            print(f"      {C['dim']}{a.get('url','')}{C['rst']}")
        else:
            print(f"[{aid}] {col}{tag:8}{C['rst']} {C['cyn']}{ag:<4}{C['rst']} {C['dim']}{reg:<12}{typ:<16}{C['rst']}")
            print(f"      {C['bld']}{(a.get('title','') or '')[:140]}{C['rst']}")
        if src:
            print(f"      {C['dim']}{a.get('source','')} | {(a.get('summary','') or '')[:120]}{C['rst']}")
        n += 1
    return n

def main():
    args = sys.argv[1:]
    cmd = args[0].lower() if args else ""
    params = {"limit": 50}

    if cmd in ("top", "critico"):
        params["priority"] = "CRITICAL"
        params["limit"] = 15
    elif cmd in ("regiao", "reg", "region"):
        if len(args) < 2:
            print("uso: intel regiao <nome>   (ex: Iran, Russia, Middle East, Asia)")
            sys.exit(1)
        params["region"] = " ".join(args[1:])
        params["limit"] = 25
    elif cmd in ("tipo", "type"):
        if len(args) < 2:
            print("uso: intel tipo <tipo>   (ex: Ground, Aerial, Naval, Cyber, Nuclear/Missile, Political, Insurgency)")
            sys.exit(1)
        params["conflictType"] = " ".join(args[1:])
        params["limit"] = 25
    elif cmd in ("mercado", "market"):
        params["limit"] = 80
    elif cmd in ("buscar", "search", "busca"):
        if len(args) < 2:
            print("uso: intel buscar <palavra>")
            sys.exit(1)
        params["limit"] = 80
        params["q"] = " ".join(args[1:])
    elif cmd in ("24h", "hoje"):
        params["limit"] = 80
        params["range"] = "24H"
    elif cmd in ("tudo", "raw"):
        params["limit"] = 50
    elif cmd in ("ao", "vivo", "live", "watch"):
        params["limit"] = 40
        try:
            while True:
                os.system("clear")
                print(f"{C['bld']}RAVENA INTEL - AO VIVO{C['rst']} ({time.strftime('%H:%M:%S')})  [Ctrl+C p/ sair]\n")
                try:
                    data = fetch(params)
                    arts = clean(data.get("articles", []), drop_spam=(cmd != "tudo"))
                    show(arts[:30], src=False)
                except Exception as e:
                    print(f"{C['red']}falha de conexao: {e}{C['rst']}")
                time.sleep(180)
        except KeyboardInterrupt:
            print("\nintel ao vivo encerrado")
            sys.exit(0)
    elif cmd in ("link", "abrir"):
        if len(args) < 2:
            print("uso: intel link <id>")
            sys.exit(1)
        params["limit"] = 50
        try:
            data = fetch(params)
            for a in data.get("articles", []):
                if (a.get("id") or "").startswith(args[1]):
                    url = a.get("url", "")
                    print(f"abrindo: {url}")
                    os.system(f'w3m "{url}"')
                    sys.exit(0)
            print("id nao encontrado")
        except Exception as e:
            print(f"erro: {e}")
        sys.exit(0)
    elif cmd in ("-h", "--help", "help", "ajuda"):
        print(__doc__)
        sys.exit(0)

    try:
        data = fetch(params)
    except Exception as e:
        print(f"{C['red']}ERRO ao consultar WarWatch: {e}{C['rst']}")
        sys.exit(1)

    arts = clean(data.get("articles", []))
    if cmd in ("mercado", "market"):
        arts = [a for a in arts if MARKET_KW.search(((a.get("title","") or "") + " " + (a.get("summary","") or ""))[:400])]
    elif cmd in ("buscar", "search", "busca"):
        kw = " ".join(args[1:]).lower()
        arts = [a for a in arts if kw in ((a.get("title","") or "") + " " + (a.get("summary","") or "")).lower()]

    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    arts.sort(key=lambda a: (order.get((a.get("priority") or "LOW").upper(), 9), a.get("publishedAt") or ""))

    title = "RAVENA INTEL - WarWatch"
    if cmd in ("top", "critico"): title += " [CRITICAL]"
    elif cmd in ("mercado", "market"): title += " [IMPACTO MERCADO]"
    elif cmd in ("24h", "hoje"): title += " [24H]"
    elif cmd in ("regiao", "reg", "region"): title += f" [REGIAO: {params.get('region')}]"
    elif cmd in ("tipo", "type"): title += f" [TIPO: {params.get('conflictType')}]"
    elif cmd in ("buscar", "search", "busca"): title += f" [BUSCA: {' '.join(args[1:])}]"
    print(f"{C['bld']}{title}{C['rst']}  ({time.strftime('%d/%m %H:%M')})\n")
    n = show(arts[:30], link_mode=True, src=True)
    print(f"\n{C['dim']}{n} noticias | intel link <id> p/ abrir | intel ao vivo | intel -h{C['rst']}")

if __name__ == "__main__":
    main()
