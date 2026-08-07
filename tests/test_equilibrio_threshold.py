"""
RAVENA AI — Teste de Equilibrio do brutality_threshold
======================================================
Varredura sistematica com dados CoinGecko REAIS para encontrar
o ponto de convergencia natural do threshold.

Uso: python tests/test_equilibrio_threshold.py
"""
import os, sys, time, json, importlib.util, math
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
os.chdir(BASE)

# ── Carregar modulos ──
def _carregar(nome, path):
    spec = importlib.util.spec_from_file_location(nome, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nome] = mod
    spec.loader.exec_module(mod)
    return mod

_cl_mod = _carregar("cl_mod", BASE / "src/clarividencia.py")
_sa_mod = _carregar("sa_mod", BASE / "src/orchestration/search_agent_v3.2.6.py")
_sb_mod = _carregar("sb_mod", BASE / "src/trading/signal_bridge_v3.2.6.py")

process_signal = _sb_mod.process_signal
SearchAgent = _sa_mod.SearchAgent

# ── Lista de ativos ──
ativos = [s for s in _cl_mod._COINGECKO_IDS.keys() if s != "DEFAULT"]
simbolos = [f"{a}USDT" for a in ativos]
N = len(simbolos)

# ── Fase 1: Coleta de dados reais ──
print(f"Coletando dados CoinGecko reais para {N} ativos...")
print()

resultados_brutos = []
for i, (simb, ativo) in enumerate(zip(simbolos, ativos), 1):
    agente = SearchAgent()
    trade_data = agente.preparar_para_trading(simb, tech_confidence=0.70)
    pkg = process_signal(trade_data, current_balance=1000.0)

    sim = pkg.get("simulacao_60_agentes") or {}
    prob = pkg.get("success_probability", 0)
    status = pkg.get("status", "N/A")
    sent = pkg.get("sentiment_score", 0)
    brute = sim.get("score_brutalidade", 0)
    vit = sim.get("taxa_vitoria", 0)
    passou = sim.get("passou_filtro", False)

    resultados_brutos.append({
        "simbolo": simb,
        "ativo": ativo,
        "prob_hibrida": round(prob, 4),
        "brutalidade": round(brute, 4),
        "taxa_vitoria": round(vit, 4),
        "sentimento": round(sent, 2),
        "status": status,
        "passou_filtro_60ag": passou,
        "bloqueado_gate": prob == 0 and brute == 0,
    })

    flag = ""
    if resultados_brutos[-1]["bloqueado_gate"]:
        flag = " [BLOQUEADO no gate AGGRESSIVE]"
    print(f"  {i:2d}. {simb:>9s}  prob={prob:.4f}  brute={brute:.4f}  {status:8s}{flag}")

# ── Fase 2: Separar ativos que chegaram ao filtro ──
chegaram = [r for r in resultados_brutos if not r["bloqueado_gate"]]
bloqueados = [r for r in resultados_brutos if r["bloqueado_gate"]]
M = len(chegaram)
B = len(bloqueados)

print(f"\n  Ativos que chegaram ao filtro 60 agentes: {M}/{N}")
print(f"  Ativos bloqueados pelo suitability gate:  {B}/{N}")

if M == 0:
    print("\n  ERRO: Nenhum ativo chegou ao filtro. Impossivel calcular threshold.")
    print("  Causa provavel: suitability_dynamic_gate (AGGRESSIVE) bloqueando tudo.")
    print("  Solucao: revisar logica do gate ou usar modo CONSERVATIVE/MODERATE.")
    sys.exit(1)

chegaram.sort(key=lambda r: r["prob_hibrida"], reverse=True)

# ── Fase 3: Distribuicao estatistica ──
brutes = [r["brutalidade"] for r in chegaram]
probs = [r["prob_hibrida"] for r in chegaram]

