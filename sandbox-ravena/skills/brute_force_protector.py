#!/usr/bin/env python3
"""
SKILL: Brute Force Protector
Protege contra ataques de força bruta na sandbox
"""

import time
import logging
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

class BruteForceProtector:
    """
    Protetor contra brute force para sandbox isolada
    ATENÇÃO: Esta skill só funciona no ambiente da sandbox
    """
    
    def __init__(self, max_attempts: int = 5, window_minutes: int = 5, lockout_minutes: int = 15):
        self.logger = logging.getLogger('BruteForceProtector')
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes
        self.lockout_minutes = lockout_minutes
        
        # Armazenamento de tentativas (em memória para sandbox)
        self.attempts = defaultdict(list)
        self.lockouts = {}
        self.blocked_ips = defaultdict(int)
        
    def check_attempt(self, ip_address: str, username: str) -> Tuple[bool, str]:
        """
        Verifica se uma tentativa de login deve ser permitida
        
        Returns:
            Tuple[allowed, message]
        """
        # Verificar se o IP está bloqueado
        if self._is_ip_locked(ip_address):
            self.logger.warning(f"IP bloqueado: {ip_address}")
            return False, f"IP bloqueado por {self.lockout_minutes} minutos"
        
        # Verificar se o usuário está bloqueado
        if self._is_user_locked(username):
            self.logger.warning(f"Usuário bloqueado: {username}")
            return False, f"Usuário bloqueado por {self.lockout_minutes} minutos"
        
        # Registrar tentativa
        self._record_attempt(ip_address, username)
        
        # Verificar se excedeu o limite
        if self._check_rate_limit(ip_address, username):
            self._apply_lockout(ip_address, username)
            return False, f"Máximo de {self.max_attempts} tentativas excedido"
        
        return True, "Tentativa permitida"
    
    def _is_ip_locked(self, ip_address: str) -> bool:
        """Verifica se o IP está bloqueado"""
        if ip_address in self.lockouts:
            lockout_time = self.lockouts[ip_address]
            if datetime.now() < lockout_time:
                return True
            else:
                del self.lockouts[ip_address]
        return False
    
    def _is_user_locked(self, username: str) -> bool:
        """Verifica se o usuário está bloqueado"""
        lockout_key = f"user:{username}"
        if lockout_key in self.lockouts:
            lockout_time = self.lockouts[lockout_key]
            if datetime.now() < lockout_time:
                return True
            else:
                del self.lockouts[lockout_key]
        return False
    
    def _record_attempt(self, ip_address: str, username: str):
        """Registra tentativa de login"""
        attempt = {
            'timestamp': datetime.now(),
            'ip_address': ip_address,
            'username': username
        }
        
        self.attempts[ip_address].append(attempt)
        
        # Limpar tentativas antigas
        cutoff_time = datetime.now() - timedelta(minutes=self.window_minutes)
        self.attempts[ip_address] = [
            a for a in self.attempts[ip_address]
            if a['timestamp'] > cutoff_time
        ]
    
    def _check_rate_limit(self, ip_address: str, username: str) -> bool:
        """Verifica se o limite de taxa foi excedido"""
        # Contar tentativas do IP
        ip_attempts = len(self.attempts.get(ip_address, []))
        
        # Contar tentativas do usuário (de todos os IPs)
        user_attempts = sum(
            len([a for a in attempts if a['username'] == username])
            for attempts in self.attempts.values()
        )
        
        return ip_attempts >= self.max_attempts or user_attempts >= self.max_attempts
    
    def _apply_lockout(self, ip_address: str, username: str):
        """Aplica bloqueio"""
        lockout_time = datetime.now() + timedelta(minutes=self.lockout_minutes)
        
        self.lockouts[ip_address] = lockout_time
        self.lockouts[f"user:{username}"] = lockout_time
        self.blocked_ips[ip_address] += 1
        
        self.logger.critical(
            f"BLOQUEIO APLICADO: IP={ip_address}, User={username}, "
            f"Duração={self.lockout_minutes}min"
        )
    
    def get_failed_attempts(self, ip_address: str = None) -> List[Dict]:
        """Retorna tentativas falhas"""
        if ip_address:
            return [
                {'timestamp': a['timestamp'].isoformat(), 'username': a['username']}
                for a in self.attempts.get(ip_address, [])
            ]
        
        all_attempts = []
        for ip, attempts in self.attempts.items():
            for a in attempts:
                all_attempts.append({
                    'ip_address': ip,
                    'timestamp': a['timestamp'].isoformat(),
                    'username': a['username']
                })
        
        return sorted(all_attempts, key=lambda x: x['timestamp'], reverse=True)
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas"""
        return {
            'total_attempts': sum(len(a) for a in self.attempts.values()),
            'blocked_ips': dict(self.blocked_ips),
            'active_lockouts': len(self.lockouts),
            'unique_ips': len(self.attempts)
        }
    
    def reset_lockout(self, ip_address: str = None, username: str = None):
        """Reseta bloqueio (para testes)"""
        if ip_address and ip_address in self.lockouts:
            del self.lockouts[ip_address]
        
        if username:
            lockout_key = f"user:{username}"
            if lockout_key in self.lockouts:
                del self.lockouts[lockout_key]


# Instância global
brute_force_protector = BruteForceProtector()


if __name__ == "__main__":
    print("="*60)
    print("TESTE: Brute Force Protector")
    print("="*60)
    
    protector = BruteForceProtector(max_attempts=3, window_minutes=1, lockout_minutes=1)
    
    # Simular tentativas
    test_ip = "192.168.1.100"
    test_user = "admin"
    
    for i in range(5):
        allowed, message = protector.check_attempt(test_ip, test_user)
        print(f"Tentativa {i+1}: Permitido={allowed} | Mensagem={message}")
    
    print("\nEstatísticas:", protector.get_stats())
