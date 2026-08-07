"""
RAVENA AI v3.2.8-Alpha — HEURISTIC & ANOMALY LAYER (Semana 3)
============================================================
Objetivo: Detectar anomalias estruturais e comportamentais em diretórios.
"""
import os
import time

class HeuristicLayer:
    def __init__(self):
        self.suspicious_extensions = [".exe", ".sh", ".bat", ".dll", ".so"]
        self.entropy_threshold = 4.5 # Exemplo de limiar para detecção de arquivos compactados/criptografados

    def analisar_diretorio_comportamental(self, path):
        """
        Analisa a 'saúde' e o comportamento de um diretório.
        """
        print(f"[HEURÍSTICA] Analisando comportamento do diretório: {path}")
        anomalias = []
        
        # Simulação de análise de arquivos suspeitos
        # Em um ambiente real, varreria o sistema de arquivos
        files_to_check = ["main.go", "config.yaml", "hidden_script.sh", "data.bin"]
        
        for f in files_to_check:
            if any(f.endswith(ext) for ext in self.suspicious_extensions):
                anomalias.append(f"Arquivo com extensão perigosa detectado: {f}")
            
            if f.startswith("."):
                anomalias.append(f"Arquivo oculto detectado: {f}")

        # Heurística de 'Idade' (Simulada)
        # Arquivos criados muito recentemente em pastas críticas são suspeitos
        anomalias.append("Alerta: Modificações recentes detectadas em arquivos de configuração.")

        return {
            "score_anomalia": len(anomalias) * 10,
            "lista_anomalias": anomalias,
            "veredito": "SUSPEITO" if len(anomalias) > 2 else "NORMAL"
        }

if __name__ == "__main__":
    layer = HeuristicLayer()
    res = layer.analisar_diretorio_comportamental("/home/ubuntu/project")
    import json
    print(json.dumps(res, indent=4))