def estat(vals):
    v = sorted(vals)
    n = len(v)
    return {
        "min": round(min(v), 4),
        "max": round(max(v), 4),
        "media": round(sum(v) / n, 4),
        "mediana": round(v[n // 2], 4),
        "p25": round(v[n // 4], 4),
        "p75": round(v[3 * n // 4], 4),
        "p90": round(v[int(0.9 * n)], 4),
        "p95": round(v[int(0.95 * n)], 4),
    }

est_brute = estat(brutes)
est_prob = estat(probs)

print(f"\n  Distribuicao de BRUTALIDADE (entre os que chegaram):")
for k, v in est_brute.items():
    print(f"    {k}: {v}")
print(f"\n  Distribuicao de PROB_HIBRIDA:")
for k, v in est_prob.items():
    print(f"    {k}: {v}")

# ── Fase 4: Varredura de thresholds ──
THRESHOLD_MIN = 0.30
THRESHOLD_MAX = 0.80
THRESHOLD_STEP = 0.01

varredura = []
for t in range(int(THRESHOLD_MIN * 100), int(THRESHOLD_MAX * 100) + 1, int(THRESHOLD_STEP * 100)):
    th = round(t / 100, 2)
    aprovados = [r for r in chegaram if r["prob_hibrida"] >= th]
    varredura.append({
        "threshold": th,
        "aprovados": len(aprovados),
        "pct": round(len(aprovados) / M * 100, 1) if M else 0,
        "media_prob": round(sum(r["prob_hibrida"] for r in aprovados) / len(aprovados), 4) if aprovados else 0,
        "media_brute": round(sum(r["brutalidade"] for r in aprovados) / len(aprovados), 4) if aprovados else 0,
    })

# ── Fase 5: Encontrar o knee point (joelho da curva) ──
# Metodo: maxima distancia perpendicular da corda (ponto inicial ao final)
def encontrar_knee(varredura):
    pts = [(v["threshold"], v["aprovados"]) for v in varredura]
    if len(pts) < 3:
        return None

    x1, y1 = pts[0]
    x2, y2 = pts[-1]

    # Comprimento da corda
    chord_len = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    if chord_len == 0:
        return None

    max_dist = -1
    knee_idx = 0
    for i in range(1, len(pts) - 1):
        x0, y0 = pts[i]
        # Distancia perpendicular do ponto (x0,y0) a reta (x1,y1)-(x2,y2)
        dist = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1) / chord_len
        if dist > max_dist:
            max_dist = dist
            knee_idx = i

    return {
        "threshold": pts[knee_idx][0],
        "aprovados": pts[knee_idx][1],
        "indice": knee_idx,
        "distancia": round(max_dist, 4),
    }

knee = encontrar_knee(varredura)

# ── Fase 6: Recomendacao ──
if knee:
    th_recomendado = knee["threshold"]
else:
    # Fallback: percentil 75 da prob_hibrida
    th_recomendado = est_prob["p75"]

# Ajuste fino: o threshold deve ser >= mediana de brute
th_minimo = est_brute["mediana"]
if th_recomendado < th_minimo:
    th_recomendado = round(th_minimo + 0.02, 2)

# Nao pode ser menor que 0.30 nem maior que 0.80
th_recomendado = max(0.30, min(0.80, th_recomendado))

# Simular quantos seriam aprovados com o threshold recomendado
aprov_final = [r for r in chegaram if r["prob_hibrida"] >= th_recomendado]
reprov_final = [r for r in chegaram if r["prob_hibrida"] < th_recomendado]

print(f"\n{'='*60}")
print(f"  RESULTADO DA ANALISE")
print(f"{'='*60}")
print(f"  Knee point identificado: threshold={knee['threshold'] if knee else 'N/A'}, "
      f"aprovados={knee['aprovados'] if knee else 'N/A'}")
print(f"  Threshold recomendado:   {th_recomendado:.2f}")
print(f"  Aprovados com este threshold: {len(aprov_final)}/{M} (dos que chegaram ao filtro)")
print(f"  Aprovados no total:           {len(aprov_final)}/{N} (de todos os ativos)")

if aprov_final:
    print(f"\n  ATIVOS QUE SERIAM APROVADOS (threshold={th_recomendado:.2f}):")
    for r in aprov_final:
        print(f"    {r['simbolo']:>9s}  prob={r['prob_hibrida']:.4f}  brute={r['brutalidade']:.4f}")

if reprov_final:
    print(f"\n  ATIVOS REPROVADOS (threshold={th_recomendado:.2f}):")
    for r in reprov_final:
        print(f"    {r['simbolo']:>9s}  prob={r['prob_hibrida']:.4f}  brute={r['brutalidade']:.4f}")

if bloqueados:
    print(f"\n  BLOQUEADOS ANTES DO FILTRO (suitability gate):")
    for r in bloqueados:
        print(f"    {r['simbolo']:>9s}  sentimento={r['sentimento']}")
    print(f"\n  ATENCAO: {B} ativos foram barrados pelo suitability_dynamic_gate")
    print(f"  antes mesmo de chegarem ao filtro de 60 agentes.")
    print(f"  Se desejar que eles participem da analise, considere:")
    print(f"  - Reduzir o limite de sentimento no suitability_dynamic_gate")
    print(f"  - Usar modo MODERATE ou CONSERVATIVE")

# ── Fase 7: Salvar output JSON ──
output = {
    "metadados": {
        "data": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_ativos": N,
        "chegaram_ao_filtro": M,
        "bloqueados_gate": B,
        "tech_confidence": 0.70,
        "balance": 1000.0,
        "suitability_mode": "AGGRESSIVE",
    },
    "distribuicao_brutalidade": est_brute,
    "distribuicao_prob_hibrida": est_prob,
    "knee_point": knee,
    "threshold_recomendado": th_recomendado,
    "aprovados_com_recomendado": [r["simbolo"] for r in aprov_final],
    "reprovados_com_recomendado": [r["simbolo"] for r in reprov_final],
    "bloqueados_gate_lista": [r["simbolo"] for r in bloqueados],
    "varredura": varredura,
    "resultados_detalhados": resultados_brutos,
}

output_path = BASE / "tests" / "test_equilibrio_threshold_output.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n  Output salvo em: tests/test_equilibrio_threshold_output.json")
print(f"{'='*60}")
