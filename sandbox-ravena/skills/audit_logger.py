#!/usr/bin/env python3
"""
SKILL: Audit Logger
Registra todas as ações na sandbox para auditoria
"""

import json
import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

class AuditLogger:
    """
    Logger de auditoria para sandbox isolada
    ATENÇÃO: Esta skill só funciona no ambiente da sandbox
    """
    
    def __init__(self):
        self.logger = logging.getLogger('AuditLogger')
        
        # Armazenamento de logs
        self.logs = []
        self.logs_by_user = defaultdict(list)
        self.logs_by_type = defaultdict(list)
        
        # Configurações
        self.sensitive_fields = ['password', 'token', 'secret', 'credit_card']
        
    def log(self, 
            action: str, 
            user_id: str = None, 
            details: Dict = None,
            ip_address: str = None,
            status: str = 'success',
            severity: str = 'info') -> Dict:
        """
        Registra uma ação
        
        Args:
            action: Tipo de ação (login, logout, withdrawal, etc.)
            user_id: ID do usuário
            details: Detalhes adicionais
            ip_address: IP de origem
            status: status da ação (success, failure, error)
            severity: Severidade (info, warning, critical)
        
        Returns:
            Dict com o log registrado
        """
        # Criar registro
        log_entry = {
            'id': self._generate_log_id(),
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user_id': user_id,
            'ip_address': ip_address,
            'status': status,
            'severity': severity,
            'details': self._sanitize_details(details or {})
        }
        
        # Adicionar hash de integridade
        log_entry['integrity_hash'] = self._calculate_hash(log_entry)
        
        # Armazenar
        self.logs.append(log_entry)
        
        if user_id:
            self.logs_by_user[user_id].append(log_entry['id'])
        
        self.logs_by_type[action].append(log_entry['id'])
        
        # Log do sistema
        log_message = f"[{severity.upper()}] {action}: user={user_id}, status={status}"
        if severity == 'critical':
            self.logger.critical(log_message)
        elif severity == 'warning':
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        return log_entry
    
    def log_login(self, user_id: str, ip_address: str, success: bool, details: Dict = None) -> Dict:
        """Registra tentativa de login"""
        return self.log(
            action='login',
            user_id=user_id,
            ip_address=ip_address,
            status='success' if success else 'failure',
            severity='info' if success else 'warning',
            details=details
        )
    
    def log_logout(self, user_id: str, ip_address: str) -> Dict:
        """Registra logout"""
        return self.log(
            action='logout',
            user_id=user_id,
            ip_address=ip_address,
            status='success'
        )
    
    def log_withdrawal(self, user_id: str, amount: float, status: str, details: Dict = None) -> Dict:
        """Registra tentativa de saque"""
        return self.log(
            action='withdrawal',
            user_id=user_id,
            details={'amount': amount, **(details or {})},
            status=status,
            severity='critical' if status == 'failure' else 'info'
        )
    
    def log_slot_spin(self, user_id: str, bet_amount: float, win_amount: float, details: Dict = None) -> Dict:
        """Registra aposta em slot"""
        return self.log(
            action='slot_spin',
            user_id=user_id,
            details={
                'bet_amount': bet_amount,
                'win_amount': win_amount,
                **(details or {})
            }
        )
    
    def log_security_event(self, event_type: str, ip_address: str, details: Dict = None) -> Dict:
        """Registra evento de segurança"""
        return self.log(
            action=f'security_{event_type}',
            ip_address=ip_address,
            severity='critical',
            details=details
        )
    
    def log_data_access(self, user_id: str, resource: str, action: str, details: Dict = None) -> Dict:
        """Registra acesso a dados"""
        return self.log(
            action=f'data_{action}',
            user_id=user_id,
            details={'resource': resource, **(details or {})},
            severity='warning'
        )
    
    def get_user_logs(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Retorna logs de um usuário"""
        log_ids = self.logs_by_user.get(user_id, [])
        
        user_logs = [
            log for log in self.logs
            if log['id'] in log_ids
        ]
        
        # Ordenar por timestamp (mais recente primeiro)
        user_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return user_logs[:limit]
    
    def get_logs_by_type(self, action: str, limit: int = 100) -> List[Dict]:
        """Retorna logs por tipo de ação"""
        log_ids = self.logs_by_type.get(action, [])
        
        type_logs = [
            log for log in self.logs
            if log['id'] in log_ids
        ]
        
        type_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return type_logs[:limit]
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """Retorna logs mais recentes"""
        sorted_logs = sorted(
            self.logs,
            key=lambda x: x['timestamp'],
            reverse=True
        )
        
        return sorted_logs[:limit]
    
    def verify_integrity(self, log_entry: Dict) -> bool:
        """Verifica integridade de um log"""
        stored_hash = log_entry.get('integrity_hash')
        if not stored_hash:
            return False
        
        # Calcular hash sem o campo integrity_hash
        log_copy = {k: v for k, v in log_entry.items() if k != 'integrity_hash'}
        calculated_hash = self._calculate_hash(log_copy)
        
        return stored_hash == calculated_hash
    
    def export_logs(self, format: str = 'json') -> str:
        """Exporta logs"""
        if format == 'json':
            return json.dumps(self.logs, indent=2, ensure_ascii=False)
        elif format == 'csv':
            # Simplificado para sandbox
            lines = ['timestamp,action,user_id,ip_address,status,severity']
            for log in self.logs:
                lines.append(
                    f"{log['timestamp']},{log['action']},{log.get('user_id', '')},"
                    f"{log.get('ip_address', '')},{log['status']},{log['severity']}"
                )
            return '\n'.join(lines)
        else:
            return str(self.logs)
    
    def _generate_log_id(self) -> str:
        """Gera ID único para o log"""
        import uuid
        return str(uuid.uuid4())
    
    def _sanitize_details(self, details: Dict) -> Dict:
        """Sanitiza detalhes sensíveis"""
        sanitized = {}
        
        for key, value in details.items():
            # Verificar se é campo sensível
            is_sensitive = any(
                sensitive in key.lower()
                for sensitive in self.sensitive_fields
            )
            
            if is_sensitive:
                # Mascarar valor
                if isinstance(value, str) and len(value) > 4:
                    sanitized[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                else:
                    sanitized[key] = '***'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _calculate_hash(self, data: Dict) -> str:
        """Calcula hash de integridade"""
        # Converter para JSON ordenado
        data_str = json.dumps(data, sort_keys=True, default=str)
        
        # Calcular SHA-256
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas"""
        return {
            'total_logs': len(self.logs),
            'unique_users': len(self.logs_by_user),
            'action_types': list(self.logs_by_type.keys()),
            'logs_by_severity': self._count_by_severity()
        }
    
    def _count_by_severity(self) -> Dict:
        """Conta logs por severidade"""
        counts = defaultdict(int)
        for log in self.logs:
            counts[log['severity']] += 1
        return dict(counts)


# Instância global
audit_logger = AuditLogger()


if __name__ == "__main__":
    print("="*60)
    print("TESTE: Audit Logger")
    print("="*60)
    
    logger = AuditLogger()
    
    # Simular ações
    print("\n1. Registrando ações:")
    
    logger.log_login("user_001", "192.168.1.100", True)
    logger.log_login("user_002", "192.168.1.101", False)
    logger.log_withdrawal("user_001", 500.00, "success")
    logger.log_slot_spin("user_001", 100.00, 250.00)
    logger.log_security_event("sql_injection", "10.0.0.1", {"payload": "' OR 1=1--"})
    
    print(f"  Total de logs: {len(logger.logs)}")
    
    # Verificar integridade
    print("\n2. Verificação de Integridade:")
    for log in logger.logs[:3]:
        is_valid = logger.verify_integrity(log)
        print(f"  Log {log['id'][:8]}...: Válido={is_valid}")
    
    # Estatísticas
    print("\n3. Estatísticas:", logger.get_stats())
    
    # Exportar
    print("\n4. Exportando logs (JSON):")
    exported = logger.export_logs('json')
    print(f"  Tamanho: {len(exported)} caracteres")
