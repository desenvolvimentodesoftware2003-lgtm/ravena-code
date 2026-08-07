"""
RAVENA AI 3.0.0 — src/security/security_core.py
=============================================
Módulo de Segurança e Blindagem Refatorado.
Implementa Lockdown V2.2, SecurityLayer (Zero Trust) e Auditoria.
Baseado em: engine_patch_seguranca_ia.py e auditor.py (v3).
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field

# Configuração de Logging
logger = logging.getLogger("ravena.security_core")

class NivelRisco(Enum):
    BAIXO = "baixo"
    MEDIO = "medio"
    ALTO = "alto"
    CRITICO = "critico"

@dataclass
class AlertaSeguranca:
    id: str
    tipo: str
    descricao: str
    severidade: NivelRisco
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    contexto: Dict[str, Any] = field(default_factory=dict)

class SecurityLayer:
    """Implementa Zero Trust e validação profunda de operações."""
    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.whitelist_dominios = ["oraclecloud.com", "github.com", "openai.com", "google.com"]
        self.blacklist_termos = ["system", "```", "INSTRUÇÃO:", "prompt_original", "bypass", "jailbreak"]

    def validar_operacao(self, contexto: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Valida uma operação contra políticas de segurança."""
        erros = []
        
        # 1. Validação de Usuário e Permissão
        usuario = contexto.get("usuario", "desconhecido")
        if usuario == "desconhecido":
            erros.append("Usuário não autenticado.")
            
        # 2. Verificação de Injeção e Jailbreak no Conteúdo
        conteudo = contexto.get("conteudo", "").lower()
        for termo in self.blacklist_termos:
            if termo.lower() in conteudo:
                erros.append(f"Termo proibido detectado: {termo}")
                
        # 3. Validação de Whitelist de Rede (se houver URL)
        url = contexto.get("url", "")
        if url:
            dominio_valido = any(d in url for d in self.whitelist_dominios)
            if not dominio_valido:
                erros.append(f"URL fora da whitelist: {url}")
                
        sucesso = len(erros) == 0
        return sucesso, erros

class LockdownV22:
    """Protocolo de blindagem máxima para respostas da IA."""
    def __init__(self):
        self.juiz = None # Será injetado ou inicializado
        
    def filtrar_saida(self, resposta: str) -> str:
        """Aplica filtros obrigatórios antes de entregar ao usuário."""
        # Remover padrões sensíveis
        resposta = re.sub(r"(?i)system prompt|instrução original", "[REDACTED]", resposta)
        # Bloquear reprodução de código malicioso simulado
        if "rm -rf /" in resposta or "format c:" in resposta:
            logger.warning("Tentativa de saída de comando perigoso detectada!")
            return "ERRO: Ação bloqueada pelo Lockdown V2.2."
            
        return resposta

class ValidadorVeracidade:
    """Validador de Veracidade de Elite (v3.1.0) - Foco em Precisão 0.90+."""
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        # Lógica Bruta de Elite: Entidades e Relacionamentos Críticos
        self.entidades_mestre = {
            "NUCLEO_OMEGA": ["orquestrador", "convergência", "central", "omega core"],
            "RAVENA_V3": ["v3.0.0", "modular", "microsserviços", "arquitetura"],
            "SEGURANCA": ["zero trust", "lockdown v2.2", "blindagem", "auditoria"],
            "RAG_EXPANSION": ["chromadb", "embeddings", "base de conhecimento", "contexto"]
        }

    def validar_fato(self, fato: str, contexto_rag: List[Dict[str, Any]]) -> Tuple[bool, float, str]:
        """Validação de Triplo Cruzamento: Entidades + RAG + Proximidade."""
        logger.info(f"Iniciando Validação de Elite: {fato[:50]}...")
        
        if not contexto_rag:
            return False, 0.0, "ERRO: Base de conhecimento inacessível."

        fato_lower = fato.lower()
        total_contexto = " ".join([doc.get('conteudo', '').lower() for doc in contexto_rag])
        
        # 1. Validação de Entidades Críticas (NER Simplificado)
        entidades_presentes = 0
        matches_entidades = 0
        for entidade, sinonimos in self.entidades_mestre.items():
            if any(s in fato_lower for s in sinonimos):
                entidades_presentes += 1
                if any(s in total_contexto for s in sinonimos):
                    matches_entidades += 1
        
        score_entidades = (matches_entidades / entidades_presentes) if entidades_presentes > 0 else 1.0
        
        # 2. Validação de Proximidade e Coerência (N-Grams)
        palavras_chave = [p for p in re.findall(r'\w+', fato_lower) if len(p) > 3]
        matches_rag = sum(1 for p in palavras_chave if p in total_contexto)
        score_rag = (matches_rag / len(palavras_chave)) if palavras_chave else 0.0
        
        # 3. Validação de Integridade de Frase (Sequência de Termos)
        # Verifica se pelo menos um bigrama (par de palavras) do fato existe no contexto
        bigramas_fato = [" ".join(palavras_chave[i:i+2]) for i in range(len(palavras_chave)-1)]
        matches_sequencia = sum(1 for b in bigramas_fato if b in total_contexto)
        score_sequencia = (matches_sequencia / len(bigramas_fato)) if bigramas_fato else 1.0

        # Cálculo Final de Elite (Pesos: 35% Entidades, 35% RAG, 30% Sequência/Coerência)
        score_final = (score_entidades * 0.35) + (score_rag * 0.35) + (score_sequencia * 0.30)
        
        # Bônus de Densidade para fatos bem fundamentados
        if len(fato) > 100:
            score_final = min(score_final + 0.05, 1.0)

        confiavel = score_final >= self.threshold
        status = "✅ ELITE" if score_final >= 0.90 else ("⚠️ CONFIÁVEL" if confiavel else "❌ REJEITADO")
        
        detalhes = f"{status} | Score: {score_final:.2f} [Entidades: {score_entidades:.2f}, RAG: {score_rag:.2f}, Seq: {score_sequencia:.2f}]"
        
        return confiavel, score_final, detalhes

class AuditorCore:
    """Auditoria em tempo real de todas as ações do sistema."""
    def __init__(self, log_path: str = "./logs/auditoria/"):
        self.log_path = log_path
        os.makedirs(log_path, exist_ok=True)
        
    def registrar_acao(self, acao: str, resultado: str, usuario: str = "sistema"):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "usuario": usuario,
            "acao": acao,
            "resultado": resultado
        }
        log_file = os.path.join(self.log_path, f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl")
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        logger.info(f"AUDIT: {acao} por {usuario} - {resultado}")
