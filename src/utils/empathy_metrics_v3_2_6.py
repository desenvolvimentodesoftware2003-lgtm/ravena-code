import numpy as np

class EmpathyMetrics:
    def __init__(self):
        self.coerencia_contextual = [] # % de vezes que repetições foram evitadas
        self.antecipacao_logica = [] # % de acerto na previsão do próximo passo
        self.eficiencia_comando = [] # % de acerto no processamento de comandos concisos

    def registrar_metrica(self, cc: float, al: float, ec: float):
        self.coerencia_contextual.append(cc)
        self.antecipacao_logica.append(al)
        self.eficiencia_comando.append(ec)

    def calcular_mes(self) -> float:
        # Média ponderada conforme o relatório de auditoria
        # Coerência Contextual (CC) tem peso maior na otimização
        if not self.coerencia_contextual:
            return 0.0
        
        avg_cc = np.mean(self.coerencia_contextual)
        avg_al = np.mean(self.antecipacao_logica)
        avg_ec = np.mean(self.eficiencia_comando)
        
        # Pesos ajustados para refletir a necessidade de melhoria na CC
        mes = (avg_cc * 0.40) + (avg_al * 0.30) + (avg_ec * 0.30)
        return mes

    def reset_metrics(self):
        self.coerencia_contextual = []
        self.antecipacao_logica = []
        self.eficiencia_comando = []

if __name__ == "__main__":
    metrics = EmpathyMetrics()
    metrics.registrar_metrica(0.25, 0.90, 0.85) # Valores iniciais do relatório
    print(f"MES Inicial: {metrics.calcular_mes():.2f}%")

    # Simulação de melhoria na Coerência Contextual
    metrics.registrar_metrica(0.70, 0.92, 0.88)
    print(f"MES Após Melhoria: {metrics.calcular_mes():.2f}%")
