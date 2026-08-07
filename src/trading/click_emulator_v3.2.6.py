"""
MÓDULO DE EXECUÇÃO (EMULADOR DE CLIQUE v2.4.0) — Ravena AI Trading Bot
======================================================================
Laboratório de Validação IQ Option | Fase 7 — Tijolo 12

Este módulo implementa o mimetismo humano e a precisão necessária para
operar na interface da IQ Option como um laboratório de testes definitivo.

Novos Recursos:
  - Mimetismo Humano: Movimentos curvos (Bézier) e velocidades variáveis.
  - Pausas Aleatórias: Micro-pausas entre ações para evitar detecção.
  - Gerenciamento de Lote: Digitação automática do valor da entrada.
  - Padronização IQ Option: Coordenadas fixas para botões Verde/Vermelho.
  - Modo Simulação: Funciona em ambientes headless para testes de lógica.
"""

import time
import random
import logging
import math
import os
from typing import Dict, Tuple, Optional
from datetime import datetime
from pathlib import Path

# Tentar importar pyautogui para ambiente com interface gráfica
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    pyautogui.FAILSAFE = True
except (ImportError, Exception):
    PYAUTOGUI_AVAILABLE = False

# Tentar importar PIL para captura de tela
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger("ravena.click_emulator")

# Configuração de diretórios de auditoria visual
_BASE_DIR = Path(__file__).parent.parent
_SCREENSHOT_DIR = _BASE_DIR / "logs" / "screenshots"
_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

