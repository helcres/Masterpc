import time
import requests
from random import choice
from urllib.parse import quote
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Obtener las credenciales desde la variable de entorno
creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if not creds_json:
    raise ValueError("La variable de entorno GOOGLE_APPLICATION_CREDENTIALS no está configurada")

# Cargar las credenciales desde el JSON en la variable de entorno
try:
    creds_info = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(creds_info)
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    service = build('sheets', 'v4', credentials=creds)
except ValueError as e:
    print(f"Error al cargar las credenciales de Google: {e}")
    service = None
except Exception as e:
    print(f"Error desconocido: {e}")
    service = None

SPREADSHEET_ID = '1xmBGzom4JuLMq--7OgJGRa48BucODBcuygo0B0-H6js'
RANGE_INSTAGRAM = 'B3:B28'
RANGE_TINDER = 'J3:J28'

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
]

def check_instagram_status(username):
    headers = {
        'User-Agent': choice(USER_AGENTS)
    }
    url = f'https://www.instagram.com/{quote(username)}/'
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            if 'Page Not Found' in soup.title.text:
                return 'Banned/Deleted'
            else:
                return 'Active'
        elif response.status_code == 404:
            return 'Banned/Deleted'
        else:
            return 'Unknown'
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

def check_tinder_status(username):
    url = f"https://tinder.com/@{quote(username)}"
    headers = {
        'User-Agent': choice(USER_AGENTS)
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag and username.lower() in title_tag.text.lower():
                return "Active"
            else:
                return "Banned"
        else:
            return "Banned"
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

def update_google_sheet(range_name, values):
    if not service:
        print("El servicio de Google Sheets no está disponible")
        return
    
    try:
        sheet = service.spreadsheets()
        body = {'values': values}
        sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=range_name, valueInputOption='RAW', body=body).execute()
    except HttpError as error:
        print(f"Error al actualizar Google Sheets: {error}")

@app.route('/check_status', methods=['POST'])
def check_status():
    start_time = time.time()

    try:
        sheet = service.spreadsheets()

        # Obtener nombres de usuario de Instagram
        result_instagram = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_INSTAGRAM).execute()
        instagram_usernames = [row[0] for row in result_instagram.get('values', [])]

        # Obtener nombres de usuario de Tinder
        result_tinder = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_TINDER).execute()
        tinder_usernames = [row[0] for row in result_tinder.get('values', [])]

        # Ejecutar verificación de Instagram
        with ThreadPoolExecutor(max_workers=10) as executor:
            instagram_results = list(executor.map(check_instagram_status, instagram_usernames))
            time.sleep(2)

        # Ejecutar verificación de Tinder
        with ThreadPoolExecutor(max_workers=10) as executor:
            tinder_results = list(executor.map(check_tinder_status, tinder_usernames))
            time.sleep(2)

        # Actualizar Google Sheets con los resultados
        instagram_statuses = [[status] for status in instagram_results]
        tinder_statuses = [[status] for status in tinder_results]

        update_google_sheet('I3:I28', instagram_statuses)
        update_google_sheet('K3:K28', tinder_statuses)

    except Exception as e:
        return jsonify({'status': 'Error', 'details': f'Error desconocido: {e}'})

    end_time = time.time()
    total_time = end_time - start_time
    return jsonify({'status': 'Success', 'execution_time': f"{total_time:.2f} segundos"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
