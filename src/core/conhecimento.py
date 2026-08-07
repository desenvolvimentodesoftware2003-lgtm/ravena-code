import os
import json
import time
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from copy import deepcopy

_projeto_raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_AUTHORITY_BASE = {
    "usuario": 0.9,
    "aprendizado": 0.7,
    "documento": 0.5,
    "inferido": 0.3,
    "conhecimento_interno": 0.5,
    "alimentacao": 0.5
}

_GRUPOS_PADRAO = {
    "geografia": {
        "palavras": ["capital", "pais", "cidade", "rio", "estado", "regiao", "continente", "oceano", "mapa", "fronteira", "habitante", "populacao", "localiza", "bandeira", "clima", "relevo", "latitude", "longitude", "territorio", "nacao", "municipio", "norte", "sul", "leste", "oeste"],
        "descricao": "Geografia, capitais, paises e cidades"
    },
    "ciencia": {
        "palavras": ["agua", "fotossintese", "energia", "bioquimico", "quimica", "fisica", "biologia", "celula", "dna", "atomo", "molecula", "reacao", "elemento", "composto", "forca", "movimento", "gravidade", "temperatura", "pressao", "volume", "massa", "densidade", "eletron", "proton", "neutron", "organismo", "especie", "ecossistema", "habitat", "evolucao", "genetica", "proteina", "enzima", "metabolismo", "fossil", "mineral", "rocha", "vulcao", "tornado", "furacao", "terremoto", "luz", "cor", "ceu", "atmosfera", "som", "onda"],
        "descricao": "Ciencias naturais e exatas"
    },
    "tecnologia": {
        "palavras": ["python", "programacao", "software", "computador", "algoritmo", "codigo", "linguagem", "compilador", "dados", "inteligencia", "ia", "rede", "internet", "servidor", "aplicativo", "sistema", "hardware", "memoria", "processador", "banco", "api", "frontend", "backend", "dev", "bug", "funcao", "variavel", "loop", "classe", "objeto", "metodo", "biblioteca", "framework", "script", "terminal", "comando", "docker", "git", "nuvem"],
        "descricao": "Tecnologia, programacao e computacao"
    },
    "automotivo": {
        "palavras": ["pneu", "carro", "motor", "roda", "freio", "embreagem", "cambio", "oleo", "combustivel", "gasolina", "direcao", "suspensao", "amortecedor", "radiador", "bateria", "alternador", "ignicao", "vela", "injetor", "turbo", "escapamento", "catalisador", "pistao", "cilindro", "valvula", "correia", "filtro", "farol", "painel", "tanque", "porta", "vidro", "travas", "alarme", "airbag", "lataria", "pintura", "retrovisor", "limpador", "buzina", "oficina", "mecanico", "revisao", "troca", "vazamento"],
        "descricao": "Automotivo, veiculos e mecanica"
    },
    "historia": {
        "palavras": ["descobriu", "guerra", "imperio", "revolucao", "seculo", "ano", "data", "epoca", "periodo", "antigo", "civilizacao", "historia", "fundador", "inventou", "criou", "imperador", "rei", "rainha", "presidente", "ditador", "colonia", "independencia", "batalha", "tratado", "nazismo", "feudal", "renascimento", "iluminismo", "escravidao", "democracia", "república", "monarquia", "reinado", "dinastia", "arqueologia", "pre historia"],
        "descricao": "Historia e eventos historicos"
    },
    "matematica": {
        "palavras": ["numero", "formula", "equacao", "calculo", "geometria", "algebra", "teorema", "logaritmo", "funcao", "derivada", "integral", "estatistica", "probabilidade", "soma", "subtracao", "divisao", "multiplicacao", "matriz", "vetor", "angulo", "triangulo", "quadrado", "circulo", "porcentagem", "media", "mediana", "moda", "desvio", "padrao", "limite", "sequencia", "serie"],
        "descricao": "Matematica e formulas"
    },
    "lingua": {
        "palavras": ["significa", "palavra", "lingua", "idioma", "traducao", "portugues", "ingles", "espanhol", "sinonimo", "antonimo", "gramatica", "verbo", "substantivo", "adjetivo", "adverbio", "preposicao", "conjugacao", "ortografia", "acentuacao", "pontuacao", "silaba", "ditongo", "hiato", "fonetica", "semantica", "morfologia", "sintaxe", "prefixo", "sufixo", "radical"],
        "descricao": "Linguas e linguistica"
    },
    "saude": {
        "palavras": ["doenca", "saude", "medico", "sintoma", "tratamento", "virus", "bacteria", "vacina", "remedio", "hospital", "alimentacao", "exercicio", "corpo", "mental", "febre", "dor", "cirurgia", "diagnostico", "prevencao", "cancer", "diabetes", "colesterol", "pressao", "cardiaco", "respiratorio", "digestivo", "nervoso", "muscular", "esqueletico", "pele", "cabelo", "unha", "visao", "audicao", "olfato", "paladar", "tato", "nutricao", "dieta", "vitamina", "mineral", "caloria", "proteina", "carboidrato", "gordura", "imunidade", "alergia", "inflamacao", "infeccao", "ferimento", "queimadura", "fratura"],
        "descricao": "Saude e medicina"
    },
    "filosofia": {
        "palavras": ["filosofia", "existencia", "etica", "moral", "pensador", "logica", "conhecimento", "verdade", "razao", "mente", "consciencia", "significado", "proposito", "socrates", "platao", "aristoteles", "nietzsche", "kant", "descartes", "estoico", "epicuro", "sofista", "dialetica", "metafisica", "epistemologia", "axiologia", "estetica", "politica", "justica", "liberdade", "igualdade", "dever", "virtude", "felicidade", "bem", "mal", "dualismo", "materialismo", "idealismo", "realismo", "pragmatismo", "ceticismo", "dogmatismo", "ontologia", "teleologia"],
        "descricao": "Filosofia e pensamento"
    },
    "geral": {
        "palavras": [],
        "descricao": "Conhecimento geral"
    }
}

