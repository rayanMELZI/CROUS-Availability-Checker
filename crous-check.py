import os
import threading
import time
import requests
import smtplib
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
MDP = os.getenv("EMAIL_PASSWORD")
DESTINATAIRE = os.getenv("SEND_TO")
PORT = int(os.environ.get("PORT", 5000))

URL_LYON = "https://trouverunlogement.lescrous.fr/tools/41/search?bounds=4.7718134_45.8082628_4.8983774_45.7073666"
URL_VILLEURBANNE = "https://trouverunlogement.lescrous.fr/tools/41/search?bounds=4.8583622_45.7955875_4.9212614_45.7484524"

app = Flask(__name__)

def check_disponibilite(url, ville):
    try:
        response = requests.get(url)
        if "Aucun logement" in response.text:
            print(f"❌ Aucun logement a {ville}")
        else:
            print(f"✅ Logement(s) a {ville} ! Envoi email...")
            send_email(url, ville)
    except Exception as e:
        print(f"⚠️ Erreur pour {ville}:", e)

def send_email(url, ville):
    subject = f"Logement CROUS disponible a {ville}"
    body = f"Vite ici : {url}"
    msg = f"Subject: {subject}\n\n{body}"
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL, MDP)
        server.sendmail(EMAIL, DESTINATAIRE, msg)
        print("📧 Email envoyé !")

def bot_loop():
    while True:
        try:
            print(f"🔄 Vérification en cours...")
            check_disponibilite(URL_LYON, "Lyon")
            check_disponibilite(URL_VILLEURBANNE, "Villeurbanne")
            time.sleep(60*5) # 5 minutes1
        except:
            print("✖️ Error")
            time.sleep(10)  # 10 seconds

@app.route("/")
def index():
    return "🤖 Le bot tourne !"

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
