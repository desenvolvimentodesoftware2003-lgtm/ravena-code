pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Escopos necessários para ler e renomear arquivos
SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = 'token.json'

def get_credentials():
    creds = None
    # O arquivo token.json armazena seus tokens de acesso após a primeira execução
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Se não houver credenciais válidas, realiza o login via navegador
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salva as credenciais para a próxima vez
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return creds

def executar_organizacao(folder_id):
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)

    # Buscar arquivos
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name)"
    ).execute()
    
    files = results.get('files', [])
    files.sort(key=lambda x: x['name'])
    
    total = len(files)
    print(f"Encontrados {total} arquivos. Iniciando renomeação...")

    for i, file in enumerate(files):
        novo_nome = f"RAVENA_DOC_{total - i:03d}_{file['name']}"
        service.files().update(fileId=file['id'], body={'name': novo_nome}).execute()
        print(f"Renomeado: {file['name']} -> {novo_nome}")

if __name__ == '__main__':
    # Cole o ID da pasta do seu drive aqui
    ID_DA_PASTA = 'INSIRA_O_ID_DA_PASTA_AQUI' 
    executar_organizacao(ID_DA_PASTA)