import os
import datetime
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build_from_document
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import json
from requests.exceptions import RequestException

# Scopes pour accéder aux Google Photos
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
ERROR_LOG_FILE = 'failed_downloads.json'

def authenticate_google_photos():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def download_photo(item, download_folder, failed_items, max_retries=3, timeout=30):
    file_name = item['filename']
    base_url = item['baseUrl']
    file_path = os.path.join(download_folder, file_name)

    for attempt in range(max_retries):
        try:
            photo_response = requests.get(f'{base_url}=d', timeout=timeout)
            photo_response.raise_for_status()  # Vérifie les erreurs HTTP

            with open(file_path, 'wb') as f:
                f.write(photo_response.content)
            print(f"Photo téléchargée avec succès : {file_name}")
            return  # Sort de la fonction après un téléchargement réussi

        except RequestException as e:
            print(f"Erreur lors du téléchargement de {file_name} (tentative {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Échec du téléchargement de {file_name} après {max_retries} tentatives.")
                failed_items.append(item)  # Enregistre les items échoués
                return

def download_photos_between_dates(service, start_date, end_date, download_folder):
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    next_page_token = None
    items = []
    failed_items = []

    while True:
        results = service.mediaItems().search(body={
            "filters": {
                "dateFilter": {
                    "ranges": [{
                        "startDate": {
                            "year": start_date.year,
                            "month": start_date.month,
                            "day": start_date.day,
                        },
                        "endDate": {
                            "year": end_date.year,
                            "month": end_date.month,
                            "day": end_date.day,
                        }
                    }]
                }
            },
            "pageSize": 100,
            "pageToken": next_page_token
        }).execute()

        items.extend(results.get('mediaItems', []))
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break

    if not items:
        print('Aucune photo trouvée.')
        return

    with tqdm(total=len(items), desc="Téléchargement des photos", unit="photo") as progress_bar:
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_item = {executor.submit(download_photo, item, download_folder, failed_items): item for item in items}
            for future in as_completed(future_to_item):
                progress_bar.update(1)
                item = future_to_item[future]
                try:
                    future.result()  # Lève une exception s'il y en a une
                except Exception as e:
                    print(f"Erreur lors du téléchargement de {item['filename']}: {e}")

    # Enregistrement des photos échouées dans un fichier JSON
    if failed_items:
        with open(ERROR_LOG_FILE, 'w') as f:
            json.dump(failed_items, f, indent=4)
        print(f"Les photos échouées ont été enregistrées dans {ERROR_LOG_FILE}.")

def retry_failed_downloads(download_folder):
    if not os.path.exists(ERROR_LOG_FILE):
        print(f"Aucun fichier de log trouvé ({ERROR_LOG_FILE}). Rien à réessayer.")
        return

    with open(ERROR_LOG_FILE, 'r') as f:
        failed_items = json.load(f)

    if not failed_items:
        print("Aucune photo échouée à réessayer.")
        return

    print(f"Réessai du téléchargement des {len(failed_items)} photos échouées...")

    with tqdm(total=len(failed_items), desc="Réessai des téléchargements", unit="photo") as progress_bar:
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_item = {executor.submit(download_photo, item, download_folder, [], max_retries=3): item for item in failed_items}
            for future in as_completed(future_to_item):
                progress_bar.update(1)
                item = future_to_item[future]
                try:
                    future.result()  # Lève une exception s'il y en a une
                except Exception as e:
                    print(f"Erreur lors du réessai du téléchargement de {item['filename']}: {e}")

    # Nettoyage du fichier de log après les réessais
    os.remove(ERROR_LOG_FILE)
    print("Réessai terminé. Les photos échouées restantes ont été supprimées du fichier de log.")

def get_date_input(prompt):
    while True:
        try:
            date_input = input(prompt)
            return datetime.datetime.strptime(date_input, '%d-%m-%Y')
        except ValueError:
            print("Format incorrect. Veuillez entrer la date au format JJ-MM-AAAA.")

def main():
    creds = authenticate_google_photos()

    try:
        with open('photoslibrary_discovery.json', 'r') as discovery_file:
            service = build_from_document(discovery_file.read(), credentials=creds)
    except FileNotFoundError:
        print("Le fichier de découverte 'photoslibrary_discovery.json' est introuvable.")
        return

    start_date = get_date_input("Entrez la date de début (format JJ-MM-AAAA) : ")
    end_date = get_date_input("Entrez la date de fin (format JJ-MM-AAAA) : ")
    download_folder = 'photos_download'

    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    download_photos_between_dates(service, start_date, end_date, download_folder)

    # Permet de réessayer les téléchargements échoués après le téléchargement initial
    retry = input("Souhaitez-vous réessayer les photos échouées ? (oui/non) : ")
    if retry.lower() == 'oui':
        retry_failed_downloads(download_folder)

if __name__ == '__main__':
    main()
