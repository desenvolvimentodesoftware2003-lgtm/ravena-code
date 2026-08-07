#!/usr/bin/env python3
"""
SKILL: SQL Injection Detector
Detecta e bloqueia tentativas de SQL Injection na sandbox
"""

import re
import logging
from typing import Tuple, Dict, List

class SQLInjectionDetector:
    """
    Detector de SQL Injection para sandbox isolada
    ATENÇÃO: Esta skill só funciona no ambiente da sandbox
    """
    
    def __init__(self):
        self.logger = logging.getLogger('SQLiDetector')
        self.patterns = self._load_patterns()
        self.blocked_attempts = []
        
    def _load_patterns(self) -> Dict[str, List[str]]:
        """Carrega padrões de SQL Injection"""
        return {
            'union': [
                r'UNION\s+SELECT',
                r'UNION\s+ALL\s+SELECT',
                r'UNION\s+DISTINCT\s+SELECT'
            ],
            'comment': [
                r'--\s*$',
                r'/\*.*\*/',
                r'#\s*$'
            ],
            'always_true': [
                r"'\s*OR\s+'1'\s*=\s*'1",
                r"'\s*OR\s+1\s*=\s*1",
                r"'\s*OR\s+true",
                r'"\s*OR\s+"1"\s*=\s*"1',
                r'"\s*OR\s+1\s*=\s*1'
            ],
            'stacked': [
                r';\s*SELECT',
                r';\s*INSERT',
                r';\s*UPDATE',
                r';\s*DELETE',
                r';\s*DROP'
            ],
            'info_gathering': [
                r' information_schema',
                r' pg_catalog',
                r' sys\.objects',
                r' sys\.columns',
                r' SHOW\s+TABLES',
                r' SHOW\s+DATABASES'
            ],
            'blind': [
                r'AND\s+\d+\s*=\s*\d+',
                r'OR\s+\d+\s*=\s*\d+',
                r'AND\s+\'\w+\'\s*=\s*\'\w+\'',
                r'WAITFOR\s+DELAY',
                r'BENCHMARK\s*\(',
                r'SLEEP\s*\('
            ],
            'dangerous_functions': [
                r'EXEC\s*\(',
                r'EXECUTE\s*\(',
                r'CHAR\s*\(',
                r'0x[0-9a-fA-F]+',
                r'CONCAT\s*\(',
                r'GROUP_CONCAT\s*\('
            ]
        }
    
    def analyze(self, input_data: str) -> Tuple[bool, str, float]:
        """
        Analisa input em busca de SQL Injection
        
        Returns:
            Tuple[is_malicious, attack_type, confidence]
        """
        if not input_data:
            return False, None, 0.0
        
        input_upper = input_data.upper().strip()
        
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, input_upper, re.IGNORECASE):
                    confidence = self._calculate_confidence(category, input_data)
                    self.logger.warning(f"SQL Injection detectado: {category}")
                    return True, category, confidence
        
        return False, None, 0.0
    
    def _calculate_confidence(self, category: str, input_data: str) -> float:
        """Calcula confiança da detecção"""
        base_confidence = {
            'union': 0.95,
            'comment': 0.70,
            'always_true': 0.90,
            'stacked': 0.95,
            'info_gathering': 0.85,
            'blind': 0.80,
            'dangerous_functions': 0.90
        }
        
        confidence = base_confidence.get(category, 0.5)
        
        # Aumentar confiança se houver múltiplos padrões
        for other_category, patterns in self.patterns.items():
            if other_category != category:
                for pattern in patterns:
                    if re.search(pattern, input_data, re.IGNORECASE):
                        confidence = min(confidence + 0.1, 1.0)
                        break
        
        return confidence
    
    def block_and_log(self, input_data: str, endpoint: str, ip_address: str) -> Dict:
        """Bloqueia e registra tentativa de ataque"""
        is_malicious, attack_type, confidence = self.analyze(input_data)
        
        if is_malicious:
            attempt = {
                'input': input_data[:500],
                'endpoint': endpoint,
                'ip_address': ip_address,
                'attack_type': attack_type,
                'confidence': confidence,
                'timestamp': self._get_timestamp()
            }
            
            self.blocked_attempts.append(attempt)
            self.logger.critical(f"BLOQUEADO: {attack_type} de {ip_address}")
            
            return {
                'blocked': True,
                'attack_type': attack_type,
                'confidence': confidence,
                'message': f'Ataque {attack_type} detectado e bloqueado'
            }
        
        return {'blocked': False}
    
    def _get_timestamp(self) -> str:
        """Retorna timestamp atual"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas de detecção"""
        stats = {
            'total_blocked': len(self.blocked_attempts),
            'by_type': {},
            'by_ip': {}
        }
        
        for attempt in self.blocked_attempts:
            attack_type = attempt['attack_type']
            ip = attempt['ip_address']
            
            stats['by_type'][attack_type] = stats['by_type'].get(attack_type, 0) + 1
            stats['by_ip'][ip] = stats['by_ip'].get(ip, 0) + 1
        
        return stats


# Instância global para uso na sandbox
sqli_detector = SQLInjectionDetector()


if __name__ == "__main__":
    # Testes da skill
    print("="*60)
    print("TESTE: SQL Injection Detector")
    print("="*60)
    
    test_cases = [
        ("' OR 1=1--", True),
        ("admin'--", True),
        ("' UNION SELECT * FROM users--", True),
        ("normal input", False),
        ("'; DROP TABLE users;--", True),
        ("1' AND '1'='1", True),
        ("SELECT * FROM users WHERE id=1", True),
        ("hello world", False)
    ]
    
    detector = SQLInjectionDetector()
    
    for input_data, expected in test_cases:
        is_malicious, attack_type, confidence = detector.analyze(input_data)
        status = "✓" if is_malicious == expected else "✗"
        print(f"{status} Input: {input_data[:30]:<30} | Malicioso: {is_malicious} | Tipo: {attack_type}")
    
    print("\n" + "="*60)
    print("Estatísticas:", detector.get_stats())
