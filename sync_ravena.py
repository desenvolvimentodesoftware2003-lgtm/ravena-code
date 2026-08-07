
import subprocess
import os
import datetime
from modulos.api.bot_ravena import send_notification


# Configurações
GITHUB_REPO_URL = "https://github.com/desenvolvimentodesoftware2003-lgtm/ravena-aim.git"
LOCAL_REPO_PATH = "/home/ubuntu/ravena-aim"
DRIVE_REMOTE_NAME = "manus_google_drive"
DRIVE_FOLDER_PATH = "ravena-modula"
RCLONE_CONFIG_PATH = "/home/ubuntu/.gdrive-rclone.ini"

# Pastas a serem sincronizadas do repositório local para o Drive
FOLDERS_TO_SYNC = [
    "logs",
    "memoria",
    "modulos" # Assumindo que 'modulos' contém artefatos que precisam ser sincronizados
]

def log_message(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_command(command, cwd=None):
    try:
        log_message(f"Executando comando: {command}")
        result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True, shell=True)
        log_message(f"Saída do comando:\n{result.stdout}")
        if result.stderr:
            log_message(f"Erros do comando (stderr):\n{result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"Erro ao executar comando: {e}")
        log_message(f"Saída padrão:\n{e.stdout}")
        log_message(f"Saída de erro:\n{e.stderr}")
        return False
    except Exception as e:
        log_message(f"Ocorreu um erro inesperado: {e}")
        return False

def sync_github_to_drive():
    log_message("Iniciando sincronização GitHub para Google Drive...")
    send_notification("Iniciando sincronização GitHub para Google Drive...")


    # 1. Atualizar repositório GitHub
    if not os.path.exists(LOCAL_REPO_PATH):
        log_message(f"Repositório local não encontrado em {LOCAL_REPO_PATH}. Clonando...")
        if not run_command(f"gh repo clone {GITHUB_REPO_URL.split('/')[-1].replace('.git', '')} {LOCAL_REPO_PATH}"):
            log_message("Falha ao clonar o repositório GitHub.")
            send_notification("Falha ao clonar o repositório GitHub.")
            return
    else:
        log_message(f"Atualizando repositório local em {LOCAL_REPO_PATH}...")
        if not run_command("git pull origin main", cwd=LOCAL_REPO_PATH):
            log_message("Falha ao atualizar o repositório GitHub.")
            send_notification("Falha ao atualizar o repositório GitHub.")
            return

    # 2. Sincronizar pastas específicas para o Google Drive
    for folder in FOLDERS_TO_SYNC:
        local_folder_path = os.path.join(LOCAL_REPO_PATH, folder)
        drive_target_path = f"{DRIVE_REMOTE_NAME}:{DRIVE_FOLDER_PATH}/{folder}"
        
        if not os.path.exists(local_folder_path):
            log_message(f"A pasta local '{local_folder_path}' não existe. Pulando sincronização para esta pasta.")
            continue

        log_message(f"Sincronizando '{local_folder_path}' para '{drive_target_path}'...")
        # Usamos 'rclone copy' para evitar exclusão acidental de arquivos no Drive
        # 'rclone sync' é mais agressivo e espelha o conteúdo, o que pode ser perigoso
        if not run_command(f"rclone copy --config {RCLONE_CONFIG_PATH} {local_folder_path} {drive_target_path}"):
            log_message(f"Falha ao sincronizar a pasta \'{folder}\' para o Google Drive.")
            send_notification(f"Falha ao sincronizar a pasta \'{folder}\' para o Google Drive.")
            # Continuar com as outras pastas mesmo se uma falhar

    log_message("Sincronização concluída.")
    send_notification("Sincronização GitHub para Google Drive concluída com sucesso!")

if __name__ == "__main__":
    sync_github_to_drive()
