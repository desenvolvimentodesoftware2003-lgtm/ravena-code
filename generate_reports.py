"""
RAVENA AIM — Report Generator v3.2.6
====================================
Gera relatórios em Markdown (.md) e HTML (.html) a partir do JSON de health check.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def load_report():
    report_path = PROJECT_ROOT / "tests" / "health_check_report.json"
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_markdown(report):
    lines = []
    lines.append("# Ravena AIM — Health Check Report\n")
    lines.append(f"**Timestamp:** {report['timestamp']}  ")
    lines.append(f"**Version:** {report['version']}  ")
    lines.append(f"**Environment:** {report['environment']}  ")
    lines.append(f"**Verdict:** {report['verdict']}\n")
    lines.append("## Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total | {report['summary']['total']} |")
    lines.append(f"| ✅ Passed | {report['summary']['passed']} |")
    lines.append(f"| ⚠️ Warned | {report['summary']['warned']} |")
    lines.append(f"| ❌ Failed | {report['summary']['failed']} |")
    lines.append(f"| Time (s) | {report['summary']['time_seconds']} |")
    lines.append(f"| Health Score | {report['summary']['health_score']}% |\n")
    lines.append("## Module Results\n")
    lines.append("| # | Module | Status | Details | Time (ms) |")
    lines.append("|---|--------|--------|---------|-----------|")
    for i, r in enumerate(report["results"], 1):
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(r["status"], "❓")
        lines.append(f"| {i} | {r['module']} | {icon} {r['status']} | {r['details']} | {r['time_ms']} |")
    lines.append("\n---\n")
    lines.append(f"*Generated at {datetime.now().isoformat()}*")
    return "\n".join(lines)

def generate_html(report):
    md = generate_markdown(report)
    rows = ""
    for i, r in enumerate(report["results"], 1):
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(r["status"], "❓")
        color = {"PASS": "green", "WARN": "orange", "FAIL": "red"}.get(r["status"], "gray")
        rows += f"<tr><td>{i}</td><td>{r['module']}</td><td style='color:{color}'>{icon} {r['status']}</td><td>{r['details']}</td><td>{r['time_ms']}</td></tr>\n"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ravena AIM — Health Check Report</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 40px auto; padding: 0 20px; background: #0d1117; color: #c9d1d9; }}
h1, h2, h3 {{ color: #58a6ff; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
th, td {{ border: 1px solid #30363d; padding: 8px 12px; text-align: left; }}
th {{ background: #161b22; color: #8b949e; text-transform: uppercase; font-size: 12px; }}
tr:nth-child(even) {{ background: #161b22; }}
tr:hover {{ background: #1c2128; }}
.summary {{ display: flex; gap: 20px; flex-wrap: wrap; }}
.card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; min-width: 120px; text-align: center; }}
.card .value {{ font-size: 28px; font-weight: bold; }}
.card .label {{ font-size: 12px; color: #8b949e; }}
.green {{ color: #3fb950 !important; }}
.orange {{ color: #d29922 !important; }}
.red {{ color: #f85149 !important; }}
.verdict {{ font-size: 24px; text-align: center; padding: 20px; border-radius: 8px; }}
.verdict.healthy {{ background: #3fb95022; color: #3fb950; border: 1px solid #3fb950; }}
.verdict.partial {{ background: #d2992222; color: #d29922; border: 1px solid #d29922; }}
.verdict.unhealthy {{ background: #f8514922; color: #f85149; border: 1px solid #f85149; }}
</style>
</head>
<body>
<h1>Ravena AIM — Health Check Report</h1>
<p><strong>Timestamp:</strong> {report['timestamp']} | <strong>Version:</strong> {report['version']} | <strong>Environment:</strong> {report['environment']}</p>
<div class="verdict {'healthy' if report['verdict'] == 'HEALTHY' else 'partial' if report['verdict'] == 'PARTIAL' else 'unhealthy'}">{report['verdict']}</div>
<h2>Summary</h2>
<div class="summary">
<div class="card"><div class="value">{report['summary']['total']}</div><div class="label">Total</div></div>
<div class="card"><div class="value green">{report['summary']['passed']}</div><div class="label">Passed</div></div>
<div class="card"><div class="value orange">{report['summary']['warned']}</div><div class="label">Warned</div></div>
<div class="card"><div class="value red">{report['summary']['failed']}</div><div class="label">Failed</div></div>
<div class="card"><div class="value">{report['summary']['time_seconds']}s</div><div class="label">Time</div></div>
<div class="card"><div class="value green">{report['summary']['health_score']}%</div><div class="label">Score</div></div>
</div>
<h2>Module Results</h2>
<table>
<thead><tr><th>#</th><th>Module</th><th>Status</th><th>Details</th><th>Time (ms)</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
<hr>
<p><em>Generated at {datetime.now().isoformat()}</em></p>
</body>
</html>"""
    return html

if __name__ == "__main__":
    report = load_report()
    md = generate_markdown(report)
    html = generate_html(report)

    md_path = PROJECT_ROOT / "tests" / "health_check_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Markdown report saved: {md_path}")

    html_path = PROJECT_ROOT / "tests" / "health_check_report.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML report saved: {html_path}")

    print(f"\nReport generated successfully at {datetime.now().isoformat()}")
