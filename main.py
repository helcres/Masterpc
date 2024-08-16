import time
import requests
from random import choice
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from urllib.parse import quote
from bs4 import BeautifulSoup
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

# Lista ampliada de User-Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
]

PROXIES = [
    "http://xzJoPZOELjvXOpQtKPXz217nvoytQK:zF0g32D7fYQbvTTY@proxy.digiproxy.cc:8082",
    "http://xzJoPZOELjvXOpQtKPXz217nvoytQK:zF0g32D7fYQbvTTY@proxy.digiproxy.cc:8082",
    "http://xzJoPZOELjvXOpQtKPXz217nvoytQK:zF0g32D7fYQbvTTY@proxy.digiproxy.cc:8082",
    "http://xzJoPZOELjvXOpQtKPXz217nvoytQK:zF0g32D7fYQbvTTY@proxy.digiproxy.cc:8082",
    "http://xzJoPZOELjvXOpQtKPXz217nvoytQK:zF0g32D7fYQbvTTY@proxy.digiproxy.cc:8082",
]

def check_instagram_status(username):
    headers = {
        'User-Agent': choice(USER_AGENTS)
    }
    proxy = {
        'http': choice(PROXIES),
        'https': choice(PROXIES),
    }
    url = f'https://www.instagram.com/{quote(username)}/'
    try:
        response = requests.get(url, headers=headers, proxies=proxy, timeout=10)
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
        print(f"Error en la solicitud a Instagram: {e}")
        return 'Error'

def check_tinder_status(username):
    # Implementa la lógica real aquí
    return 'Simulated Status'

@app.route('/check_status', methods=['POST'])
def check_status():
    if not service:
        return jsonify({'status': 'Error', 'details': 'El servicio de Google Sheets no está disponible'})

    sheet = service.spreadsheets()
    try:
        result_instagram = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_INSTAGRAM).execute()
        usernames_instagram = result_instagram.get('values', [])
        result_tinder = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_TINDER).execute()
        usernames_tinder = result_tinder.get('values', [])

        statuses_instagram = []
        statuses_tinder = []
        summaries = []

        for i in range(len(usernames_instagram)):
            ig_status = check_instagram_status(usernames_instagram[i][0] if usernames_instagram[i] else '')
            t_status = check_tinder_status(usernames_tinder[i][0] if usernames_tinder[i] else '')

            statuses_instagram.append([ig_status])
            statuses_tinder.append([t_status])

            if ig_status == 'Banned/Deleted' and t_status == 'Banned/Deleted':
                summaries.append(['Both Banned'])
            elif ig_status == 'Active' and t_status == 'Active':
                summaries.append(['Both Active'])
            else:
                summaries.append(['Mixed Status'])

            time.sleep(10)

        sheet.values().update(spreadsheetId=SPREADSHEET_ID, range='I3:I28', valueInputOption='RAW', body={'values': statuses_instagram}).execute()
        sheet.values().update(spreadsheetId=SPREADSHEET_ID, range='K3:K28', valueInputOption='RAW', body={'values': statuses_tinder}).execute()
        sheet.values().update(spreadsheetId=SPREADSHEET_ID, range='L3:L28', valueInputOption='RAW', body={'values': summaries}).execute()

        return jsonify({'status': 'Success'})

    except HttpError as error:
        return jsonify({'status': 'Error', 'details': str(error)})
    except Exception as e:
        return jsonify({'status': 'Error', 'details': f'Error desconocido: {e}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