logger = logging.getLogger("ravena.conhecimento")

@dataclass
class ItemConhecimento:
    id: str = ""
    pergunta: str = ""
    conteudo: str = ""
    fonte: str = "usuario"
    estado: str = "ativo"
    grupo: str = ""
    authority_score: float = 0.5
    timestamp_criacao: str = ""
    timestamp_atualizacao: str = ""
    acertos: int = 0
    erros: int = 0
    historico: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def para_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "pergunta": self.pergunta,
            "conteudo": self.conteudo,
            "fonte": self.fonte,
            "estado": self.estado,
            "grupo": self.grupo,
            "authority_score": self.authority_score,
            "timestamp_criacao": self.timestamp_criacao,
            "timestamp_atualizacao": self.timestamp_atualizacao,
            "acertos": self.acertos,
            "erros": self.erros,
            "historico": self.historico,
            "metadata": self.metadata
        }

    @classmethod
    def de_dict(cls, dados: Dict[str, Any]) -> "ItemConhecimento":
        return cls(
            id=dados.get("id", ""),
            pergunta=dados.get("pergunta", ""),
            conteudo=dados.get("conteudo", ""),
            fonte=dados.get("fonte", "usuario"),
            estado=dados.get("estado", "ativo"),
            grupo=dados.get("grupo", ""),
            authority_score=dados.get("authority_score", 0.5),
            timestamp_criacao=dados.get("timestamp_criacao", ""),
            timestamp_atualizacao=dados.get("timestamp_atualizacao", ""),
            acertos=dados.get("acertos", 0),
            erros=dados.get("erros", 0),
            historico=dados.get("historico", []),
            metadata=dados.get("metadata", {})
        )


