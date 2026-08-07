#!/usr/bin/env python3
"""
Sessao Conversacional Guiada (Fase 1 — validacao semi-automatica).

Loop interativo:
  1. Usuario digita pergunta (ou /help, /boletim, /sair)
  2. Omega(Ravena) processa e retorna resposta + diagnostico
  3. Professor avalia a resposta em tempo real
  4. Usuario pode corrigir (expert correction) para gerar exemplos
  5. Tudo registrado -> dataset de fine-tuning

Uso: python scripts/sessao_conversacional.py
"""

import os
import sys
import json
from datetime import datetime

_projeto_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _projeto_raiz not in sys.path:
    sys.path.insert(0, _projeto_raiz)

from src.core.omega import obter_omega, Omega, ResultadoMissao
from src.core.professor import Professor

# ── Palavras-chave para auto-classificacao ──
_AUTO_ASSUNTO = {
    "auto_consciencia": ["consciencia", "self", "quem sou", "identidade", "eu sou", "existencia"],
    "auto_etica": ["etica", "moral", "certo", "errado", "dever", "responsabilidade"],
    "auto_aprendizado": ["aprender", "estudo", "metodo", "ensino", "educacao", "conhecimento"],
    "auto_raciocinio": ["logica", "raciocinio", "pensamento", "deducao", "inferencia", "argumento"],
    "auto_linguagem": ["linguagem", "comunicacao", "fala", "texto", "significado", "semantica"],
    "auto_memoria": ["memoria", "lembrar", "esquecer", "recordar", "passado"],
    "auto_percepcao": ["percepcao", "sentido", "visao", "audicao", "observar", "notar"],
    "auto_emocao": ["emocao", "sentimento", "afeto", "paixao", "humor"],
    "auto_vontade": ["vontade", "desejo", "intencao", "motivacao", "escolha", "decisao"],
    "auto_criatividade": ["criatividade", "criar", "inovacao", "imaginacao", "original"],
    "auto_incerteza": ["incerteza", "duvida", "probabilidade", "risco", "ambiguidade"],
    "auto_sistema": ["sistema", "organizacao", "estrutura", "processo", "engenharia"],
    "auto_meta": ["meta", "objetivo", "proposito", "finalidade", "planejamento"],
    "auto_colaboracao": ["colaboracao", "equipe", "cooperacao", "grupo", "junto"],
    "auto_resiliencia": ["resiliencia", "falha", "erro", "recuperacao", "superar", "adaptacao"],
    "geral": []
}


def _detectar_assunto(pergunta: str) -> str:
    pl = pergunta.lower()
    for assunto, palavras in _AUTO_ASSUNTO.items():
        if assunto == "geral":
            continue
        for p in palavras:
            if p in pl:
                return assunto
    return "geral"


def _formatar_diagnostico(d: dict) -> str:
    linhas = [
        f"  Confianca: {d.get('confianca', 0):.2f}",
        f"  Fonte: {d.get('fonte', 'N/A')}",
        f"  Modulos: {', '.join(d.get('modulos_usados', []))}",
        f"  Tempo: {d.get('tempo_total_ms', 0):.0f}ms",
    ]
    if d.get("score_ameaca", 0) > 0:
        linhas.append(f"  Score ameaca: {d['score_ameaca']:.2f}")
    return "\n".join(linhas)


def _formatar_avaliacao(av: dict) -> str:
    linhas = [
        f"  Nota: {av.get('nota', 0):.1f}%",
        f"  Nivel: {av.get('nivel', 'N/A')}",
        f"  Metodologia: {av.get('metodologia', 'N/A')}",
        f"  Inspiracao: {av.get('inspiracao', 'N/A')}",
    ]
    if av.get("lacunas"):
        linhas.append(f"  Lacunas: {', '.join(av['lacunas'])}")
    if av.get("parecer"):
        linhas.append("  Parecer:")
        for linha in av["parecer"]:
            linhas.append(f"    ~ {linha}")
    return "\n".join(linhas)


def _mostrar_boletim(prof: Professor):
    boletim = prof.boletim_core()
    print(f"\n=== BOLETIM: {boletim['aluno']} | Nivel: {boletim['nivel_geral']} ===")
    materias = boletim.get("materias", {})
    if not materias:
        print("  (nenhuma materia registrada)")
    for assunto, info in sorted(materias.items()):
        print(f"  {assunto}")
        print(f"    Nivel: {info.get('nivel', 'N/A')}  |  Nota: {info.get('nota', 'N/A')}")
        comps = info.get("competencias", {})
        if comps:
            print(f"    Comp.: {', '.join(f'{k}={v:.2f}' for k, v in sorted(comps.items()) if isinstance(v, (int, float)))}")
    print(f"Exemplos expert: {boletim.get('total_exemplos_expert', 0)}")
    print()


def _mostrar_boletim_llm(prof: Professor):
    boletim = prof.boletim_llm()
    print(f"\n=== BOLETIM LLM ===")
    print(boletim)
    print()


