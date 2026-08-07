#!/usr/bin/env python3
"""
SKILL: Session Manager
Gerencia sessões de forma segura na sandbox
"""

import secrets
import hashlib
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

class SessionManager:
    """
    Gerenciador de sessões para sandbox isolada
    ATENÇÃO: Esta skill só funciona no ambiente da sandbox
    """
    
    def __init__(self, session_timeout_minutes: int = 30, max_sessions_per_user: int = 3):
        self.logger = logging.getLogger('SessionManager')
        self.session_timeout = session_timeout_minutes
        self.max_sessions = max_sessions_per_user
        
        # Armazenamento de sessões
        self.sessions = {}
        self.user_sessions = defaultdict(list)
        self.invalidated_tokens = set()
        
    def create_session(self, user_id: str, ip_address: str, user_agent: str) -> Dict:
        """Cria uma nova sessão"""
        # Gerar token seguro
        token = self._generate_token()
        
        # Criar sessão
        session = {
            'token': token,
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=self.session_timeout),
            'last_activity': datetime.now(),
            'is_valid': True
        }
        
        # Armazenar sessão
        self.sessions[token] = session
        self.user_sessions[user_id].append(token)
        
        # Verificar limite de sessões
        self._enforce_session_limit(user_id)
        
        self.logger.info(f"Sessão criada para user_id={user_id}")
        
        return {
            'token': token,
            'expires_at': session['expires_at'].isoformat()
        }
    
    def validate_session(self, token: str, ip_address: str) -> Tuple[bool, Dict]:
        """
        Valida uma sessão
        
        Returns:
            Tuple[is_valid, session_data_or_error]
        """
        # Verificar se o token foi invalidado
        if token in self.invalidated_tokens:
            return False, {'error': 'Token invalidado'}
        
        # Verificar se a sessão existe
        if token not in self.sessions:
            return False, {'error': 'Sessão não encontrada'}
        
        session = self.sessions[token]
        
        # Verificar se a sessão é válida
        if not session['is_valid']:
            return False, {'error': 'Sessão inválida'}
        
        # Verificar expiração
        if datetime.now() > session['expires_at']:
            self._invalidate_session(token)
            return False, {'error': 'Sessão expirada'}
        
        # Verificar IP (opcional - para maior segurança)
        if session['ip_address'] != ip_address:
            self.logger.warning(
                f"Tentativa de sessão de IP diferente: "
                f"esperado={session['ip_address']}, atual={ip_address}"
            )
            # Não invalidar, mas registrar
        
        # Atualizar atividade
        session['last_activity'] = datetime.now()
        
        return True, {
            'user_id': session['user_id'],
            'ip_address': session['ip_address'],
            'created_at': session['created_at'].isoformat(),
            'expires_at': session['expires_at'].isoformat()
        }
    
    def invalidate_session(self, token: str) -> bool:
        """Invalida uma sessão específica"""
        return self._invalidate_session(token)
    
    def invalidate_all_user_sessions(self, user_id: str) -> int:
        """Invalida todas as sessões de um usuário"""
        tokens = self.user_sessions.get(user_id, [])
        count = 0
        
        for token in tokens:
            if self._invalidate_session(token):
                count += 1
        
        self.user_sessions[user_id] = []
        
        self.logger.info(f"Todas as sessões invalidadas para user_id={user_id}: {count}")
        
        return count
    
    def _invalidate_session(self, token: str) -> bool:
        """Invalida uma sessão internamente"""
        if token in self.sessions:
            self.sessions[token]['is_valid'] = False
            self.invalidated_tokens.add(token)
            
            user_id = self.sessions[token]['user_id']
            if token in self.user_sessions[user_id]:
                self.user_sessions[user_id].remove(token)
            
            return True
        return False
    
    def _generate_token(self) -> str:
        """Gera um token seguro"""
        # Usar secrets para cryptographically secure random
        random_bytes = secrets.token_bytes(32)
        
        # Adicionar timestamp para unicidade
        timestamp = datetime.now().isoformat()
        
        # Hash
        token_data = f"{random_bytes}{timestamp}".encode()
        token = hashlib.sha256(token_data).hexdigest()
        
        return token
    
    def _enforce_session_limit(self, user_id: str):
        """Enforce maximum sessions per user"""
        user_tokens = self.user_sessions.get(user_id, [])
        
        while len(user_tokens) > self.max_sessions:
            # Invalidar a sessão mais antiga
            oldest_token = user_tokens.pop(0)
            self._invalidate_session(oldest_token)
            self.logger.warning(f"Sessão removida por limite: user_id={user_id}")
    
    def get_user_sessions(self, user_id: str) -> List[Dict]:
        """Retorna sessões ativas de um usuário"""
        tokens = self.user_sessions.get(user_id, [])
        sessions = []
        
        for token in tokens:
            if token in self.sessions and self.sessions[token]['is_valid']:
                session = self.sessions[token]
                sessions.append({
                    'token': token[:16] + '...',  # Mascarar token
                    'ip_address': session['ip_address'],
                    'created_at': session['created_at'].isoformat(),
                    'expires_at': session['expires_at'].isoformat(),
                    'last_activity': session['last_activity'].isoformat()
                })
        
        return sessions
    
    def get_all_active_sessions(self) -> Dict:
        """Retorna todas as sessões ativas"""
        active_sessions = {}
        
        for token, session in self.sessions.items():
            if session['is_valid'] and datetime.now() < session['expires_at']:
                active_sessions[token[:16]] = {
                    'user_id': session['user_id'],
                    'ip_address': session['ip_address'],
                    'expires_at': session['expires_at'].isoformat()
                }
        
        return active_sessions
    
    def cleanup_expired_sessions(self) -> int:
        """Remove sessões expiradas"""
        expired_tokens = []
        
        for token, session in self.sessions.items():
            if datetime.now() > session['expires_at']:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            self._invalidate_session(token)
        
        if expired_tokens:
            self.logger.info(f"Sessões expiradas removidas: {len(expired_tokens)}")
        
        return len(expired_tokens)
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas"""
        active_count = sum(
            1 for s in self.sessions.values()
            if s['is_valid'] and datetime.now() < s['expires_at']
        )
        
        return {
            'total_sessions': len(self.sessions),
            'active_sessions': active_count,
            'invalidated_tokens': len(self.invalidated_tokens),
            'users_with_sessions': len(self.user_sessions)
        }


# Instância global
session_manager = SessionManager()


if __name__ == "__main__":
    print("="*60)
    print("TESTE: Session Manager")
    print("="*60)
    
    manager = SessionManager(session_timeout_minutes=5, max_sessions_per_user=2)
    
    # Criar sessões
    print("\n1. Criando sessões:")
    for i in range(3):
        result = manager.create_session(
            user_id="user_001",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )
        print(f"  Sessão {i+1}: {result['token'][:16]}...")
    
    # Validar sessão
    print("\n2. Validando sessão:")
    token = list(manager.sessions.keys())[0]
    is_valid, data = manager.validate_session(token, "192.168.1.100")
    print(f"  Válido: {is_valid} | Dados: {data}")
    
    # Estatísticas
    print("\n3. Estatísticas:", manager.get_stats())
