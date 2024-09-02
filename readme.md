# Google Photos Downloader
Ce projet fournit un script Python pour télécharger des photos depuis Google Photos entre deux dates, gérer les erreurs de téléchargement, et réessayer les téléchargements échoués.

## Fonctionnalités
- Télécharger des Photos : Récupère des photos de Google Photos entre des dates spécifiées.
- Gérer les Erreurs : Enregistre les tentatives de téléchargement échouées pour un examen ultérieur.
- Réessayer les Téléchargements Échoués : Tente à nouveau de télécharger les photos qui ont échoué lors de la première tentative.

## Prérequis
- Python 3.x : Assurez-vous que Python 3.x est installé sur votre système.
- Identifiants API Google : Vous devez configurer les identifiants OAuth 2.0 pour accéder à l'API Google Photos.
- Bibliothèques Python Nécessaires : Installez les bibliothèques nécessaires à l'aide de pip.

## Installation
Cloner le Répertoire :

```
git clone https://github.com/MatBonnin/GooglePhoto2dates.git
cd GooglePhoto2dates
```
Installer les Bibliothèques Python Nécessaires :

```
pip install -r requirements.txt
```
Configurer l'API Google :

1. Aller à la Console Google Cloud.
2. Créer un nouveau projet ou sélectionner un existant.
3. Activer l'API Google Photos Library.
4. Créer des identifiants OAuth 2.0 (Client ID et Client Secret).
5. Télécharger le fichier credentials.json et le placer dans le répertoire du projet.

## Utilisation
Authentifier et Télécharger des Photos : Exécutez le script pour vous authentifier avec Google Photos et télécharger des photos entre deux dates :

```
python google_photos_downloader.py
```
Vous serez invité à entrer les dates de début et de fin au format JJ-MM-AAAA.

Réessayer les Téléchargements Échoués : Après le téléchargement initial, vous pouvez réessayer de télécharger les photos échouées en exécutant :

```
python google_photos_downloader.py --retry
```

## Détails du Script
/google_photos_downloader.py

**/authenticate_google_photos()** : Gère l'authentification de l'API Google Photos et la gestion des tokens.

**/download_photo(item, download_folder, failed_items, max_retries=3, timeout=30)** : Télécharge une photo unique et gère les tentatives en cas d'échec.

**/download_photos_between_dates(service, start_date, end_date, download_folder)**: Télécharge toutes les photos entre les dates spécifiées et consigne les échecs de téléchargement.

**/retry_failed_downloads(download_folder)** : Réessaie de télécharger les photos qui ont échoué lors du premier essai.

**/get_date_input(prompt)** : Invite l'utilisateur à saisir les dates au format JJ-MM-AAAA.

**/main()** : Fonction principale pour gérer le processus de téléchargement et les tentatives.

## Gestion des erreurs
Les téléchargements échoués sont consignés dans failed_downloads.json. Utilisez l'option de réessai pour tenter de télécharger à nouveau les photos échouées.


