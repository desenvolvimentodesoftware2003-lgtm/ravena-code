#!/usr/bin/env python3
"""
SKILL: Input Validator
Valida e sanitiza entradas na sandbox
"""

import re
import html
import logging
from typing import Dict, List, Tuple, Any

class InputValidator:
    """
    Validador de entradas para sandbox isolada
    ATENÇÃO: Esta skill só funciona no ambiente da sandbox
    """
    
    def __init__(self):
        self.logger = logging.getLogger('InputValidator')
        self.validation_rules = self._load_rules()
        self.blocked_patterns = self._load_blocked_patterns()
        
    def _load_rules(self) -> Dict[str, Dict]:
        """Carrega regras de validação"""
        return {
            'username': {
                'min_length': 3,
                'max_length': 50,
                'pattern': r'^[a-zA-Z0-9_]+$',
                'blocked': ['admin', 'root', 'system']
            },
            'email': {
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'max_length': 100
            },
            'password': {
                'min_length': 8,
                'max_length': 128,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_digit': True,
                'require_special': True
            },
            'amount': {
                'type': 'numeric',
                'min_value': 0.01,
                'max_value': 10000.00,
                'decimal_places': 2
            },
            'pix_key': {
                'min_length': 10,
                'max_length': 100,
                'pattern': r'^[a-zA-Z0-9@._-]+$'
            },
            'text': {
                'max_length': 1000,
                'strip_html': True
            },
            'sql_safe': {
                'blocked_patterns': [
                    r"('|\\')",
                    r"(--|#|/\*|\*/)",
                    r"(;|DROP|DELETE|INSERT|UPDATE|SELECT|UNION|ALTER)"
                ]
            }
        }
    
    def _load_blocked_patterns(self) -> List[str]:
        """Carrega padrões bloqueados"""
        return [
            # SQL Injection
            r"'\s*OR\s+'1'\s*=\s*'1",
            r"'\s*OR\s+1\s*=\s*1",
            r"UNION\s+SELECT",
            r"DROP\s+TABLE",
            r"INSERT\s+INTO",
            r"DELETE\s+FROM",
            
            # XSS
            r"<script[^>]*>",
            r"javascript:",
            r"on\w+\s*=",
            r"eval\s*\(",
            r"document\.cookie",
            
            # Path Traversal
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e",
            
            # Command Injection
            r";\s*ls",
            r";\s*cat",
            r"\|\s*ls",
            r"`.*`",
            
            # LDAP Injection
            r"\(\|.*\)",
            r"\(&.*\)"
        ]
    
    def validate(self, value: Any, field_type: str) -> Tuple[bool, str, Any]:
        """
        Valida um valor
        
        Returns:
            Tuple[is_valid, error_message, sanitized_value]
        """
        if field_type not in self.validation_rules:
            return True, None, value
        
        rules = self.validation_rules[field_type]
        
        # Verificar se é string
        if isinstance(value, str):
            # Verificar padrões bloqueados
            if self._contains_blocked_pattern(value):
                self.logger.warning(f"Padrão bloqueado detectado em {field_type}")
                return False, "Entrada contém padrão não permitido", None
            
            # Sanitizar
            sanitized = self._sanitize(value, rules)
            
            # Validar comprimento
            if 'min_length' in rules and len(sanitized) < rules['min_length']:
                return False, f"Mínimo de {rules['min_length']} caracteres", None
            
            if 'max_length' in rules and len(sanitized) > rules['max_length']:
                return False, f"Máximo de {rules['max_length']} caracteres", None
            
            # Validar padrão
            if 'pattern' in rules and not re.match(rules['pattern'], sanitized):
                return False, "Formato inválido", None
            
            # Verificar bloqueados
            if 'blocked' in rules and sanitized.lower() in rules['blocked']:
                return False, "Valor não permitido", None
            
            return True, None, sanitized
        
        # Validar numérico
        if rules.get('type') == 'numeric':
            try:
                num_value = float(value)
                
                if 'min_value' in rules and num_value < rules['min_value']:
                    return False, f"Valor mínimo: {rules['min_value']}", None
                
                if 'max_value' in rules and num_value > rules['max_value']:
                    return False, f"Valor máximo: {rules['max_value']}", None
                
                return True, None, num_value
            
            except (ValueError, TypeError):
                return False, "Valor numérico inválido", None
        
        return True, None, value
    
    def _contains_blocked_pattern(self, value: str) -> bool:
        """Verifica se contém padrão bloqueado"""
        value_upper = value.upper()
        
        for pattern in self.blocked_patterns:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        
        return False
    
    def _sanitize(self, value: str, rules: Dict) -> str:
        """Sanitiza o valor"""
        sanitized = value
        
        # Remover espaços extras
        sanitized = sanitized.strip()
        
        # Escape HTML se necessário
        if rules.get('strip_html', False):
            sanitized = html.escape(sanitized)
        
        # Remover caracteres perigosos
        if rules.get('strip_special', False):
            sanitized = re.sub(r'[<>"\']', '', sanitized)
        
        return sanitized
    
    def validate_password_strength(self, password: str) -> Dict:
        """Valida força da senha"""
        result = {
            'is_strong': False,
            'score': 0,
            'checks': {
                'length': len(password) >= 8,
                'uppercase': bool(re.search(r'[A-Z]', password)),
                'lowercase': bool(re.search(r'[a-z]', password)),
                'digit': bool(re.search(r'\d', password)),
                'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
            }
        }
        
        # Calcular score
        score = 0
        for check, passed in result['checks'].items():
            if passed:
                score += 20
        
        result['score'] = score
        result['is_strong'] = score >= 80
        
        return result
    
    def sanitize_for_sql(self, value: str) -> str:
        """Sanitiza valor para consulta SQL (não use em produção!)"""
        # ATENÇÃO: Apenas para demonstração na sandbox
        # Em produção, use Prepared Statements!
        
        if not isinstance(value, str):
            return str(value)
        
        # Escape de aspas simples
        sanitized = value.replace("'", "''")
        
        # Remover caracteres perigosos
        sanitized = re.sub(r'[;\\]', '', sanitized)
        
        return sanitized
    
    def validate_batch(self, data: Dict[str, Tuple[Any, str]]) -> Dict[str, Dict]:
        """
        Valida múltiplos campos
        
        Args:
            data: Dict com {campo: (valor, tipo)}
        
        Returns:
            Dict com resultados de validação
        """
        results = {}
        
        for field, (value, field_type) in data.items():
            is_valid, error, sanitized = self.validate(value, field_type)
            results[field] = {
                'is_valid': is_valid,
                'error': error,
                'sanitized': sanitized
            }
        
        return results
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas"""
        return {
            'available_rules': list(self.validation_rules.keys()),
            'blocked_patterns_count': len(self.blocked_patterns)
        }


# Instância global
input_validator = InputValidator()


if __name__ == "__main__":
    print("="*60)
    print("TESTE: Input Validator")
    print("="*60)
    
    validator = InputValidator()
    
    # Testes de validação
    test_cases = [
        ("admin", "username", True),
        ("' OR 1=1--", "username", False),
        ("user@example.com", "email", True),
        ("invalid-email", "email", False),
        ("100.50", "amount", True),
        ("-10", "amount", False),
        ("12345678", "password", False),
        ("Abc@1234", "password", True)
    ]
    
    print("\n1. Testes de Validação:")
    for value, field_type, expected in test_cases:
        is_valid, error, sanitized = validator.validate(value, field_type)
        status = "✓" if is_valid == expected else "✗"
        print(f"  {status} {field_type}: {value[:20]:<20} | Válido: {is_valid} | Erro: {error}")
    
    # Teste de força de senha
    print("\n2. Teste de Força de Senha:")
    passwords = ["123456", "Abc@1234", "Fraca123!", "S3gura@Fort3"]
    for pwd in passwords:
        result = validator.validate_password_strength(pwd)
        print(f"  {pwd:<15} | Score: {result['score']}% | Forte: {result['is_strong']}")
    
    print("\n3. Estatísticas:", validator.get_stats())
