#!/usr/bin/env python3
import os
import sys
import time
import logging
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "logs", "ingestao_wikipedia.log"
        ), mode="a", encoding="utf-8")
    ]
)

logger = logging.getLogger("ingestao_wikipedia")

from src.core.alimentacao.parsers_externos.wikipedia_pipeline import WikipediaPipeline
from src.core.alimentacao.parsers_externos.wikipedia_embedder import WikipediaEmbedder
from src.core.alimentacao.alimentador import Alimentador

MODO_INFO = "info"
MODO_DOWNLOAD = "download"
MODO_PROCESSAR = "processar"
MODO_API = "api"
MODO_STATUS = "status"
MODO_INDEXAR = "indexar"
MODO_BUSCAR = "buscar"

LINGUAS_SUPORTADAS = {
    "pt": "Portugues", "en": "Ingles", "es": "Espanhol",
    "fr": "Frances", "de": "Alemao", "it": "Italiano",
    "ja": "Japones", "zh": "Chines", "ru": "Russo", "ar": "Arabe",
}

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Prioridade 6 - Pipeline Wikipedia para LLM privada",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python scripts/ingestao_wikipedia.py info
  python scripts/ingestao_wikipedia.py download
  python scripts/ingestao_wikipedia.py processar --max-artigos 100
  python scripts/ingestao_wikipedia.py processar --categorias "Ciencia,Tecnologia"
  python scripts/ingestao_wikipedia.py processar --max-artigos 500 --caminho-dump data/wikipedia/pt/wiki-latest.xml.bz2
  python scripts/ingestao_wikipedia.py api --topicos "Inteligencia artificial,Python,Brasil"
  python scripts/ingestao_wikipedia.py status
  python scripts/ingestao_wikipedia.py indexar
  python scripts/ingestao_wikipedia.py buscar "o que e astronomia" --top-k 5
        """
    )
    parser.add_argument("modo", choices=[MODO_INFO, MODO_DOWNLOAD, MODO_PROCESSAR,
                                          MODO_API, MODO_STATUS, MODO_INDEXAR, MODO_BUSCAR],
                        help="Modo de operacao")
    parser.add_argument("--lingua", default="pt", choices=list(LINGUAS_SUPORTADAS.keys()),
                        help="Lingua do Wikipedia")
    parser.add_argument("--caminho-dump", help="Caminho do dump .xml.bz2 (padrao: data/wikipedia/<lingua>/... )")
    parser.add_argument("--max-artigos", type=int, default=None, help="Limite de artigos (padrao: todos)")
    parser.add_argument("--categorias", help="Filtrar por categorias (separadas por virgula)")
    parser.add_argument("--topicos", help="Topicos para buscar via API (separados por virgula)")
    parser.add_argument("--projeto-raiz", default=None, help="Raiz do projeto (detectado)")
    parser.add_argument("--top-k", type=int, default=5, help="Numero de resultados (buscar)")
    parser.add_argument("--modelo", default="paraphrase-multilingual-MiniLM-L12-v2",
                        help="Modelo de embedding (indexar/buscar)")
    parser.add_argument("--colecao", default="wikipedia_pt",
                        help="Colecao ChromaDB (indexar/buscar)")
    parser.add_argument("consulta", nargs="?", default=None,
                        help="Texto da consulta (modo buscar)")

    args = parser.parse_args()
    projeto_raiz = args.projeto_raiz or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    pipeline = WikipediaPipeline(projeto_raiz, lingua=args.lingua)

    if args.modo == MODO_INFO:
        info = pipeline.info_dump()
        print(f"\n{'='*60}")
        print(f"Wikipedia Dump - {LINGUAS_SUPORTADAS.get(args.lingua, args.lingua)}")
        print(f"{'='*60}")
        print(f"Dumps disponiveis: {info['dumps_disponiveis']}")
        print(f"Dump principal: {info['dump_principal']}")
        if info['tamanho_estimado_gb']:
            print(f"Tamanho estimado: {info['tamanho_estimado_gb']} GB")
        print(f"Diretorio de saida: {info['diretorio_saida']}")
        print()

    elif args.modo == MODO_DOWNLOAD:
        caminho = pipeline.baixar_dump()
        if caminho:
            tamanho_mb = os.path.getsize(caminho) / (1024 * 1024)
            print(f"\nDump baixado: {caminho}")
            print(f"Tamanho: {tamanho_mb:.0f} MB")
            print(f"Use: python scripts/ingestao_wikipedia.py processar --caminho-dump \"{caminho}\"")
        else:
            logger.error("Falha no download")

    elif args.modo == MODO_PROCESSAR:
        caminho_dump = args.caminho_dump
        if not caminho_dump:
            caminho_dump = os.path.join(projeto_raiz, "data", "wikipedia", args.lingua,
                                        f"{args.lingua}wiki-latest-pages-articles.xml.bz2")
            if not os.path.exists(caminho_dump):
                logger.error(f"Dump nao encontrado: {caminho_dump}")
                logger.error("Baixe primeiro: python scripts/ingestao_wikipedia.py download")
                return

        categorias = [c.strip() for c in args.categorias.split(",")] if args.categorias else None

        if categorias:
            print(f"Filtrando categorias: {categorias}")
        if args.max_artigos:
            print(f"Modo limitado: {args.max_artigos} artigos")
        else:
            resp = input("Processar TODOS os artigos? (s/N): ")
            if resp.lower() != "s":
                return

        print(f"Processando dump: {caminho_dump}")
        inicio = time.time()
        primeiro_jsonl = pipeline.processar_artigos_para_jsonl(
            caminho_dump=caminho_dump,
            max_artigos=args.max_artigos,
            categorias_filtro=categorias
        )
        duracao = time.time() - inicio
        manifest = pipeline.carregar_manifest()
        if manifest:
            print(f"\n{'='*50}")
            print(f"PROCESSAMENTO CONCLUIDO")
            print(f"Artigos processados: {manifest['total_artigos_processados']}")
            print(f"Chunks gerados: {manifest['total_chunks_gerados']}")
            print(f"Tempo: {manifest['duracao_segundos']}s")
            print(f"Velocidade: {manifest['chunks_por_segundo']} chunks/s")
            print(f"Diretorio: {os.path.dirname(primeiro_jsonl)}")
            print(f"Arquivos: {len(pipeline.listar_jsonl_processados())} JSONL")
            print(f"{'='*50}")

    elif args.modo == MODO_API:
        if not args.topicos:
            logger.error("Informe --topicos separados por virgula")
            return
        topicos = [t.strip() for t in args.topicos.split(",")]
        print(f"Buscando {len(topicos)} topicos via API...")
        caminho = pipeline.buscar_e_processar_topicos_api(topicos)
        print(f"Salvo em: {caminho}")

    elif args.modo == MODO_STATUS:
        manifest = pipeline.carregar_manifest()
        arquivos = pipeline.listar_jsonl_processados()
        print(f"\n{'='*60}")
        print(f"STATUS - Wikipedia {args.lingua.upper()}")
        print(f"{'='*60}")
        print(f"Diretorio: {pipeline._saida}")
        print(f"Arquivos JSONL: {len(arquivos)}")
        for arq in arquivos:
            tamanho = os.path.getsize(arq) / (1024 * 1024)
            print(f"  {os.path.basename(arq)} ({tamanho:.1f} MB)")
        if manifest:
            print(f"\nUltimo processamento:")
            print(f"  Artigos: {manifest.get('total_artigos_processados', '?')}")
            print(f"  Chunks: {manifest.get('total_chunks_gerados', '?')}")
            print(f"  Data: {manifest.get('timestamp', '?')}")
        print()

    elif args.modo == MODO_INDEXAR:
        embedder = WikipediaEmbedder(modelo=args.modelo, colecao=args.colecao)
        status_antes = embedder.status()
        print(f"\nColecao antes: {status_antes}")
        print(f"\nIndexando JSONLs de: {pipeline._saida}")
        resultado = embedder.indexar_todos(pipeline._saida)
        status_depois = embedder.status()
        print(f"\n{'='*50}")
        print(f"INDEXACAO CONCLUIDA")
        print(f"Lidos: {resultado['lidos']}")
        print(f"Inseridos: {resultado['inseridos']}")
        print(f"Ignorados (ja existentes): {resultado['ignorados']}")
        print(f"Total na colecao: {status_depois.get('total_documentos', '?')}")
        print(f"{'='*50}")

    elif args.modo == MODO_BUSCAR:
        if not args.consulta:
            logger.error("Informe o texto da consulta como argumento")
            print('Exemplo: python scripts/ingestao_wikipedia.py buscar "o que e astronomia" --top-k 5')
            return
        embedder = WikipediaEmbedder(modelo=args.modelo, colecao=args.colecao)
        print(f"\nBuscando: '{args.consulta}'")
        print(f"{'='*60}")
        resultados = embedder.buscar(args.consulta, top_k=args.top_k)
        if not resultados:
            print("Nenhum resultado encontrado.")
            return
        for i, r in enumerate(resultados, 1):
            meta = r.get("metadata", {})
            distancia = r.get("distancia", 0)
            score = max(0, 1 - distancia)
            print(f"\n--- Resultado {i} (relevancia: {score:.2f}) ---")
            print(f"  Titulo: {meta.get('titulo', '?')}")
            print(f"  Secao: {meta.get('secao', '?')}")
            print(f"  Categorias: {meta.get('categorias', '')}")
            pergunta = meta.get("pergunta", "")
            if pergunta:
                print(f"  Pergunta: {pergunta}")
            doc = r.get("documento", "")
            if doc:
                print(f"  Texto: {doc[:300]}...")
        print(f"\n{len(resultados)} resultados em {args.colecao}")

if __name__ == "__main__":
    main()
