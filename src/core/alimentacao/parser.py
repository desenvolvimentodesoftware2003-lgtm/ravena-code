import os
import re
import ast
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("ravena.alimentacao.parser")

@dataclass
class ItemParseado:
    pergunta: str
    conteudo: str
    grupo: str
    fonte: str
    hash_item: str
    metadados: Dict[str, Any]

_PADRAO_HEADING = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)
_PADRAO_CLASSE = re.compile(r'^class\s+(\w+)')
_PADRAO_FUNCAO = re.compile(r'^def\s+(\w+)\s*\(')
_PADRAO_DOCSTRING = re.compile(r'"""(.*?)"""', re.DOTALL)
_PADRAO_COMENTARIO_BLOCO = re.compile(r"'''(.+?)'''", re.DOTALL)

class ParserArquivo:
    def parsear(self, caminho: str) -> List[ItemParseado]:
        ext = os.path.splitext(caminho)[1].lower()
        if ext == ".md":
            return self._parse_md(caminho)
        elif ext == ".py":
            return self._parse_py(caminho)
        elif ext == ".txt":
            return self._parse_txt(caminho)
        elif ext == ".json":
            return self._parse_json(caminho)
        elif ext == ".pdf":
            return self._parse_pdf(caminho)
        else:
            logger.warning(f"Extensao nao suportada: {ext} para {caminho}")
            return []

    def _extrair_hash(self, pergunta: str, conteudo: str) -> str:
        import hashlib
        return hashlib.sha256(f"{pergunta}|{conteudo}".encode("utf-8")).hexdigest()[:16]

    def _parse_md(self, caminho: str) -> List[ItemParseado]:
        with open(caminho, "r", encoding="utf-8", errors="replace") as f:
            texto = f.read()

        secoes = self._extrair_secoes(texto)
        itens = []
        for titulo, conteudo in secoes:
            pergunta = f"O que e {titulo.strip().lower()}?"
            conteudo_limpo = conteudo.strip()
            if conteudo_limpo:
                itens.append(ItemParseado(
                    pergunta=pergunta,
                    conteudo=conteudo_limpo,
                    grupo="",
                    fonte=caminho,
                    hash_item=self._extrair_hash(pergunta, conteudo_limpo),
                    metadados={"tipo": "md_section", "titulo": titulo.strip()}
                ))

        if not itens:
            texto_limpo = texto.strip()
            if len(texto_limpo) > 100:
                primeiras_linhas = "\n".join(texto.split("\n")[:5])
                itens.append(ItemParseado(
                    pergunta=f"Sobre {os.path.basename(caminho)}",
                    conteudo=texto_limpo[:2000],
                    grupo="",
                    fonte=caminho,
                    hash_item=self._extrair_hash(os.path.basename(caminho), texto_limpo[:2000]),
                    metadados={"tipo": "md_full", "arquivo": os.path.basename(caminho)}
                ))

        return itens

    def _extrair_secoes(self, texto: str) -> List[tuple]:
        linhas = texto.split("\n")
        secoes = []
        titulo_atual = "Documento"
        conteudo_atual = []

        for linha in linhas:
            match = _PADRAO_HEADING.match(linha)
            if match:
                if conteudo_atual:
                    secoes.append((titulo_atual, "\n".join(conteudo_atual).strip()))
                titulo_atual = match.group(1).strip()
                conteudo_atual = []
            else:
                conteudo_atual.append(linha)

        if conteudo_atual:
            secoes.append((titulo_atual, "\n".join(conteudo_atual).strip()))

        return secoes

    def _parse_py(self, caminho: str) -> List[ItemParseado]:
        with open(caminho, "r", encoding="utf-8", errors="replace") as f:
            texto = f.read()

        itens = []

        try:
            arvore = ast.parse(texto)

            classes_definidas = {no.name for no in ast.walk(arvore) if isinstance(no, ast.ClassDef)}
            funcoes_topo = []
            for no in ast.iter_child_nodes(arvore):
                if isinstance(no, ast.FunctionDef):
                    funcoes_topo.append(no.name)

            for no in ast.walk(arvore):
                if isinstance(no, ast.ClassDef):
                    docstring = ast.get_docstring(no) or ""
                    metodos = [n.name for n in no.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    conteudo = docstring if docstring else f"Classe com metodos: {', '.join(metodos[:10])}"
                    if conteudo:
                        itens.append(ItemParseado(
                            pergunta=f"O que faz a classe {no.name}?",
                            conteudo=conteudo,
                            grupo="",
                            fonte=caminho,
                            hash_item=self._extrair_hash(no.name, conteudo),
                            metadados={"tipo": "py_class", "nome": no.name, "metodos": metodos}
                        ))

                elif isinstance(no, ast.FunctionDef):
                    if no.name in funcoes_topo:
                        docstring = ast.get_docstring(no) or ""
                        if docstring:
                            itens.append(ItemParseado(
                                pergunta=f"O que faz a funcao {no.name}?",
                                conteudo=docstring,
                                grupo="",
                                fonte=caminho,
                                hash_item=self._extrair_hash(no.name, docstring),
                                metadados={"tipo": "py_function", "nome": no.name}
                            ))
        except SyntaxError:
            logger.warning(f"Erro de sintaxe ao parsear {caminho}, usando fallback regex")
            itens = self._parse_py_fallback(texto, caminho)

        return itens

    def _parse_py_fallback(self, texto: str, caminho: str) -> List[ItemParseado]:
        itens = []
        for match in _PADRAO_CLASSE.finditer(texto):
            nome_classe = match.group(1)
            itens.append(ItemParseado(
                pergunta=f"O que faz a classe {nome_classe}?",
                conteudo=f"Classe {nome_classe} definida em {os.path.basename(caminho)}.",
                grupo="",
                fonte=caminho,
                hash_item=self._extrair_hash(nome_classe, caminho),
                metadados={"tipo": "py_class_fallback", "nome": nome_classe}
            ))
        return itens

    def _parse_txt(self, caminho: str) -> List[ItemParseado]:
        with open(caminho, "r", encoding="utf-8", errors="replace") as f:
            texto = f.read()

        blocos = [b.strip() for b in re.split(r'\n\s*\n', texto) if b.strip()]
        itens = []
        for i, bloco in enumerate(blocos):
            if len(bloco) < 50:
                continue
            primeiras_linhas = bloco.split("\n")[0][:80]
            pergunta = f"Sobre {primeiras_linhas.lower().rstrip('.')}"
            itens.append(ItemParseado(
                pergunta=pergunta,
                conteudo=bloco[:2000],
                grupo="",
                fonte=caminho,
                hash_item=self._extrair_hash(pergunta, bloco[:2000]),
                metadados={"tipo": "txt_block", "indice": i}
            ))
        return itens

    def _parse_json(self, caminho: str) -> List[ItemParseado]:
        with open(caminho, "r", encoding="utf-8", errors="replace") as f:
            dados = json.load(f)

        itens = []
        if isinstance(dados, dict):
            for chave, valor in dados.items():
                if isinstance(valor, str) and len(valor) > 20:
                    itens.append(ItemParseado(
                        pergunta=f"O que e {chave} na configuracao?",
                        conteudo=valor,
                        grupo="",
                        fonte=caminho,
                        hash_item=self._extrair_hash(chave, valor),
                        metadados={"tipo": "json_key", "chave": chave}
                    ))
                elif isinstance(valor, (dict, list)):
                    itens.append(ItemParseado(
                        pergunta=f"Qual e a configuracao de {chave}?",
                        conteudo=json.dumps(valor, ensure_ascii=False, indent=2)[:2000],
                        grupo="",
                        fonte=caminho,
                        hash_item=self._extrair_hash(chave, str(valor)),
                        metadados={"tipo": "json_complex", "chave": chave}
                    ))
        return itens

    def _parse_pdf(self, caminho: str) -> List[ItemParseado]:
        try:
            import fitz
        except ImportError:
            logger.warning("PyMuPDF nao instalado. Use: pip install pymupdf")
            return []

        try:
            doc = fitz.open(caminho)
            texto_completo = ""
            for pagina in doc:
                texto_completo += pagina.get_text()
            doc.close()
        except Exception as e:
            logger.warning(f"Erro ao ler PDF {caminho}: {e}")
            return []

        secoes = self._extrair_secoes(texto_completo)
        itens = []
        for titulo, conteudo in secoes:
            conteudo_limpo = conteudo.strip()
            if len(conteudo_limpo) < 50:
                continue
            pergunta = f"O que e {titulo.strip().lower()}?"
            itens.append(ItemParseado(
                pergunta=pergunta,
                conteudo=conteudo_limpo[:2000],
                grupo="",
                fonte=caminho,
                hash_item=self._extrair_hash(pergunta, conteudo_limpo[:2000]),
                metadados={"tipo": "pdf_section", "titulo": titulo.strip()}
            ))

        if not itens and len(texto_completo) > 100:
            primeiras_200 = texto_completo[:200].strip()
            itens.append(ItemParseado(
                pergunta=f"Sobre {os.path.basename(caminho)}",
                conteudo=texto_completo[:2000],
                grupo="",
                fonte=caminho,
                hash_item=self._extrair_hash(os.path.basename(caminho), texto_completo[:2000]),
                metadados={"tipo": "pdf_full", "arquivo": os.path.basename(caminho)}
            ))

        return itens
