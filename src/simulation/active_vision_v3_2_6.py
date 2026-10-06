"""
ACTIVE_VISION — Módulo de Visão Ativa para o Ravena Trading Bot
==============================================================
Este módulo estende o vision_module.py da Ravena AI para focar na 
validação visual de sinais de trade através de capturas de tela 
de dashboards (Bybit/TradingView).

Funcionalidades:
  - Captura de tela (Headless via Xvfb ou Desktop).
  - Detecção de elementos de interface (Botões Buy/Sell, Preço).
  - Análise de cor de velas (Verde/Vermelho) para confirmação de tendência.
  - Cross-check com sinais da API.
"""

import cv2
import numpy as np
import mss
import os
import logging
from PIL import Image
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Importar o módulo base da Ravena
from vision_module import ModuloPercepçãoVisual, TipoEntradaVisual, NivelAmeaca

logger = logging.getLogger("ravena.active_vision")

class ActiveVision:
    def __init__(self, display=None):
        """
        Inicializa a visão ativa.
        display: O display X11 a ser usado (padrão None para não forçar).
        """
        self.display = display or os.environ.get("DISPLAY")
        if self.display:
            os.environ["DISPLAY"] = self.display
        self.base_vision = ModuloPercepçãoVisual()
        self.screenshot_dir = "screenshots"
        
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

    def capture_screen(self, filename: str = "latest_dashboard.png") -> Optional[str]:
        """Captura a tela atual e salva em arquivo."""
        try:
            path = os.path.join(self.screenshot_dir, filename)
            with mss.mss() as sct:
                # Captura o monitor principal
                sct.shot(output=path)
            logger.info(f"Captura de tela salva em: {path}")
            return path
        except Exception as e:
            logger.error(f"Erro ao capturar tela: {e}")
            return None

    def analyze_trend_visual(self, image_path: str) -> Dict[str, Any]:
        """
        Analisa visualmente a tendência baseada nas cores predominantes 
        (simulação de detecção de velas).
        """
        img = cv2.imread(image_path)
        if img is None:
            return {"trend": "UNKNOWN", "confidence": 0.0}

        # Converter para HSV para melhor detecção de cores
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Definir ranges para Verde (Vela de Alta) e Vermelho (Vela de Baixa)
        # Nota: Estes ranges podem precisar de ajuste dependendo do tema do dashboard
        lower_green = np.array([40, 40, 40])
        upper_green = np.array([80, 255, 255])
        
        lower_red1 = np.array([0, 70, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 70, 50])
        upper_red2 = np.array([180, 255, 255])

        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

        green_pixels = cv2.countNonZero(mask_green)
        red_pixels = cv2.countNonZero(mask_red)
        
        total_pixels = img.shape[0] * img.shape[1]
        
        logger.info(f"Pixels Verdes: {green_pixels}, Pixels Vermelhos: {red_pixels}")

        if green_pixels > red_pixels * 1.2:
            trend = "BULLISH"
            confidence = min(0.9, green_pixels / (green_pixels + red_pixels))
        elif red_pixels > green_pixels * 1.2:
            trend = "BEARISH"
            confidence = min(0.9, red_pixels / (green_pixels + red_pixels))
        else:
            trend = "NEUTRAL"
            confidence = 0.5

        return {
            "trend": trend,
            "confidence": confidence,
            "green_ratio": green_pixels / total_pixels,
            "red_ratio": red_pixels / total_pixels
        }

    def validate_signal(self, api_signal: str, image_path: str) -> Tuple[bool, float]:
        """
        Valida o sinal da API contra a análise visual.
        Retorna (is_valid, visual_confidence).
        """
        analysis = self.analyze_trend_visual(image_path)
        visual_trend = analysis["trend"]
        visual_conf = analysis["confidence"]

        is_valid = False
        if api_signal == "BUY" and visual_trend == "BULLISH":
            is_valid = True
        elif api_signal == "SELL" and visual_trend == "BEARISH":
            is_valid = True
        elif api_signal == "HOLD":
            is_valid = True
            
        logger.info(f"Validação Visual: API={api_signal}, Visão={visual_trend}, Válido={is_valid}")
        return is_valid, visual_conf

if __name__ == "__main__":
    # Teste básico
    logging.basicConfig(level=logging.INFO)
    vision = ActiveVision()
    # Como não temos um dashboard real aberto, o teste apenas verifica se o código roda
    print("Módulo ActiveVision carregado com sucesso.")
