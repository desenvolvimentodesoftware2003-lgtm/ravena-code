"""Coleta do pytest — ravena-code.

test_equilibrio_threshold.py nao TEM testes: e um script manual de
varredura de thresholds ("Uso: python tests/test_equilibrio_threshold.py")
que faz coleta CoinGecko e roda o pipeline INTEIRO (LLMs locais em
data/models) no nivel do modulo. Importar no pytest disparava N
inferencias reais e estourava o tempo da suite. Ignorado aqui — rode
na mao quando quiser.
"""

collect_ignore = ["test_equilibrio_threshold.py"]
