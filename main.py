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
try:
    creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_json:
        raise ValueError("La variable de entorno GOOGLE_APPLICATION_CREDENTIALS no está configurada")
    
    # Cargar las credenciales desde el JSON en la variable de entorno
    creds_info = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(creds_info)
    
    # Construir el servicio de Google Sheets
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    service = build('sheets', 'v4', credentials=creds)
except Exception as e:
    print(f"Error al cargar las credenciales de Google: {e}")
    service = None

# ID y nombre de la hoja de cálculo
SPREADSHEET_ID = '1xmBGzom4JuLMq--7OgJGRa48BucODBcuygo0B0-H6js'
RANGE_INSTAGRAM = 'B3:B28'  # Rango para usuarios de Instagram
RANGE_TINDER = 'J3:J28'     # Rango para usuarios de Tinder

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

# Lista de proxies actualizada
PROXIES = [
    "http://xzJoPZOELjvXOpQtKPXz217nvoytQK:zF0g32D7fYQbvTTY@proxy.digiproxy.cc:8082",
    "http://xzJoPZOELjvXOpQtKPXz217nvoytQK:zF0g32D7fYQbvTTY@proxy.digiproxy.cc:8082",
    "http://xzJoPZOELjvXOpQtKPXz217nvoytQK:zF0g32D7fYQbvTTY@proxy.digiproxy.cc:8082",
    "http://xzJoPZOELjvXOpQtKPXz217nvoytQK:zF0g32D7fYQbvTTY@proxy.digiproxy.cc:8082",
    "http://xzJoPZOELjvXOpQtKPXz217nvoytQK:zF0g32D7fYQbvTTY@proxy.digiproxy.cc:8082",
]

def verificar_instagram(usuario):
    """Verifica el estado de un usuario de Instagram."""
    headers = {
        'User-Agent': choice(USER_AGENTS)
    }
    proxy = {
        'http': choice(PROXIES),
        'https': choice(PROXIES),
    }
    url = f'https://www.instagram.com/{quote(usuario)}/'
    try:
        response = requests.get(url, headers=headers, proxies=proxy, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            if 'Page Not Found' in soup.title.text:
                return 'Baneada/Eliminada'
            else:
                return 'Activa'
        elif response.status_code == 404:
            return 'Baneada/Eliminada'
        else:
            return 'Desconocido'
    except requests.exceptions.RequestException:
        return 'Error'

def verificar_tinder(usuario):
    """Verifica el estado de un usuario de Tinder."""
    url = f"https://tinder.com/@{quote(usuario)}"
    headers = {
        'User-Agent': choice(USER_AGENTS)
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag and usuario.lower() in title_tag.text.lower():
                return "Activa"
            else:
                return "Baneada"
        else:
            return "Baneada"
    except requests.exceptions.RequestException as e:
        print(f"Error al verificar {usuario}: {e}")
        return "Error al verificar"

@app.route('/check_status', methods=['POST'])
def check_status():
    if not service:
        return jsonify({'status': 'Error', 'details': 'El servicio de Google Sheets no está disponible'})

    sheet = service.spreadsheets()
    try:
        # Obtener usuarios de Instagram
        result_instagram = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_INSTAGRAM).execute()
        usernames_instagram = [u[0] for u in result_instagram.get('values', [])]

        # Obtener usuarios de Tinder
        result_tinder = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_TINDER).execute()
        usernames_tinder = [u[0] for u in result_tinder.get('values', [])]

        return jsonify({'status': 'Success'})

    except HttpError as error:
        return jsonify({'status': 'Error', 'details': str(error)})

@app.route('/update_instagram_status', methods=['POST'])
def update_instagram_status():
    if not service:
        return jsonify({'status': 'Error', 'details': 'El servicio de Google Sheets no está disponible'})

    sheet = service.spreadsheets()
    try:
        # Obtener usuarios de Instagram
        result_instagram = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_INSTAGRAM).execute()
        usernames_instagram = [u[0] for u in result_instagram.get('values', [])]

        statuses_instagram = []

        for username in usernames_instagram:
            status = verificar_instagram(username)
            statuses_instagram.append([status])
            time.sleep(10)  # Esperar 10 segundos entre verificaciones

        # Guardar los resultados en la hoja de cálculo
        sheet.values().update(spreadsheetId=SPREADSHEET_ID, range='I3:I28', valueInputOption='RAW', body={'values': statuses_instagram}).execute()

        return jsonify({'status': 'Success'})

    except HttpError as error:
        return jsonify({'status': 'Error', 'details': str(error)})

@app.route('/update_tinder_status', methods=['POST'])
def update_tinder_status():
    if not service:
        return jsonify({'status': 'Error', 'details': 'El servicio de Google Sheets no está disponible'})

    sheet = service.spreadsheets()
    try:
        # Obtener usuarios de Tinder
        result_tinder = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_TINDER).execute()
        usernames_tinder = [u[0] for u in result_tinder.get('values', [])]

        statuses_tinder = []

        for username in usernames_tinder:
            status = verificar_tinder(username)
            statuses_tinder.append([status])
            time.sleep(10)  # Esperar 10 segundos entre verificaciones

        # Guardar los resultados en la hoja de cálculo
        sheet.values().update(spreadsheetId=SPREADSHEET_ID, range='K3:K28', valueInputOption='RAW', body={'values': statuses_tinder}).execute()

        return jsonify({'status': 'Success'})

    except HttpError as error:
        return jsonify({'status': 'Error', 'details': str(error)})

if __name__ == '__main__':
    app.run(debug=True)
