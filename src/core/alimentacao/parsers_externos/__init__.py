from src.core.alimentacao.parsers_externos.wikipedia_parser import WikipediaParser
from src.core.alimentacao.parsers_externos.wikipedia_dump_parser import WikipediaDumpParser, ArtigoWikipedia
from src.core.alimentacao.parsers_externos.wikipedia_pipeline import WikipediaPipeline
from src.core.alimentacao.parsers_externos.wikipedia_embedder import WikipediaEmbedder
from src.core.alimentacao.parsers_externos.arxiv_parser import ArxivParser
from src.core.alimentacao.parsers_externos.datasets_parser import DatasetsParser

__all__ = [
    "WikipediaParser", "WikipediaDumpParser", "ArtigoWikipedia",
    "WikipediaPipeline", "WikipediaEmbedder",
    "ArxivParser", "DatasetsParser"
]
