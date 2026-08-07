"""
RISK_MANAGER — Módulo de Gestão de Risco Dinâmica (Fase 3)
=========================================================
Implementa o Protocolo Zero Trust e blindagem de capital para o 
Ravena Trading Bot.

Funcionalidades:
  - Validação de saldo disponível antes de cada trade.
  - Limite de alocação máxima por trade (% do capital total).
  - Protocolo Zero Trust: Exige assinatura de 'Juiz' (confirmação extra) 
    para ordens acima de um limite crítico.
  - Verificação de exposição total (Drawdown Control).
"""

import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("ravena.risk_manager")

class RiskManager:
    """
    Gerenciador de Risco Dinâmico com Protocolo Zero Trust.
    """
    
    def __init__(
        self, 
        max_allocation_pct: float = 0.02,  # Reduzido para 2% no Capital Real
        critical_threshold_usdt: float = 200.0, # Reduzido para 200 USDT para maior segurança
        max_drawdown_pct: float = 0.05     # Reduzido para 5% (Proteção Conservadora)
    ):
        self.max_allocation_pct = max_allocation_pct
        self.critical_threshold_usdt = critical_threshold_usdt
        self.max_drawdown_pct = max_drawdown_pct
        self.initial_balance = None
        
    def set_initial_balance(self, balance: float):
        """Define o saldo inicial para controle de drawdown."""
        if self.initial_balance is None:
            self.initial_balance = balance
            logger.info(f"[RISK] Saldo inicial definido: {balance} USDT")

    def validate_trade(
        self, 
        symbol: str, 
        action: str, 
        qty: float, 
        price: float, 
        current_balance: float
    ) -> Tuple[bool, str]:
        """
        Valida se um trade pode ser executado baseado nos protocolos de risco.
        Retorna (is_allowed, reason).
        """
        # 1. Verificar se o saldo inicial foi definido
        if self.initial_balance is None:
            self.set_initial_balance(current_balance)
            
        # 2. Calcular valor total da ordem em USDT
        order_value = qty * price
        
        # 3. Verificar se há saldo suficiente
        if order_value > current_balance:
            return False, f"Saldo insuficiente. Necessário: {order_value:.2f}, Disponível: {current_balance:.2f}"
            
        # 4. Verificar limite de alocação máxima (% do capital)
        max_allowed_value = current_balance * self.max_allocation_pct
        if order_value > max_allowed_value:
            return False, f"Alocação excede limite de {self.max_allocation_pct*100}%. Máximo permitido: {max_allowed_value:.2f} USDT"
            
        # 5. Verificar Protocolo Zero Trust (Assinatura do Juiz)
        if order_value > self.critical_threshold_usdt:
            # Em um cenário real, isso poderia ser uma confirmação manual ou via outro módulo IA (Omega)
            # Por enquanto, logamos como uma 'assinatura pendente' que bloqueia ordens grandes
            logger.warning(f"[ZERO TRUST] Ordem de {order_value:.2f} USDT excede limite crítico de {self.critical_threshold_usdt} USDT.")
            return False, "PROTOCOLO ZERO TRUST: Ordem exige assinatura do Módulo Juiz (Valor Crítico Excedido)"
            
        # 6. Verificar Drawdown Máximo
        current_drawdown = (self.initial_balance - current_balance) / self.initial_balance
        if current_drawdown > self.max_drawdown_pct:
            return False, f"DRAWDOWN CRÍTICO: {current_drawdown*100:.2f}% (Limite: {self.max_drawdown_pct*100}%)"
            
        logger.info(f"[RISK] Trade VALIDADO: {action} {qty} {symbol} ({order_value:.2f} USDT)")
        return True, "Validado"

if __name__ == "__main__":
    # Teste simples do RiskManager
    risk = RiskManager(max_allocation_pct=0.1, critical_threshold_usdt=1000)
    
    # Simular validação
    allowed, reason = risk.validate_trade("BTCUSDT", "BUY", 0.01, 60000, 5000)
    print(f"Trade 1 (600 USDT): Allowed={allowed}, Reason={reason}")
    
    allowed, reason = risk.validate_trade("BTCUSDT", "BUY", 0.02, 60000, 5000)
    print(f"Trade 2 (1200 USDT - Zero Trust): Allowed={allowed}, Reason={reason}")
    
    allowed, reason = risk.validate_trade("BTCUSDT", "BUY", 0.1, 60000, 5000)
    print(f"Trade 3 (6000 USDT - Saldo): Allowed={allowed}, Reason={reason}")
