import os
import threading
import time
import requests
import smtplib
from flask import Flask
from dotenv import load_dotenv

from flask import request

import json

USERS_FILE = "users.json"

def save_user(chat_id):
    try:
        if not os.path.exists(USERS_FILE):
            with open(USERS_FILE, "w") as f:
                json.dump([], f)

        with open(USERS_FILE, "r") as f:
            users = json.load(f)

        if chat_id not in users:
            users.append(chat_id)
            with open(USERS_FILE, "w") as f:
                json.dump(users, f)
            add_log(f"👤 Nouvel utilisateur enregistré : {chat_id}")
    except Exception as e:
        add_log(f"❌ Erreur lors de l'enregistrement de l'utilisateur : {e}")


# Load environment variables from .env
load_dotenv()

# Email configuration
EMAIL = os.getenv("EMAIL")
MDP = os.getenv("EMAIL_PASSWORD")
DESTINATAIRE = os.getenv("SEND_TO")
PORT = int(os.environ.get("PORT", 5000))

# URLs à vérifier
# URL_LYON = "https://trouverunlogement.lescrous.fr/tools/41/search"
URL_LYON = "https://trouverunlogement.lescrous.fr/tools/41/search?bounds=4.7718134_45.8082628_4.8983774_45.7073666"
URL_VILLEURBANNE = "https://trouverunlogement.lescrous.fr/tools/41/search?bounds=4.8583622_45.7955875_4.9212614_45.7484524"
URL_PARIS = "https://trouverunlogement.lescrous.fr/tools/41/search?bounds=1.4462445_49.241431_3.5592208_48.1201456"
# URL_PARIS = "https://trouverunlogement.lescrous.fr/tools/41/search"

# Logs (max 100 lignes)
logs = []

def add_log(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"{timestamp} — {message}"
    print(full_message)
    logs.append(full_message)
    if len(logs) > 100:
        logs.pop(0)

# Email sending
def send_email(url, ville):
    subject = f"Logement CROUS disponible a {ville}"
    body = f"Vite ! Verifie ici : {url}"
    msg = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL, MDP)
            server.sendmail(EMAIL, DESTINATAIRE, msg)
        add_log(f"📧 Email envoyé pour {ville}")
    except Exception as e:
        add_log(f"❌ Erreur lors de l'envoi d'email : {e}")

#telegram notification
def send_telegram(message, ville):
    try:
        token = os.getenv(f"{ville}_TELEGRAM_TOKEN")
        chat_id = os.getenv(f"{ville}_TELEGRAM_CHAT_ID")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        requests.post(url, data=payload)
        add_log("📲 Notification Telegram envoyée.")
    except Exception as e:
        add_log(f"⚠️ Erreur envoi Telegram : {e}")

def send_message(chat_id, message):
    try:
        token = os.getenv("Paris_TELEGRAM_TOKEN")  # on peut réutiliser n’importe lequel
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        requests.post(url, data=payload)
    except Exception as e:
        add_log(f"❌ Erreur envoi message /start : {e}")



# Vérification d'une ville
def check_disponibilite(url, ville):
    try:
        response = requests.get(url)
        if "Aucun logement" in response.text:
            add_log(f"❌ Aucun logement à {ville}")
        else:
            add_log(f"✅ Logement(s) trouvé(s) à {ville} ! Envoi d'e-mail...")
            if ville == "Villeurbanne" or ville == "Lyon":
                send_email(url, ville)
            send_telegram(f"🚨 Logement dispo à {ville} ! Vérifie vite : {url}", ville)
    except Exception as e:
        add_log(f"⚠️ Erreur lors de la vérification à {ville} : {e}")

# Boucle principale du bot
def bot_loop():
    while True:
        check_disponibilite(URL_LYON, "Lyon")
        check_disponibilite(URL_VILLEURBANNE, "Villeurbanne")
        check_disponibilite(URL_PARIS, "Paris")
        time.sleep(300)  # 5 minutes

def hourly_ping():
    while True:
        now = time.strftime('%Y-%m-%d %H:%M')
        send_telegram(f"🟢 Le bot CROUS tourne toujours ({now})", "Lyon")
        send_telegram(f"🟢 Le bot CROUS tourne toujours ({now})", "Villeurbanne")
        send_telegram(f"🟢 Le bot CROUS tourne toujours ({now})", "Paris")
        time.sleep(3600)  # 1 heure


# Flask web server
app = Flask(__name__)

@app.route("/")
def index():
    return f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="30">
        <title>Logs du bot CROUS</title>
    </head>
    <body style="font-family: monospace;">
        <h2>📝 Logs du bot CROUS</h2>
        <pre>{chr(10).join(logs)}</pre>
    </body>
    </html>
    """


# @app.route("/webhook", methods=["POST"])
# def webhook():
#     data = request.json
#     try:
#         if "message" in data:
#             message = data["message"]
#             text = message.get("text", "")
#             chat_id = message["chat"]["id"]

#             if text == "/start":
#                 save_user(chat_id)
#                 send_message(chat_id, "✅ Abonnement activé. Tu recevras les alertes automatiquement.")
#             else:
#                 send_message(chat_id, "🤖 Envoie /start pour t'abonner aux alertes logement CROUS.")
#         return "ok"
#     except Exception as e:
#         add_log(f"❌ Erreur webhook: {e}")
#         return "error"

# Lancement
if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    threading.Thread(target=hourly_ping, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)