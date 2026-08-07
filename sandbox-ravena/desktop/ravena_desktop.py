#!/usr/bin/env python3
# ============================================
# RAVENA DESKTOP - Interface eDEX-UI Style
# Ravena Security Sandbox
# ============================================
# Interface estilo sci-fi para terminal
# com Terra 3D, monitores e ferramentas
# ============================================

import os
import sys
import json
import time
import signal
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple

# ============================================
# Cores ANSI (eDEX-UI Style)
# ============================================

class Cores:
    """Cores estilo eDEX-UI"""
    PRETO = '\033[30m'
    VERMELHO = '\033[31m'
    VERDE = '\033[32m'
    AMARELO = '\033[33m'
    AZUL = '\033[34m'
    MAGENTA = '\033[35m'
    CIANO = '\033[36m'
    BRANCO = '\033[37m'
    
    # Cores brilhantes (neon)
    NEON_VERDE = '\033[92m'
    NEON_AZUL = '\033[94m'
    NEON_CIANO = '\033[96m'
    NEON_AMARELO = '\033[93m'
    NEON_VERMELHO = '\033[91m'
    NEON_MAGENTA = '\033[95m'
    
    # Fundo
    FUNDO_PRETO = '\033[40m'
    FUNDO_AZUL = '\033[44m'
    FUNDO_VERMELHO = '\033[41m'
    
    # Estilos
    NEGRITO = '\033[1m'
    SUBLINHADO = '\033[4m'
    PISCANDO = '\033[5m'
    
    # Resetar
    RESET = '\033[0m'

# ============================================
# Classe Terminal
# ============================================

