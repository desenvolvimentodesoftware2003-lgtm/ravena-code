import re

class JuizUniversal:
    def __init__(self):
        self.protocolo_lockdown = "V2.2"
        self.regras_seguranca = {
            "shell_injection": [r"rm -rf", r"sudo", r"chmod", r"chown", r"mkfs", r"dd if=", r"sh ", r"bash ", r"python -c"],
            "data_exfiltration": [r"curl", r"wget", r"scp", r"ftp", r"telnet", r"nc ", r"netcat"],
            "sensitive_files": [r"/etc/passwd", r"/etc/shadow", r"~/.ssh", r"~/.aws", r"~/.kube", r"~/.gitconfig"],
            "malicious_patterns": [r"eval\(", r"exec\(", r"os\.system", r"subprocess\.run", r"__import__"],
            "api_token_protection": [r"sk-[a-zA-Z0-9]{48}", r"ghp_[a-zA-Z0-9]{36}", r"[0-9]{9,10}:[a-zA-Z0-9_-]{35}", r"AIza[0-9A-Za-z-_]{35}"]
        }

    def validar_comando(self, comando):
        for categoria, padroes in self.regras_seguranca.items():
            for padrao in padroes:
                if re.search(padrao, comando):
                    return False, f"Comando bloqueado pelo Protocolo Lockdown {self.protocolo_lockdown} (Categoria: {categoria})"
        return True, "Comando seguro."

    def auditar_acao(self, acao, usuario="sistema"):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}] [AUDITORIA] Usuário: {usuario} | Ação: {acao}"