def processar_pergunta(omega: Omega, prof: Professor, pergunta: str, assunto: str = "geral") -> dict:
    if assunto == "geral":
        auto = _detectar_assunto(pergunta)
        if auto != "geral":
            assunto = auto

    resultado: ResultadoMissao = omega.executar(pergunta)

    resposta_dict = {}
    avaliacao = None
    if prof and resultado.sucesso:
        resposta_dict = {
            "confianca": resultado.diagnostico.confianca,
            "precisao_tecnica": resultado.diagnostico.confianca,
            "completude": min(resultado.diagnostico.confianca + 0.1, 1.0),
            "clareza": min(resultado.diagnostico.confianca + 0.05, 1.0),
            "fundamentacao": resultado.diagnostico.authority_score or resultado.diagnostico.confianca,
            "fonte": resultado.diagnostico.fonte,
            "resposta": resultado.resposta,
        }
        avaliacao = prof.avaliar(assunto, resposta_dict)

    return {
        "pergunta": pergunta,
        "assunto": assunto,
        "sucesso": resultado.sucesso,
        "resposta": resultado.resposta,
        "raciocinio": resultado.raciocinio,
        "erro": resultado.erro,
        "sugestao": resultado.sugestao,
        "diagnostico": {
            "confianca": resultado.diagnostico.confianca,
            "fonte": resultado.diagnostico.fonte,
            "modulos_usados": resultado.diagnostico.modulos_usados,
            "tempo_total_ms": resultado.diagnostico.tempo_total_ms,
            "authority_score": resultado.diagnostico.authority_score,
            "score_ameaca": resultado.diagnostico.score_ameaca,
        },
        "avaliacao_professor": avaliacao,
    }