class Terminal:
    """Gerencia o terminal"""
    
    def __init__(self):
        self.largura = 80
        self.altura = 24
        self.cursor_visivel = False
    
    def limpar(self):
        """Limpa a tela"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def mover(self, x: int, y: int):
        """Move o cursor para posição"""
        print(f"\033[{y};{x}H", end='')
    
    def ocultar_cursor(self):
        """Oculta o cursor"""
        print("\033[?25l", end='')
    
    def mostrar_cursor(self):
        """Mostra o cursor"""
        print("\033[?25h", end='')
    
    def obter_tamanho(self):
        """Obtém tamanho do terminal"""
        try:
            import shutil
            self.largura, self.altura = shutil.get_terminal_size()
        except:
            self.largura = 80
            self.altura = 24

# ============================================
# Classe Terra 3D
# ============================================

class Terra3D:
    """Globo terrestre 3D ASCII"""
    
    def __init__(self, centro_x: int, centro_y: int, raio: int):
        self.centro_x = centro_x
        self.centro_y = centro_y
        self.raio = raio
        self.rotacao = 0
        self.países = self._carregar_países()
    
    def _carregar_países(self) -> List[Dict]:
        """Carrega dados dos países"""
        return [
            {'nome': 'BR', 'x': -0.3, 'y': 0.2, 'cor': Cores.VERDE},
            {'nome': 'US', 'x': 0.4, 'y': -0.3, 'cor': Cores.AZUL},
            {'nome': 'DE', 'x': 0.6, 'y': -0.2, 'cor': Cores.AMARELO},
            {'nome': 'FR', 'x': 0.5, 'y': -0.15, 'cor': Cores.CIANO},
            {'nome': 'GB', 'x': 0.55, 'y': -0.25, 'cor': Cores.MAGENTA},
            {'nome': 'JP', 'x': 0.8, 'y': -0.1, 'cor': Cores.VERMELHO},
            {'nome': 'AU', 'x': 0.7, 'y': 0.4, 'cor': Cores.AMARELO},
            {'nome': 'CN', 'x': 0.75, 'y': 0.0, 'cor': Cores.VERMELHO},
            {'nome': 'RU', 'x': 0.7, 'y': -0.35, 'cor': Cores.AZUL},
            {'nome': 'IN', 'x': 0.7, 'y': 0.1, 'cor': Cores.AMARELO},
        ]
    
    def desenhar(self) -> List[str]:
        """Desenha o globo"""
        linhas = []
        
        # Fundo do globo
        for y in range(-self.raio, self.raio + 1):
            linha = ''
            for x in range(-self.raio * 2, self.raio * 2 + 1):
                # Calcular distância do centro
                dist_x = x / 2
                dist_y = y
                
                if dist_x**2 + dist_y**2 <= self.raio**2:
                    # Dentro do globo
                    if dist_x**2 + dist_y**2 <= (self.raio - 1)**2:
                        # Interior
                        linha += f"{Cores.NEON_AZUL}░{Cores.RESET}"
                    else:
                        # Borda
                        linha += f"{Cores.NEON_CIANO}▒{Cores.RESET}"
                else:
                    # Fora
                    linha += ' '
            
            linhas.append(linha)
        
        # Adicionar países
        for país in self.países:
            px = int((país['x'] + 1) * self.raio * 2)
            py = int((-país['y'] + 1) * self.raio)
            
            if 0 <= py < len(linhas) and 0 <= px < len(linhas[py]):
                # Substituir caractere pelo nome do país
                linha_lista = list(linhas[py])
                for i, char in enumerate(país['nome']):
                    if px + i < len(linha_lista):
                        linha_lista[px + i] = f"{país['cor']}{char}{Cores.RESET}"
                linhas[py] = ''.join(linha_lista)
        
        return linhas
    
    def atualizar(self):
        """Atualiza rotação"""
        self.rotacao = (self.rotacao + 1) % 360

# ============================================
# Classe Monitor de Sistema
# ============================================

class MonitorSistema:
    """Monitor de recursos do sistema"""
    
    def __init__(self):
        self.cpu = 0.0
        self.ram = 0.0
        self.disco = 0.0
        self.rede_up = 0
        self.rede_down = 0
    
    def atualizar(self):
        """Atualiza métricas"""
        try:
            # CPU
            with open('/proc/stat', 'r') as f:
                linha = f.readline()
                cpu = linha.split()
                total = sum(int(x) for x in cpu[1:])
                idle = int(cpu[4])
                self.cpu = 100 * (1 - idle / total) if total > 0 else 0
            
            # RAM
            with open('/proc/meminfo', 'r') as f:
                for linha in f:
                    if 'MemTotal' in linha:
                        total = int(linha.split()[1])
                    elif 'MemAvailable' in linha:
                        disponivel = int(linha.split()[1])
                        self.ram = 100 * (1 - disponivel / total) if total > 0 else 0
        except:
            # Fallback para sistemas que não têm /proc
            self.cpu = 50.0
            self.ram = 65.0
    
    def desenhar(self, x: int, y: int) -> List[str]:
        """Desenha o monitor"""
        linhas = []
        
        # Título
        linhas.append(f"{Cores.NEON_CIANO}┌─────────────────────┐{Cores.RESET}")
        linhas.append(f"{Cores.NEON_CIANO}│  MONITOR DE SISTEMA │{Cores.RESET}")
        linhas.append(f"{Cores.NEON_CIANO}├─────────────────────┤{Cores.RESET}")
        
        # CPU
        cpu_barra = self._criar_barra(self.cpu)
        linhas.append(f"{Cores.NEON_CIANO}│{Cores.RESET} CPU: {cpu_barra} {self.cpu:5.1f}% {Cores.NEON_CIANO}│{Cores.RESET}")
        
        # RAM
        ram_barra = self._criar_barra(self.ram)
        linhas.append(f"{Cores.NEON_CIANO}│{Cores.RESET} RAM: {ram_barra} {self.ram:5.1f}% {Cores.NEON_CIANO}│{Cores.RESET}")
        
        # Disco
        disco_barra = self._criar_barra(35.0)
        linhas.append(f"{Cores.NEON_CIANO}│{Cores.RESET} DIS: {disco_barra} 35.0% {Cores.NEON_CIANO}│{Cores.RESET}")
        
        linhas.append(f"{Cores.NEON_CIANO}└─────────────────────┘{Cores.RESET}")
        
        return linhas
    
    def _criar_barra(self, porcentagem: float) -> str:
        """Cria barra de progresso"""
        tamanho = 10
        preenchido = int(porcentagem / 100 * tamanho)
        
        if porcentagem > 80:
            cor = Cores.NEON_VERMELHO
        elif porcentagem > 60:
            cor = Cores.NEON_AMARELO
        else:
            cor = Cores.NEON_VERDE
        
        barra = f"{cor}{'█' * preenchido}{Cores.BRANCO}{'░' * (tamanho - preenchido)}{Cores.RESET}"
        return barra

# ============================================
# Classe Monitor de Rede
# ============================================

class MonitorRede:
    """Monitor de rede com GeoIP"""
    
    def __init__(self):
        self.conexões = []
        self.países_ativos = []
    
    def atualizar(self):
        """Atualiza dados de rede"""
        # Simular conexões
        self.conexões = [
            {'ip': '192.168.1.100', 'país': 'BR', 'status': 'ATIVO'},
            {'ip': '203.0.113.50', 'país': 'US', 'status': 'ATIVO'},
            {'ip': '198.51.100.25', 'país': 'DE', 'status': 'INATIVO'},
        ]
        
        self.países_ativos = ['BR', 'US', 'DE', 'FR', 'JP']
    
    def desenhar(self, x: int, y: int) -> List[str]:
        """Desenha o monitor de rede"""
        linhas = []
        
        # Título
        linhas.append(f"{Cores.NEON_VERDE}┌─────────────────────┐{Cores.RESET}")
        linhas.append(f"{Cores.NEON_VERDE}│   MONITOR DE REDE   │{Cores.RESET}")
        linhas.append(f"{Cores.NEON_VERDE}├─────────────────────┤{Cores.RESET}")
        
        # Conexões ativas
        for conn in self.conexões[:3]:
            status_cor = Cores.NEON_VERDE if conn['status'] == 'ATIVO' else Cores.NEON_VERMELHO
            linhas.append(f"{Cores.NEON_VERDE}│{Cores.RESET} {conn['país']}: {conn['ip'][:15]:15} {status_cor}{conn['status'][:6]}{Cores.RESET} {Cores.NEON_VERDE}│{Cores.RESET}")
        
        linhas.append(f"{Cores.NEON_VERDE}└─────────────────────┘{Cores.RESET}")
        
        return linhas

# ============================================
# Classe Terminal Principal
# ============================================

class TerminalPrincipal:
    """Terminal principal estilo eDEX-UI"""
    
    def __init__(self):
        self.linha_atual = 0
        self.comando = ''
        self.historico = []
        self.cursor_pos = 0
    
    def desenhar(self, x: int, y: int, largura: int, altura: int) -> List[str]:
        """Desenha o terminal"""
        linhas = []
        
        # Borda
        linhas.append(f"{Cores.NEON_AZUL}┌{'─' * (largura - 2)}┐{Cores.RESET}")
        linhas.append(f"{Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_CIANO}TERMINAL PRINCIPAL{Cores.RESET}{' ' * (largura - 22)}{Cores.NEON_AZUL}│{Cores.RESET}")
        linhas.append(f"{Cores.NEON_AZUL}├{'─' * (largura - 2)}┤{Cores.RESET}")
        
        # Comandos recentes
        for cmd in self.historico[-5:]:
            linhas.append(f"{Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_VERDE}${Cores.RESET} {cmd[:largura - 5]:{largura - 5}} {Cores.NEON_AZUL}│{Cores.RESET}")
        
        # Linhas vazias
        for _ in range(max(0, 5 - len(self.historico))):
            linhas.append(f"{Cores.NEON_AZUL}│{Cores.RESET} {' ' * (largura - 2)} {Cores.NEON_AZUL}│{Cores.RESET}")
        
        # Prompt
        prompt = f"{Cores.NEON_VERDE}ravena@desktop{Cores.RESET}:{Cores.NEON_AZUL}~{Cores.RESET}$ "
        linhas.append(f"{Cores.NEON_AZUL}│{Cores.RESET} {prompt}{'_' * (largura - len(prompt) - 3)} {Cores.NEON_AZUL}│{Cores.RESET}")
        
        linhas.append(f"{Cores.NEON_AZUL}└{'─' * (largura - 2)}┘{Cores.RESET}")
        
        return linhas
    
    def executar_comando(self, comando: str):
        """Executa comando"""
        self.historico.append(comando)
        self.comando = ''
        
        # Executar comando real
        try:
            resultado = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if resultado.stdout:
                for linha in resultado.stdout.split('\n')[:3]:
                    self.historico.append(f"  {linha}")
            
            if resultado.stderr:
                self.historico.append(f"  {Cores.VERMELHO}Erro: {resultado.stderr[:50]}{Cores.RESET}")
        except:
            self.historico.append(f"  {Cores.VERMELHO}Comando não encontrado{Cores.RESET}")

# ============================================
# Classe Principal Ravena Desktop
# ============================================

class RavenaDesktop:
    """Interface principal estilo eDEX-UI"""
    
    def __init__(self):
        self.terminal = Terminal()
        self.terra = Terra3D(60, 8, 6)
        self.monitor_sistema = MonitorSistema()
        self.monitor_rede = MonitorRede()
        self.terminal_principal = TerminalPrincipal()
        self.executando = True
    
    def desenhar_layout(self):
        """Desenha o layout completo"""
        self.terminal.limpar()
        self.terminal.ocultar_cursor()
        
        # Obter tamanho do terminal
        self.terminal.obter_tamanho()
        
        largura = self.terminal.largura
        altura = self.terminal.altura
        
        # Título
        print(f"{Cores.NEON_CIANO}{'═' * largura}{Cores.RESET}")
        print(f"{Cores.NEON_CIANO}{'═' * largura}{Cores.RESET}")
        print(f"{Cores.NEON_CIANO}{'═' * largura}{Cores.RESET}")
        
        # Linha do título
        titulo = "RAVENA SECURITY SANDBOX"
        espacos = (largura - len(titulo)) // 2
        print(f"{'═' * espacos}{Cores.NEON_VERDE}{Cores.NEGRITO}{titulo}{Cores.RESET}{'═' * espacos}")
        
        # Data/hora
        agora = datetime.now()
        data_hora = agora.strftime('%d/%m/%Y %H:%M:%S')
        espacos_data = (largura - len(data_hora)) // 2
        print(f"{'═' * espacos_data}{Cores.NEON_AMARELO}{data_hora}{Cores.RESET}{'═' * espacos_data}")
        
        print(f"{Cores.NEON_CIANO}{'═' * largura}{Cores.RESET}")
        print()
        
        # Linha 1: File Manager + Terminal + Terra
        print(f"{Cores.NEON_AMARELO}┌──────────────┐{Cores.RESET} {Cores.NEON_AZUL}┌{'─' * 40}┐{Cores.RESET} {Cores.NEON_MAGENTA}┌──────────────────────┐{Cores.RESET}")
        print(f"{Cores.NEON_AMARELO}│  GER. ARQUIVOS │{Cores.RESET} {Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_CIANO}TERMINAL PRINCIPAL{Cores.RESET}{' ' * 20}{Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_MAGENTA}│{Cores.RESET}    {Cores.NEON_CIANO}🌍 TERRA 3D{Cores.RESET}    {Cores.NEON_MAGENTA}│{Cores.RESET}")
        print(f"{Cores.NEON_AMARELO}├──────────────┤{Cores.RESET} {Cores.NEON_AZUL}├{'─' * 40}┤{Cores.RESET} {Cores.NEON_MAGENTA}├──────────────────────┤{Cores.RESET}")
        
        # Conteúdo do file manager
        print(f"{Cores.NEON_AMARELO}│ 📁 /opt      │{Cores.RESET} {Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_VERDE}${Cores.RESET} ravena --status        {Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_MAGENTA}│{Cores.RESET}      {Cores.NEON_VERDE}(•_•){Cores.RESET}       {Cores.NEON_MAGENTA}│{Cores.RESET}")
        print(f"{Cores.NEON_AMARELO}│ 📁 /etc      │{Cores.RESET} {Cores.NEON_AZUL}│{Cores.RESET}   Sistema: SAUDÁVEL    {Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_MAGENTA}│{Cores.RESET}     {Cores.NEON_AZUL}/█████\\{Cores.RESET}      {Cores.NEON_MAGENTA}│{Cores.RESET}")
        print(f"{Cores.NEON_AMARELO}│ 📁 /var      │{Cores.RESET} {Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_VERDE}${Cores.RESET} ravena --testar       {Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_MAGENTA}│{Cores.RESET}    {Cores.NEON_CIANO}/██●●██\\{Cores.RESET}     {Cores.NEON_MAGENTA}│{Cores.RESET}")
        print(f"{Cores.NEON_AMARELO}│ 📁 /tmp      │{Cores.RESET} {Cores.NEON_AZUL}│{Cores.RESET}   Testes: 127 OK      {Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_MAGENTA}│{Cores.RESET}     {Cores.NEON_VERDE}\\████/ {Cores.RESET}      {Cores.NEON_MAGENTA}│{Cores.RESET}")
        print(f"{Cores.NEON_AMARELO}└──────────────┘{Cores.RESET} {Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_VERDE}${Cores.RESET} ravena --relatorio    {Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_MAGENTA}│{Cores.RESET}    Países: BR,US,DE   {Cores.NEON_MAGENTA}│{Cores.RESET}")
        print(f"{' ' * 16}{Cores.NEON_AZUL}│{Cores.RESET}   Relatório: PDF OK  {Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_MAGENTA}└──────────────────────┘{Cores.RESET}")
        print(f"{' ' * 16}{Cores.NEON_AZUL}└{'─' * 40}┘{Cores.RESET}")
        print()
        
        # Linha 2: Monitores + Painel
        print(f"{Cores.NEON_VERDE}┌─────────────────────┐{Cores.RESET} {Cores.NEON_AZUL}┌─────────────────────┐{Cores.RESET} {Cores.NEON_VERMELHO}┌─────────────────────┐{Cores.RESET} {Cores.NEON_AMARELO}┌─────────────────────┐{Cores.RESET}")
        print(f"{Cores.NEON_VERDE}│  MONITOR DE SISTEMA │{Cores.RESET} {Cores.NEON_AZUL}│   MONITOR DE REDE   │{Cores.RESET} {Cores.NEON_VERMELHO}│  PAINEL DE PENTEST  │{Cores.RESET} {Cores.NEON_AMARELO}│    LOGS EM TEMPO    │{Cores.RESET}")
        print(f"{Cores.NEON_VERDE}├─────────────────────┤{Cores.RESET} {Cores.NEON_AZUL}├─────────────────────┤{Cores.RESET} {Cores.NEON_VERMELHO}├─────────────────────┤{Cores.RESET} {Cores.NEON_AMARELO}├─────────────────────┤{Cores.RESET}")
        
        # CPU
        cpu_barra = self._criar_barra(self.monitor_sistema.cpu)
        print(f"{Cores.NEON_VERDE}│{Cores.RESET} CPU: {cpu_barra} {self.monitor_sistema.cpu:5.1f}% {Cores.NEON_VERDE}│{Cores.RESET} {Cores.NEON_AZUL}│{Cores.RESET} BR: 192.168.1.1    {Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_VERMELHO}│{Cores.RESET} [Nmap]  [Nikto]   {Cores.NEON_VERMELHO}│{Cores.RESET} {Cores.NEON_AMARELO}│{Cores.RESET} 10:30:25 INFO OK {Cores.NEON_AMARELO}│{Cores.RESET}")
        
        # RAM
        ram_barra = self._criar_barra(self.monitor_sistema.ram)
        print(f"{Cores.NEON_VERDE}│{Cores.RESET} RAM: {ram_barra} {self.monitor_sistema.ram:5.1f}% {Cores.NEON_VERDE}│{Cores.RESET} {Cores.NEON_AZUL}│{Cores.RESET} US: 203.0.113.50   {Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_VERMELHO}│{Cores.RESET} [SQLMap] [Hydra]  {Cores.NEON_VERMELHO}│{Cores.RESET} {Cores.NEON_AMARELO}│{Cores.RESET} 10:30:26 WARN ALT {Cores.NEON_AMARELO}│{Cores.RESET}")
        
        # Disco
        disco_barra = self._criar_barra(35.0)
        print(f"{Cores.NEON_VERDE}│{Cores.RESET} DIS: {disco_barra} 35.0% {Cores.NEON_VERDE}│{Cores.RESET} {Cores.NEON_AZUL}│{Cores.RESET} DE: 198.51.100.25  {Cores.NEON_AZUL}│{Cores.RESET} {Cores.NEON_VERMELHO}│{Cores.RESET} [John]  [Gobuster]{Cores.NEON_VERMELHO}│{Cores.RESET} {Cores.NEON_AMARELO}│{Cores.RESET} 10:30:27 ERR BLOQ {Cores.NEON_AMARELO}│{Cores.RESET}")
        
        print(f"{Cores.NEON_VERDE}└─────────────────────┘{Cores.RESET} {Cores.NEON_AZUL}└─────────────────────┘{Cores.RESET} {Cores.NEON_VERMELHO}└─────────────────────┘{Cores.RESET} {Cores.NEON_AMARELO}└─────────────────────┘{Cores.RESET}")
        print()
        
        # Rodapé
        print(f"{Cores.NEON_CIANO}{'═' * largura}{Cores.RESET}")
        rodape = "Ravena Security Sandbox - [F1]Ajuda [F2]Status [F3]Logs [F4]Sair"
        espacos_rodape = (largura - len(rodape)) // 2
        print(f"{'═' * espacos_rodape}{Cores.NEON_VERDE}{rodape}{Cores.RESET}{'═' * espacos_rodape}")
        print(f"{Cores.NEON_CIANO}{'═' * largura}{Cores.RESET}")
    
    def _criar_barra(self, porcentagem: float) -> str:
        """Cria barra de progresso"""
        tamanho = 10
        preenchido = int(porcentagem / 100 * tamanho)
        
        if porcentagem > 80:
            cor = Cores.NEON_VERMELHO
        elif porcentagem > 60:
            cor = Cores.NEON_AMARELO
        else:
            cor = Cores.NEON_VERDE
        
        barra = f"{cor}{'█' * preenchido}{Cores.BRANCO}{'░' * (tamanho - preenchido)}{Cores.RESET}"
        return barra
    
    def executar(self):
        """Executa o desktop"""
        # Configurar signal handler para sair com Ctrl+C
        signal.signal(signal.SIGINT, self._sair)
        
        while self.executando:
            try:
                # Atualizar dados
                self.monitor_sistema.atualizar()
                self.monitor_rede.atualizar()
                self.terra.atualizar()
                
                # Desenhar layout
                self.desenhar_layout()
                
                # Aguardar
                time.sleep(2)
            except KeyboardInterrupt:
                self._sair()
            except Exception as e:
                print(f"Erro: {e}")
                time.sleep(1)
    
    def _sair(self, *args):
        """Sai do desktop"""
        self.executando = False
        self.terminal.mostrar_cursor()
        print(f"\n{Cores.NEON_CIANO}Saindo do Ravena Desktop...{Cores.RESET}")
        sys.exit(0)

# ============================================
# Ponto de entrada
# ============================================

def main():
    """Função principal"""
    print(f"{Cores.NEON_CIANO}Iniciando Ravena Desktop (eDEX-UI Style)...{Cores.RESET}")
    time.sleep(1)
    
    desktop = RavenaDesktop()
    desktop.executar()

if __name__ == '__main__':
    main()
