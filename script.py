import os
import io
import datetime
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build_from_document

# Scopes pour accéder aux Google Photos
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

# Charger les identifiants OAuth 2.0
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

# Télécharger les photos entre deux dates
def download_photos_between_dates(service, start_date, end_date, download_folder):
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    next_page_token = None
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

        items = results.get('mediaItems', [])
        if not items:
            print('Aucune photo trouvée.')
            break

        for item in items:
            file_name = item['filename']
            base_url = item['baseUrl']
            photo_response = requests.get(f'{base_url}=d')

            with open(os.path.join(download_folder, file_name), 'wb') as f:
                f.write(photo_response.content)
                print(f'Téléchargé: {file_name}')

        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break

def get_date_input(prompt):
    while True:
        try:
            date_input = input(prompt)
            return datetime.datetime.strptime(date_input, '%d-%m-%Y')
        except ValueError:
            print("Format incorrect. Veuillez entrer la date au format JJ-MM-AAAA.")

def main():
    creds = authenticate_google_photos()

    # Charger le document de découverte à partir du fichier
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

if __name__ == '__main__':
    main()
