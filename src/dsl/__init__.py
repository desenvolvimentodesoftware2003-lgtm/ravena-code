"""DSL Interpreter: linguagem de comandos para interagir com todos os modulos da Ravena AIM.

Permite emitir comandos estruturados como:
  AGENT SearchAgent "find news about Bitcoin"
  MEMORY STORE episodic "User asked about price"
  TRADE SIMULATE BUY BTC 1000
  SENSOR RUN FileSensor
  VISION ANALYZE log "ERROR 403 from 10.0.0.1"
  ANALYTICS health
  SEARCH "latest crypto news"
  RAG QUERY "What is Bitcoin?"
  HELP

Disponibiliza:
- DSLInterpreter: interpretador principal que executa comandos no sistema
- DSLParser: parser que converte texto em AST de comandos
- CommandAST: tipos de nos da arvore sintatica
"""

from .dsl_interpreter_v3_2_6 import DSLInterpreter, DSLParser, CommandType, CommandAST

__all__ = ["DSLInterpreter", "DSLParser", "CommandType", "CommandAST"]