class ConhecimentoPith:
    def __init__(self, caminho_base: Optional[str] = None):
        self._itens: Dict[str, ItemConhecimento] = {}
        self._caminho_base = caminho_base or os.path.join(_projeto_raiz, "data", "conhecimento_base.json")
        self._proximo_id = 1
        self._carregar_base()
        logger.info(f"ConhecimentoPith inicializado com {len(self._itens)} itens")

    def _carregar_base(self):
        if os.path.exists(self._caminho_base):
            try:
                with open(self._caminho_base, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                for item_dict in dados.get("itens", []):
                    item = ItemConhecimento.de_dict(item_dict)
                    self._itens[item.id] = item
                self._proximo_id = max((int(i) for i in self._itens.keys()), default=0) + 1
                logger.info(f"Base carregada: {len(self._itens)} itens de {self._caminho_base}")
            except Exception as e:
                logger.warning(f"Erro ao carregar base: {e}")

    def _salvar_base(self):
        try:
            dir_base = os.path.dirname(self._caminho_base)
            os.makedirs(dir_base, exist_ok=True)
            with open(self._caminho_base, "w", encoding="utf-8") as f:
                json.dump({
                    "versao": "1.0.0",
                    "atualizado": datetime.now().isoformat(),
                    "itens": [item.para_dict() for item in self._itens.values()]
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Erro ao salvar base: {e}")

    def _gerar_id(self) -> str:
        id_atual = self._proximo_id
        self._proximo_id += 1
        return str(id_atual)

    def _agora(self) -> str:
        return datetime.now().isoformat()

    def _tokenizar(self, texto: str) -> set:
        texto = texto.lower()
        tokens = re.findall(r'\w+', texto)
        return set(tokens)

    def _calcular_authority_score(self, fonte: str, acertos: int = 0, erros: int = 0) -> float:
        base = _AUTHORITY_BASE.get(fonte, 0.3)
        total = acertos + erros
        if total > 0:
            taxa_acerto = acertos / total
            ajuste = (taxa_acerto - 0.5) * 0.4
        else:
            ajuste = 0.0
        score = base + ajuste
        return max(0.1, min(1.0, round(score, 4)))

    def _similaridade(self, pergunta: str, item: ItemConhecimento) -> float:
        tokens_pergunta = self._tokenizar(pergunta)
        tokens_item = self._tokenizar(item.pergunta)
        if not tokens_pergunta or not tokens_item:
            return 0.0
        tokens_comuns = tokens_pergunta & tokens_item
        if len(tokens_pergunta) == 0:
            return 0.0
        sim = len(tokens_comuns) / len(tokens_pergunta)
        if len(tokens_pergunta) <= 2 and sim > 0.5:
            sim *= 0.6
        return sim

    def _classificar_grupo(self, pergunta: str, conteudo: str = "") -> str:
        try:
            if not hasattr(self, "_cx"):
                from src.core.contextualidade import Contextualidade
                self._cx = Contextualidade()
            texto_limpo = self._cx.limpar_para_classificacao(f"{pergunta} {conteudo}")
        except ImportError:
            texto_limpo = f"{pergunta} {conteudo}".lower()
        palavras_texto = set(re.findall(r'\w+', texto_limpo))
        if not palavras_texto:
            return "geral"
        melhor_grupo = "geral"
        melhor_pontuacao = 0
        for grupo, config in _GRUPOS_PADRAO.items():
            if not config["palavras"]:
                continue
            pontuacao = sum(1 for p in config["palavras"] if p in palavras_texto)
            if pontuacao > melhor_pontuacao:
                melhor_pontuacao = pontuacao
                melhor_grupo = grupo
        return melhor_grupo

    def ensinar(self, pergunta: str, conteudo: str, fonte: str = "usuario",
                metadata: Optional[Dict[str, Any]] = None, grupo: Optional[str] = None) -> ItemConhecimento:
        pergunta = pergunta.strip().lower()
        if not pergunta or not conteudo:
            logger.warning("Ensinar ignorado: pergunta ou conteudo vazio")
            return None

        for item in self._itens.values():
            if item.pergunta == pergunta and item.estado in ("ativo", "contestado"):
                item.conteudo = conteudo
                item.fonte = fonte
                item.authority_score = self._calcular_authority_score(fonte, item.acertos, item.erros)
                item.timestamp_atualizacao = self._agora()
                if item.estado == "contestado":
                    item.estado = "resolvido"
                    item.historico.append({
                        "acao": "contestacao_resolvida",
                        "novo_conteudo": conteudo,
                        "timestamp": self._agora()
                    })
                logger.info(f"Conhecimento atualizado: '{pergunta[:50]}...' -> {fonte}")
                self._salvar_base()
                return item

        grupo_final = grupo or self._classificar_grupo(pergunta, conteudo)

        item = ItemConhecimento(
            id=self._gerar_id(),
            pergunta=pergunta,
            conteudo=conteudo,
            fonte=fonte,
            estado="ativo",
            grupo=grupo_final,
            authority_score=self._calcular_authority_score(fonte),
            timestamp_criacao=self._agora(),
            timestamp_atualizacao=self._agora(),
            metadata=metadata or {}
        )
        self._itens[item.id] = item
        logger.info(f"Novo conhecimento: '{pergunta[:50]}...' -> {fonte} (score: {item.authority_score})")
        self._salvar_base()
        return item

    def buscar(self, pergunta: str, max_resultados: int = 5,
               similaridade_minima: float = 0.5) -> List[Dict[str, Any]]:
        pergunta = pergunta.strip().lower()
        if not pergunta:
            return []

        tokens = self._tokenizar(pergunta)
        if len(tokens) <= 2:
            similaridade_minima = max(similaridade_minima, 0.8)

        resultados = []
        for item in self._itens.values():
            if item.estado in ("substituido", "stale"):
                continue
            if item.estado == "contestado":
                continue

            sim = self._similaridade(pergunta, item)
            if sim >= similaridade_minima:
                score_combinado = sim * 0.4 + item.authority_score * 0.6
                resultados.append({
                    "id": item.id,
                    "conteudo": item.conteudo,
                    "pergunta": item.pergunta,
                    "fonte": item.fonte,
                    "authority_score": round(item.authority_score, 4),
                    "score_combinado": round(score_combinado, 4),
                    "estado_crenca": item.estado,
                    "timestamp": item.timestamp_atualizacao
                })

        resultados.sort(key=lambda x: x["score_combinado"], reverse=True)
        top = resultados[:max_resultados]
        logger.info(f"Busca por '{pergunta[:50]}...': {len(resultados)} encontrados, {len(top)} retornados")
        return top

    def contestar(self, pergunta: str, fonte: str = "usuario",
                  motivo: str = "resposta incorreta") -> bool:
        pergunta = pergunta.strip().lower()
        for item in self._itens.values():
            if item.pergunta == pergunta and item.estado == "ativo":
                item.estado = "contestado"
                item.erros += 1
                item.authority_score = self._calcular_authority_score(item.fonte, item.acertos, item.erros)
                item.timestamp_atualizacao = self._agora()
                item.historico.append({
                    "acao": "contestado",
                    "fonte": fonte,
                    "motivo": motivo,
                    "timestamp": self._agora()
                })
                logger.info(f"Conhecimento contestado: '{pergunta[:50]}...' (score: {item.authority_score})")
                self._salvar_base()
                return True
        logger.warning(f"Nao foi possivel contestar: '{pergunta[:50]}...' nao encontrado")
        return False

    def resolver(self, pergunta: str, correcao: str, fonte: str = "usuario") -> bool:
        pergunta = pergunta.strip().lower()
        for item in self._itens.values():
            if item.pergunta == pergunta and item.estado == "contestado":
                item.historico.append({
                    "acao": "resolvido",
                    "conteudo_anterior": item.conteudo,
                    "conteudo_novo": correcao,
                    "fonte": fonte,
                    "timestamp": self._agora()
                })
                item.conteudo = correcao
                item.estado = "resolvido"
                item.acertos += 1
                item.authority_score = self._calcular_authority_score(fonte, item.acertos, item.erros)
                item.timestamp_atualizacao = self._agora()
                logger.info(f"Conhecimento resolvido: '{pergunta[:50]}...'")
                self._salvar_base()
                return True
            if item.pergunta == pergunta and item.estado == "ativo":
                return self.ensinar(pergunta, correcao, fonte) is not None
        return self.ensinar(pergunta, correcao, fonte) is not None

    def substituir(self, pergunta_antiga: str, nova_pergunta: str,
                   novo_conteudo: str, fonte: str = "usuario") -> bool:
        pergunta_antiga = pergunta_antiga.strip().lower()
        nova_pergunta = nova_pergunta.strip().lower()

        for item in self._itens.values():
            if item.pergunta == pergunta_antiga and item.estado in ("ativo", "contestado", "resolvido"):
                item.historico.append({
                    "acao": "substituido",
                    "nova_pergunta": nova_pergunta,
                    "novo_conteudo": novo_conteudo,
                    "timestamp": self._agora()
                })
                item.estado = "substituido"
                item.timestamp_atualizacao = self._agora()
                break

        novo_item = ItemConhecimento(
            id=self._gerar_id(),
            pergunta=nova_pergunta,
            conteudo=novo_conteudo,
            fonte=fonte,
            estado="ativo",
            authority_score=self._calcular_authority_score(fonte),
            timestamp_criacao=self._agora(),
            timestamp_atualizacao=self._agora(),
            metadata={"substitui": pergunta_antiga}
        )
        self._itens[novo_item.id] = novo_item
        logger.info(f"Conhecimento substituido: '{pergunta_antiga[:50]}...' -> '{nova_pergunta[:50]}...'")
        self._salvar_base()
        return True

    def podar_stale(self, meia_vida_horas: float = 720.0):
        agora = datetime.now()
        limite = timedelta(hours=meia_vida_horas)
        removidos = 0
        for item in list(self._itens.values()):
            if item.estado in ("substituido",):
                continue
            if item.timestamp_atualizacao:
                try:
                    ultima_atualizacao = datetime.fromisoformat(item.timestamp_atualizacao)
                    if (agora - ultima_atualizacao) > limite:
                        item.estado = "stale"
                        item.timestamp_atualizacao = self._agora()
                        removidos += 1
                except ValueError:
                    continue
        if removidos > 0:
            logger.info(f"Podagem concluida: {removidos} itens marcados como stale")
            self._salvar_base()

    def confirmar_acerto(self, pergunta: str) -> bool:
        pergunta = pergunta.strip().lower()
        for item in self._itens.values():
            if item.pergunta == pergunta and item.estado in ("ativo", "resolvido"):
                item.acertos += 1
                item.authority_score = self._calcular_authority_score(item.fonte, item.acertos, item.erros)
                item.timestamp_atualizacao = self._agora()
                if item.estado == "contestado":
                    item.estado = "resolvido"
                logger.info(f"Acerto confirmado: '{pergunta[:50]}...' (score: {item.authority_score})")
                self._salvar_base()
                return True
        return False

    def obter_estatisticas(self) -> Dict[str, Any]:
        total = len(self._itens)
        estados: Dict[str, int] = {}
        fontes: Dict[str, int] = {}
        grupos: Dict[str, int] = {}
        for item in self._itens.values():
            estados[item.estado] = estados.get(item.estado, 0) + 1
            fontes[item.fonte] = fontes.get(item.fonte, 0) + 1
            nome_grupo = item.grupo or "geral"
            grupos[nome_grupo] = grupos.get(nome_grupo, 0) + 1
        return {
            "total": total,
            "estados": estados,
            "fontes": fontes,
            "grupos": grupos,
            "authority_score_medio": round(sum(
                i.authority_score for i in self._itens.values()
            ) / total, 4) if total > 0 else 0.0
        }

    def listar_ativos(self) -> List[Dict[str, Any]]:
        return [
            {"id": i.id, "pergunta": i.pergunta, "conteudo": i.conteudo,
             "fonte": i.fonte, "grupo": i.grupo, "authority_score": i.authority_score,
             "estado_crenca": i.estado, "acertos": i.acertos, "erros": i.erros}
            for i in self._itens.values() if i.estado in ("ativo", "resolvido")
        ]

    def listar_contestados(self) -> List[Dict[str, Any]]:
        return [
            {"id": i.id, "pergunta": i.pergunta, "conteudo": i.conteudo,
             "fonte": i.fonte, "authority_score": i.authority_score}
            for i in self._itens.values() if i.estado == "contestado"
        ]

    def agrupar(self) -> Dict[str, List[Dict[str, Any]]]:
        grupos: Dict[str, List[Dict[str, Any]]] = {}
        for item in self._itens.values():
            nome_grupo = item.grupo or "geral"
            if nome_grupo not in grupos:
                grupos[nome_grupo] = []
            grupos[nome_grupo].append({
                "id": item.id,
                "pergunta": item.pergunta,
                "conteudo": item.conteudo,
                "fonte": item.fonte,
                "estado": item.estado,
                "authority_score": item.authority_score
            })
        return grupos

    def listar_grupos(self) -> Dict[str, Any]:
        grupos = self.agrupar()
        resultado = {
            "total_grupos": len(grupos),
            "descricao_grupos": {}
        }
        for nome, itens in sorted(grupos.items()):
            desc = _GRUPOS_PADRAO.get(nome, {}).get("descricao", nome)
            ativos = sum(1 for i in itens if i["estado"] == "ativo")
            resultado["descricao_grupos"][nome] = {
                "descricao": desc,
                "total": len(itens),
                "ativos": ativos,
                "authority_medio": round(sum(i["authority_score"] for i in itens) / len(itens), 4)
            }
        return resultado

    def buscar_por_grupo(self, pergunta: str, grupo: str,
                         max_resultados: int = 5,
                         similaridade_minima: float = 0.5) -> List[Dict[str, Any]]:
        itens_grupo = [i for i in self._itens.values()
                       if (i.grupo or "geral") == grupo and i.estado in ("ativo", "resolvido")]
        if not itens_grupo:
            return []
        resultados = []
        for item in itens_grupo:
            sim = self._similaridade(pergunta, item)
            if sim >= similaridade_minima:
                resultados.append({
                    "id": item.id,
                    "pergunta": item.pergunta,
                    "conteudo": item.conteudo,
                    "fonte": item.fonte,
                    "authority_score": item.authority_score,
                    "estado_crenca": item.estado,
                    "similaridade": round(sim, 4),
                    "grupo": item.grupo
                })
        resultados.sort(key=lambda x: (x["authority_score"] * x["similaridade"]), reverse=True)
        return resultados[:max_resultados]

    def reorganizar(self):
        for item in self._itens.values():
            grupo_antigo = item.grupo
            item.grupo = self._classificar_grupo(item.pergunta, item.conteudo)
            if grupo_antigo != item.grupo:
                logger.info(f"Item {item.id} movido: {grupo_antigo} -> {item.grupo}")
        self._salvar_base()
        logger.info("Base reclassificada por grupos")

    def limpar(self):
        self._itens.clear()
        self._proximo_id = 1
        if os.path.exists(self._caminho_base):
            os.remove(self._caminho_base)
        logger.info("Base de conhecimento limpa")


if __name__ == "__main__":
    import json

    pith = ConhecimentoPith()
    pith.ensinar("qual e a capital do brasil", "Brasilia", "usuario")
    pith.ensinar("qual e a capital da franca", "Paris", "usuario")
    pith.ensinar("o que e fotossintese", "Processo pelo qual plantas convertem luz em energia", "aprendizado")
    pith.ensinar("quem descobriu o brasil", "Pedro Alvares Cabral em 1500", "documento")
    pith.ensinar("o que e python", "Linguagem de programacao interpretada", "aprendizado")

    print("=== GRUPOS DETECTADOS AUTOMATICAMENTE ===")
    grupos = pith.agrupar()
    for nome, itens in sorted(grupos.items()):
        desc = _GRUPOS_PADRAO.get(nome, {}).get("descricao", nome)
        print(f"  {nome} ({desc}): {len(itens)} itens")
        for item in itens:
            print(f"    - {item['pergunta'][:40]}")

    print()
    print("=== LISTAR GRUPOS ===")
    print(json.dumps(pith.listar_grupos(), indent=2, ensure_ascii=False))

    print()
    print("=== BUSCA POR GRUPO ===")
    resultados = pith.buscar_por_grupo("capital", "geografia")
    for r in resultados:
        print(f"  [{r['grupo']}] {r['pergunta']} -> {r['conteudo']} (sim: {r['similaridade']})")

    print()
    print("=== ESTATISTICAS ===")
    print(json.dumps(pith.obter_estatisticas(), indent=2, ensure_ascii=False))

    print()
    print("=== BUSCA: 'capital do brasil' ===")
    resultados = pith.buscar("capital do brasil")
    for r in resultados:
        print(f"  - {r['conteudo']} (fonte: {r['fonte']}, authority: {r['authority_score']}, estado: {r['estado_crenca']})")

    print()
    print("=== CONTESTAR E RESOLVER ===")
    pith.contestar("quem descobriu o brasil", motivo="versao incompleta")
    print("Contestado:", [i["pergunta"] for i in pith.listar_contestados()])
    pith.resolver("quem descobriu o brasil", "Os povos indigenas ja habitavam o Brasil antes de 1500")
    print("Resolvido. Estatisticas:", json.dumps(pith.obter_estatisticas(), indent=2, ensure_ascii=False))

    print()
    print("=== BUSCA: 'fotossintese' ===")
    resultados = pith.buscar("fotossintese")
    for r in resultados:
        print(f"  - {r['conteudo'][:60]}... (score: {r['authority_score']})")
