#!/usr/bin/env python3
"""
SKILL: Rate Limiter
Limita taxa de requisições na sandbox
"""

import time
import logging
from typing import Dict, Tuple, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps

class RateLimiter:
    """
    Limitador de taxa para sandbox isolada
    ATENÇÃO: Esta skill só funciona no ambiente da sandbox
    """
    
    def __init__(self):
        self.logger = logging.getLogger('RateLimiter')
        
        # Armazenamento de contadores
        self.counters = defaultdict(list)
        self.blocked_until = {}
        
        # Configurações padrão
        self.default_limits = {
            'login': {'requests': 5, 'window': 300},  # 5 req/5min
            'api': {'requests': 100, 'window': 60},    # 100 req/min
            'withdrawal': {'requests': 3, 'window': 3600},  # 3 req/hora
            'slot_spin': {'requests': 50, 'window': 60},  # 50 req/min
            'default': {'requests': 60, 'window': 60}  # 60 req/min
        }
        
    def check_rate_limit(self, key: str, endpoint: str = 'default') -> Tuple[bool, Dict]:
        """
        Verifica se a requisição deve ser permitida
        
        Returns:
            Tuple[allowed, info]
        """
        # Verificar se está bloqueado
        if key in self.blocked_until:
            if datetime.now() < self.blocked_until[key]:
                remaining = (self.blocked_until[key] - datetime.now()).seconds
                return False, {
                    'error': 'Rate limit excedido',
                    'retry_after': remaining,
                    'blocked_until': self.blocked_until[key].isoformat()
                }
            else:
                del self.blocked_until[key]
        
        # Obter limites
        limits = self.default_limits.get(endpoint, self.default_limits['default'])
        requests_limit = limits['requests']
        window_seconds = limits['window']
        
        # Limpar requisições antigas
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        self.counters[key] = [
            req_time for req_time in self.counters[key]
            if req_time > cutoff_time
        ]
        
        # Verificar limite
        current_count = len(self.counters[key])
        
        if current_count >= requests_limit:
            # Bloquear por um período
            self.blocked_until[key] = datetime.now() + timedelta(seconds=window_seconds)
            
            self.logger.warning(
                f"Rate limit excedido: key={key}, endpoint={endpoint}, "
                f"count={current_count}, limit={requests_limit}"
            )
            
            return False, {
                'error': 'Rate limit excedido',
                'current_count': current_count,
                'limit': requests_limit,
                'window': window_seconds,
                'retry_after': window_seconds
            }
        
        # Registrar requisição
        self.counters[key].append(datetime.now())
        
        return True, {
            'current_count': current_count + 1,
            'limit': requests_limit,
            'remaining': requests_limit - current_count - 1,
            'window': window_seconds
        }
    
    def get_remaining_requests(self, key: str, endpoint: str = 'default') -> int:
        """Retorna requições restantes"""
        limits = self.default_limits.get(endpoint, self.default_limits['default'])
        requests_limit = limits['requests']
        window_seconds = limits['window']
        
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        current_count = sum(
            1 for req_time in self.counters[key]
            if req_time > cutoff_time
        )
        
        return max(0, requests_limit - current_count)
    
    def get_reset_time(self, key: str, endpoint: str = 'default') -> Optional[datetime]:
        """Retorna tempo até reset do contador"""
        if not self.counters[key]:
            return None
        
        limits = self.default_limits.get(endpoint, self.default_limits['default'])
        window_seconds = limits['window']
        
        oldest_request = min(self.counters[key])
        return oldest_request + timedelta(seconds=window_seconds)
    
    def set_custom_limit(self, endpoint: str, requests: int, window: int):
        """Define limite personalizado"""
        self.default_limits[endpoint] = {
            'requests': requests,
            'window': window
        }
        self.logger.info(f"Limite personalizado definido: {endpoint} = {requests}/{window}s")
    
    def reset_counter(self, key: str, endpoint: str = None):
        """Reseta contador"""
        if endpoint:
            # Resetar apenas para um endpoint específico
            # (simplificado para sandbox)
            self.counters[key] = []
        else:
            self.counters[key] = []
        
        if key in self.blocked_until:
            del self.blocked_until[key]
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas"""
        active_counters = len([k for k, v in self.counters.items() if v])
        blocked_keys = len(self.blocked_until)
        
        return {
            'active_counters': active_counters,
            'blocked_keys': blocked_keys,
            'total_requests_tracked': sum(len(v) for v in self.counters.values()),
            'available_endpoints': list(self.default_limits.keys())
        }
    
    def get_endpoint_stats(self, endpoint: str) -> Dict:
        """Retorna stats de um endpoint específico"""
        limits = self.default_limits.get(endpoint, self.default_limits['default'])
        
        # Contar requisições para este endpoint
        total_requests = 0
        for key, requests in self.counters.items():
            cutoff_time = datetime.now() - timedelta(seconds=limits['window'])
            total_requests += sum(1 for r in requests if r > cutoff_time)
        
        return {
            'endpoint': endpoint,
            'limit': limits['requests'],
            'window': limits['window'],
            'total_requests': total_requests
        }


# Instância global
rate_limiter = RateLimiter()


def rate_limit(endpoint: str):
    """
    Decorator para limitar taxa de requisições
    
    Uso:
        @rate_limit('login')
        def login():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Obter chave (IP ou user_id)
            # Para sandbox, usar IP como chave
            from flask import request
            key = request.remote_addr if request else 'local'
            
            allowed, info = rate_limiter.check_rate_limit(key, endpoint)
            
            if not allowed:
                from flask import jsonify
                return jsonify({
                    'error': 'Rate limit excedido',
                    'retry_after': info.get('retry_after', 60)
                }), 429
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    print("="*60)
    print("TESTE: Rate Limiter")
    print("="*60)
    
    limiter = RateLimiter()
    limiter.set_custom_limit('test', 3, 10)  # 3 req/10s
    
    test_key = "192.168.1.100"
    
    print("\n1. Teste de Rate Limiting:")
    for i in range(5):
        allowed, info = limiter.check_rate_limit(test_key, 'test')
        print(f"  Requisição {i+1}: Permitido={allowed} | Info={info}")
    
    print("\n2. Estatísticas:", limiter.get_stats())
