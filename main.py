import time
import requests
from random import choice, randint
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from urllib.parse import quote
from bs4 import BeautifulSoup
import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Obtener credenciales desde variables de entorno
SERVICE_ACCOUNT_INFO = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT'))
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

creds = service_account.Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO, scopes=SCOPES)

service = build('sheets', 'v4', credentials=creds)

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
    "http://xzJoPZOELjvXOpQtKPXz217nvoytQK:zF0g32D7fYQbvTTY@proxy.digiproxy.cc:8082"
]

def get_values(range_name):
    """Obtiene los nombres de usuario desde Google Sheets."""
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        values = result.get('values', [])
        return values
    except HttpError as err:
        print(f'Error al obtener valores: {err}')
        return []

def update_values(range_name, data):
    """Actualiza los resultados en Google Sheets."""
    try:
        sheet = service.spreadsheets()
        body = {'values': data}
        result = sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=range_name,
                                       valueInputOption='RAW', body=body).execute()
        print(f'{result.get("updatedCells")} celdas actualizadas.')
    except HttpError as err:
        print(f'Error al actualizar valores: {err}')

def verificar_instagram(usuario, intento=1):
    """Verifica el estado de un usuario de Instagram."""
    url = f"https://www.instagram.com/{quote(usuario)}/"
    headers = {
        'User-Agent': choice(USER_AGENTS)
    }
    proxy = {"http": choice(PROXIES), "https": choice(PROXIES)}

    try:
        response = requests.get(url, headers=headers, proxies=proxy, timeout=10)
        if response.status_code == 200:
            return "Activa"
        elif response.status_code == 404:
            return "Baneada"
        elif response.status_code == 429:
            if intento <= 5:  # Limitar a 5 intentos antes de fallar
                espera = 2 ** intento * randint(10, 20)  # Backoff exponencial
                print(f"Rate limit reached. Retrying in {espera} seconds (Attempt {intento}).")
                time.sleep(espera)
                return verificar_instagram(usuario, intento + 1)
            else:
                return "Error: Límite de solicitudes alcanzado"
        else:
            print(f"Código de estado inesperado {response.status_code} para el usuario {usuario}")
            return "Error desconocido"
    except requests.exceptions.RequestException as e:
        print(f"Error al verificar {usuario}: {e}")
        return "Error al verificar"

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

def main():
    """Función principal que ejecuta el flujo completo."""
    instagram_usuarios = get_values(RANGE_INSTAGRAM)
    tinder_usuarios = get_values(RANGE_TINDER)

    if instagram_usuarios and tinder_usuarios:
        instagram_resultados = []
        tinder_resultados = []
        resumen_resultados = []

        for i, (insta_usuario, tinder_usuario) in enumerate(zip(instagram_usuarios, tinder_usuarios)):
            # Verificación de Instagram
            insta_status = verificar_instagram(insta_usuario[0])
            instagram_resultados.append([insta_status])

            # Verificación de Tinder
            tinder_status = verificar_tinder(tinder_usuario[0])
            tinder_resultados.append([tinder_status])

            # Resumen
            if insta_status == "Activa" and tinder_status == "Activa":
                resumen = "Ambos activos"
            else:
                resumen = "Uno o ambos baneados"
            resumen_resultados.append([resumen])

            print(f'Verificado Instagram {insta_usuario[0]}: {insta_status}')
            print(f'Verificado Tinder {tinder_usuario[0]}: {tinder_status}')

            time.sleep(randint(15, 25))  # rango de espera aleatorio 15/25

        # Actualización de resultados
        update_values('I3:I28', instagram_resultados)
        update_values('K3:K28', tinder_resultados)
        update_values('L3:L28', resumen_resultados)
    else:
        print("No se pudieron obtener los valores.")

@app.route('/verificar', methods=['POST'])
def verificar():
    main()  # Ejecuta la función principal que ya tienes
    return jsonify({"status": "Verificación completada"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