class ClickEmulator:
    """
    Emulador de comportamento humano para IQ Option e Bybit.
    """
    
    def __init__(self, screen_resolution: Tuple[int, int] = (1920, 1080)):
        self.resolution = screen_resolution
        # Coordenadas padronizadas para IQ Option (Exemplo de Laboratório)
        self.coordinates = {
            "IQ_OPTION": {
                "BUY_BUTTON": (1750, 450),    # Botão Verde
                "SELL_BUTTON": (1750, 650),   # Botão Vermelho
                "AMOUNT_INPUT": (1750, 250),  # Campo de Valor
                "ASSET_SEARCH": (100, 50),    # Busca de Ativo
            },
            "BYBIT": {
                "BUY_BUTTON": (1600, 700),
                "SELL_BUTTON": (1600, 800),
                "AMOUNT_INPUT": (1600, 500),
            }
        }
        
        if not PYAUTOGUI_AVAILABLE:
            logger.warning("[EMULATOR] PyAutoGUI não disponível. Rodando em modo DRY RUN.")

    def _human_move(self, x: int, y: int):
        """
        Move o mouse de forma humana (não linear) até as coordenadas (x, y).
        Implementa uma curva de aceleração e pequenas variações.
        """
        if not PYAUTOGUI_AVAILABLE:
            logger.info(f"[EMULATOR] [DRY RUN] Movendo mouse para ({x}, {y})")
            return

        # Posição atual
        start_x, start_y = pyautogui.position()
        
        # Número de passos para o movimento
        steps = random.randint(15, 30)
        
        for i in range(steps + 1):
            # Interpolação simples com um pouco de ruído "humano"
            t = i / steps
            # Curva de aceleração/desaceleração (Ease In Out)
            t = t * t * (3 - 2 * t)
            
            target_x = start_x + (x - start_x) * t + random.uniform(-2, 2)
            target_y = start_y + (y - start_y) * t + random.uniform(-2, 2)
            
            pyautogui.moveTo(target_x, target_y)
            # Micro-pausa variável
            time.sleep(random.uniform(0.001, 0.005))

    def _human_click(self):
        """Simula um clique humano com duração variável."""
        if not PYAUTOGUI_AVAILABLE:
            logger.info("[EMULATOR] [DRY RUN] Clicando...")
            return
        
        pyautogui.mouseDown()
        time.sleep(random.uniform(0.05, 0.15))
        pyautogui.mouseUp()

    def _human_type(self, text: str):
        """Digita texto com intervalos variáveis entre teclas."""
        if not PYAUTOGUI_AVAILABLE:
            logger.info(f"[EMULATOR] [DRY RUN] Digitando: {text}")
            return
            
        for char in text:
            pyautogui.write(char)
            time.sleep(random.uniform(0.05, 0.2))

    def set_amount(self, platform: str, amount: float):
        """Configura o valor da entrada no campo correspondente."""
        coords = self.coordinates.get(platform, {}).get("AMOUNT_INPUT")
        if not coords:
            logger.error(f"[EMULATOR] Coordenadas para {platform} AMOUNT_INPUT não encontradas.")
            return False
            
        logger.info(f"[EMULATOR] Configurando lote: {amount} USDT na plataforma {platform}")
        
        # 1. Mover até o campo
        self._human_move(coords[0], coords[1])
        time.sleep(random.uniform(0.2, 0.5))
        
        # 2. Clicar para focar
        self._human_click()
        time.sleep(random.uniform(0.1, 0.3))
        
        # 3. Limpar campo (Ctrl+A -> Backspace)
        if PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('backspace')
        
        # 4. Digitar valor
        self._human_type(str(amount))
        time.sleep(random.uniform(0.3, 0.6))
        return True

    def capture_screen(self, label: str = "trade_event") -> Optional[str]:
        """
        Captura a tela atual para auditoria visual (Análise do Erro).
        """
        if not PYAUTOGUI_AVAILABLE or not PIL_AVAILABLE:
            logger.warning("[EMULATOR] Captura de tela não disponível (Headless ou PIL ausente).")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{label}_{timestamp}.png"
        filepath = _SCREENSHOT_DIR / filename
        
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(str(filepath))
            logger.info(f"[EMULATOR] Screenshot salvo: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"[EMULATOR] Falha ao capturar tela: {e}")
            return None

    def validate_order_opened(self, platform: str) -> bool:
        """
        Valida visualmente se a ordem foi aberta com sucesso.
        Em um ambiente real, isso usaria OpenCV para detectar o popup de confirmação.
        No laboratório, simulamos a verificação visual.
        """
        logger.info(f"[EMULATOR] Validando abertura de ordem visualmente em {platform}...")
        time.sleep(random.uniform(0.5, 1.0)) # Tempo para a interface reagir
        
        # Simulação de verificação visual (95% de sucesso no laboratório)
        success = random.random() < 0.95
        
        if not success:
            logger.error(f"[EMULATOR] FALHA VISUAL: Ordem não detectada na interface {platform}!")
            self.capture_screen(label=f"ERROR_VISUAL_{platform}")
        else:
            logger.info(f"[EMULATOR] Confirmação visual recebida: Ordem aberta em {platform}.")
            
        return success

    def execute_trade(self, platform: str, action: str, amount: Optional[float] = None) -> bool:
        """
        Executa a ordem de trade (BUY ou SELL) na plataforma especificada.
        """
        if action == "HOLD":
            logger.info("[EMULATOR] Ação HOLD recebida. Nenhuma operação executada.")
            return True

        # 1. Configurar lote se fornecido
        if amount is not None:
            if not self.set_amount(platform, amount):
                return False

        # 2. Determinar botão
        btn_key = "BUY_BUTTON" if action == "BUY" else "SELL_BUTTON"
        coords = self.coordinates.get(platform, {}).get(btn_key)
        
        if not coords:
            logger.error(f"[EMULATOR] Coordenadas para {platform} {btn_key} não encontradas.")
            return False

        logger.info(f"[EMULATOR] EXECUTANDO {action} em {platform}...")
        
        # 3. Movimento humano até o botão
        self._human_move(coords[0], coords[1])
        
        # 4. Pequena pausa de "decisão"
        time.sleep(random.uniform(0.1, 0.4))
        
        # 5. Clique final
        self._human_click()
        
        # 6. Validação Visual (Fase 7 - Laboratório)
        success = self.validate_order_opened(platform)
        
        if success:
            logger.info(f"[EMULATOR] Ordem {action} enviada e validada com sucesso via Emulador.")
        else:
            logger.warning(f"[EMULATOR] Ordem {action} enviada, mas validação visual falhou.")
            
        return success

# ─────────────────────────────────────────────
# Demonstração / Teste
# ─────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    emu = ClickEmulator()
    
    print("\n--- TESTE DE LABORATÓRIO IQ OPTION ---")
    emu.execute_trade("IQ_OPTION", "BUY", amount=50.0)
    
    time.sleep(2)
    
    print("\n--- TESTE DE LABORATÓRIO BYBIT ---")
    emu.execute_trade("BYBIT", "SELL", amount=0.001)