def main():
    import sys
    modo_one_shot = len(sys.argv) > 1 and not sys.argv[1].startswith("/")
    if not modo_one_shot:
        print("=" * 66)
        print("  RAVENA — Sessao Conversacional Guiada (Fase 1)")
        print("  Professor ativo: todas as respostas sao avaliadas")
        print("=" * 66)
        print("  /assunto <nome>  : define o assunto da proxima pergunta")
        print("  /perfil  <nome>  : troca perfil (permissiva, intermediaria, agressiva)")
        print("  /perfis          : lista perfis disponiveis")
        print("  /boletim         : mostra boletim core do Professor")
        print("  /boletim-llm     : mostra boletim LLM (dataset status)")
        print("  /sair            : encerra sessao")
        print()

    # ── Inicializacao Omega ──
    print("[*] Inicializando Ravena (Omega 4.0.0)... ", end="", flush=True)
    try:
        omega: Omega = obter_omega()
        print("OK")
    except Exception as e:
        print(f"FALHA: {e}")
        sys.exit(1)

    # ── Inicializacao Professor ──
    print("[*] Inicializando Professor... ", end="", flush=True)
    try:
        prof = Professor()
        print("OK")
    except Exception as e:
        print(f"FALHA: {e}")
        prof = None

    # ── One-shot mode: processa argumento e sai ──
    if modo_one_shot:
        pergunta = " ".join(sys.argv[1:])
        print(f"\n[Pergunta] {pergunta}")
        print("  [Ravena processando...]", end=" ", flush=True)
        try:
            resultado = processar_pergunta(omega, prof, pergunta)
            print("OK")
        except Exception as e:
            print(f"ERRO: {e}")
            sys.exit(1)

        print(f"\n  Resposta: {resultado['resposta']}")
        if resultado["raciocinio"]:
            print(f"  Raciocinio: {resultado['raciocinio'][:300]}{'...' if len(resultado['raciocinio']) > 300 else ''}")
        if resultado["diagnostico"]["modulos_usados"]:
            print(f"  Modulos: {', '.join(resultado['diagnostico']['modulos_usados'])}")
        if resultado["avaliacao_professor"]:
            print(f"\n  --- Professor ---")
            print(_formatar_avaliacao(resultado["avaliacao_professor"]))
        if resultado["erro"]:
            print(f"\n  [!] {resultado['erro']}: {resultado.get('sugestao', '')}")
        print()
        return

    # ── Estado da sessao ──
    assunto_atual = "geral"
    historico = []

    # ── Loop conversacional ──
    while True:
        try:
            perfil_tag = omega._perfil_nome[:4] if hasattr(omega, '_perfil_nome') and omega._perfil_nome else "???"
            entrada = input(f"\n[Voce] ({assunto_atual}) [{perfil_tag}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not entrada:
            continue

        # Comandos
        if entrada.lower() in ("/sair", "/exit", "/quit"):
            break
        if entrada.lower().startswith("/assunto "):
            assunto_atual = entrada[9:].strip()
            print(f"  Assunto alterado para: {assunto_atual}")
            continue
        if entrada.lower() == "/boletim":
            if prof:
                _mostrar_boletim(prof)
            else:
                print("  Professor nao disponivel")
            continue
        if entrada.lower() == "/boletim-llm":
            if prof:
                _mostrar_boletim_llm(prof)
            else:
                print("  Professor nao disponivel")
            continue
        if entrada.lower().startswith("/perfil "):
            nome_perfil = entrada[8:].strip()
            if omega.aplicar_perfil(nome_perfil):
                print(f"  Perfil alterado para: {nome_perfil}")
            else:
                perfis = omega.listar_perfis()
                print(f"  Perfil '{nome_perfil}' nao encontrado. Disponiveis: {', '.join(perfis['perfis_disponiveis'].keys())}")
            continue
        if entrada.lower() == "/perfis":
            perfis = omega.listar_perfis()
            print(f"  Perfil ativo: {perfis['perfil_atual']}")
            print("  Disponiveis:")
            for nome, info in perfis['perfis_disponiveis'].items():
                ativo = " <<" if nome == perfis['perfil_atual'] else ""
                print(f"    {nome:15s} - {info['label']:<15s} {info['descricao'][:50]}{ativo}")
            continue
        if entrada.lower() in ("/help", "/?"):
            print("  /assunto <nome>  : define assunto da proxima pergunta")
            print("  /perfil <nome>   : troca perfil (permissiva, intermediaria, agressiva)")
            print("  /perfis          : lista perfis disponiveis e o ativo")
            print("  /boletim         : boletim core (notas, materias)")
            print("  /boletim-llm     : boletim LLM (dataset status)")
            print("  /sair            : encerra sessao")
            continue

        # ── Ravena processa + Professor avalia ──
        print("  [Ravena processando...]", end=" ", flush=True)
        try:
            resultado = processar_pergunta(omega, prof, entrada, assunto_atual if assunto_atual != "geral" else None)
            print("OK")
        except Exception as e:
            print(f"ERRO: {e}")
            continue

        assunto_usado = resultado["assunto"]
        if assunto_atual == "geral" and assunto_usado != "geral":
            assunto_atual = assunto_usado
            print(f"  (assunto detectado: {assunto_atual})")

        # ── Mostrar ──
        print(f"\n  Resposta: {resultado['resposta']}")
        if resultado["raciocinio"]:
            print(f"  Raciocinio: {resultado['raciocinio'][:200]}{'...' if len(resultado['raciocinio']) > 200 else ''}")

        if resultado["avaliacao_professor"]:
            av = resultado["avaliacao_professor"]
            print(f"\n  --- Professor ---")
            print(_formatar_avaliacao(av))
            historico.append({"pergunta": entrada, "assunto": assunto_usado, "resposta": resultado["resposta"], "avaliacao": av})

            # ── Monta resposta_dict para correcao ──
            resp_dict = {
                "confianca": resultado["diagnostico"]["confianca"],
                "precisao_tecnica": resultado["diagnostico"]["confianca"],
                "completude": min(resultado["diagnostico"]["confianca"] + 0.1, 1.0),
                "clareza": min(resultado["diagnostico"]["confianca"] + 0.05, 1.0),
                "fundamentacao": resultado["diagnostico"]["authority_score"] or resultado["diagnostico"]["confianca"],
                "resposta": resultado["resposta"],
            }

            # ── Perguntar se quer corrigir ──
            try:
                corrigir = input("\n  Corrigir? (s/N/criterios) ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                corrigir = "n"

            if corrigir in ("s", "sim"):
                print("  Digite a correcao no formato JSON, ex:")
                print('  {"precisao_tecnica": 95, "completude": 80, "_observacao": "faltou mencionar X"}')
                try:
                    linha_correcao = input("  Correc.: ").strip()
                    correcao = json.loads(linha_correcao)
                except (EOFError, KeyboardInterrupt):
                    correcao = None
                except json.JSONDecodeError:
                    print("  JSON invalido. Usando correcao padrao (nota 90).")
                    correcao = {"precisao_tecnica": 90, "completude": 90, "clareza": 90, "fundamentacao": 90}

                if correcao:
                    corr = prof.corrigir(assunto_usado, resp_dict, correcao)
                    print(f"  Correcao registrada! Total exemplos: {corr['total_exemplos_expert']}")

            elif corrigir.startswith("{"):
                try:
                    correcao = json.loads(corrigir)
                    corr = prof.corrigir(assunto_usado, resp_dict, correcao)
                    print(f"  Correcao registrada! Total exemplos: {corr['total_exemplos_expert']}")
                except json.JSONDecodeError:
                    print("  JSON invalido, ignorado.")

        elif not resultado["sucesso"]:
            print(f"\n  [!] Falha: {resultado['erro']}")
            if resultado.get("sugestao"):
                print(f"      Sugestao: {resultado['sugestao']}")

        # ── Reset assunto se foi auto-detectado ──
        if assunto_atual != "geral" and entrada.lower().startswith("/assunto"):
            pass
        else:
            assunto_atual = "geral"

    # ── Fim da sessao ──
    print("\n\n=== FIM DA SESSAO ===")
    print(f"Total interacoes: {len(historico)}")
    print(f"Exemplos expert registrados: {prof.boletim_core().get('total_exemplos_expert', 0) if prof else 0}")
    print(f"Pronto para fine-tuning: {prof.boletim_llm() if prof else 'N/A'}")
    print("Até logo.\n")


if __name__ == "__main__":
    main()
