import os
import re
import statistics
import requests
from flask import Flask, request

TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

historique = []


def envoyer(chat_id, texte):
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={"chat_id": chat_id, "text": texte}
    )


def analyser(valeurs):
    if not valeurs:
        return "❌ Aucun multiplicateur valide trouvé."

    moyenne = sum(valeurs) / len(valeurs)
    mediane = statistics.median(valeurs)
    minimum = min(valeurs)
    maximum = max(valeurs)

    bas = sum(x < 1.50 for x in valeurs)
    moyens = sum(1.50 <= x < 2.00 for x in valeurs)
    hauts = sum(2.00 <= x < 5.00 for x in valeurs)
    tres_hauts = sum(x >= 5.00 for x in valeurs)

    texte = (
        "📊 ANALYSE HAM$TER\n\n"
        f"🎲 Tours analysés : {len(valeurs)}\n"
        f"📈 Moyenne : {moyenne:.2f}x\n"
        f"📍 Médiane : {mediane:.2f}x\n"
        f"⬇️ Minimum : {minimum:.2f}x\n"
        f"⬆️ Maximum : {maximum:.2f}x\n\n"
        "📌 RÉPARTITION\n"
        f"🔴 < 1.50x : {bas} ({bas/len(valeurs)*100:.1f}%)\n"
        f"🟡 1.50x–1.99x : {moyens} ({moyens/len(valeurs)*100:.1f}%)\n"
        f"🟢 2x–4.99x : {hauts} ({hauts/len(valeurs)*100:.1f}%)\n"
        f"🔥 ≥ 5x : {tres_hauts} ({tres_hauts/len(valeurs)*100:.1f}%)\n\n"
        "⚠️ IMPORTANT\n"
        "Les crashs sont aléatoires. Cette analyse décrit les résultats "
        "passés et ne permet pas de connaître le prochain multiplicateur."
    )

    return texte


def traiter_message(message):
    chat_id = message["chat"]["id"]
    texte = message.get("text", "").strip()

    if texte == "/start":
        envoyer(
            chat_id,
            "🤖 HAM$TER ANALYZER\n\n"
            "Bienvenue !\n\n"
            "📊 Envoie-moi plusieurs multiplicateurs, par exemple :\n"
            "1.56 3.16 1.78 1.71 1.20 5.84\n\n"
            "Commandes disponibles :\n"
            "/start - Menu principal\n"
            "/stats - Statistiques de l'historique\n"
            "/historique - Voir les derniers résultats\n"
            "/effacer - Effacer l'historique\n"
            "/aide - Instructions\n\n"
            "⚠️ Ce bot analyse les données passées. "
            "Il ne prédit pas le prochain crash."
        )
        return

    if texte == "/aide":
        envoyer(
            chat_id,
            "📖 COMMENT UTILISER LE BOT\n\n"
            "Envoie simplement les multiplicateurs séparés par des espaces.\n\n"
            "Exemple :\n"
            "1.20 1.56 2.10 3.16 5.84\n\n"
            "Le bot calcule la moyenne, la médiane, le minimum, "
            "le maximum et la répartition des résultats."
        )
        return

    if texte == "/stats":
        if not historique:
            envoyer(chat_id, "📊 Aucun résultat enregistré pour le moment.")
        else:
            envoyer(chat_id, analyser(historique))
        return

    if texte == "/historique":
        if not historique:
            envoyer(chat_id, "📜 Historique vide.")
        else:
            derniers = historique[-30:]
            envoyer(
                chat_id,
                "📜 30 DERNIERS RÉSULTATS\n\n"
                + "  ".join(f"{x:.2f}x" for x in derniers)
            )
        return

    if texte == "/effacer":
        historique.clear()
        envoyer(chat_id, "🗑️ Historique effacé.")
        return

    # Recherche des nombres dans le message
    nombres = re.findall(r"\d+(?:[.,]\d+)?", texte)

    if nombres:
        valeurs = [float(x.replace(",", ".")) for x in nombres]
        valeurs = [x for x in valeurs if x >= 1.00]

        if valeurs:
            historique.extend(valeurs)
            envoyer(chat_id, analyser(valeurs))
            return

    envoyer(
        chat_id,
        "❓ Je n'ai pas trouvé de multiplicateurs.\n\n"
        "Exemple :\n"
        "1.56 3.16 1.78 1.71 1.20 5.84"
    )


@app.route("/", methods=["GET"])
def accueil():
    return "HAM$TER ANALYZER fonctionne ✅"


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True)

    if update and "message" in update:
        traiter_message(update["message"])

    return "OK"


def configurer_webhook():
    render_url = os.environ.get("RENDER_EXTERNAL_URL")

    if not TOKEN:
        print("❌ BOT_TOKEN n'est pas configuré.")
        return

    if render_url:
        webhook_url = render_url.rstrip("/") + "/webhook"

        resultat = requests.post(
            f"{BASE_URL}/setWebhook",
            json={"url": webhook_url}
        )

        print("Webhook :", resultat.text)
    else:
        print("⚠️ RENDER_EXTERNAL_URL absent.")


if __name__ == "__main__":
    configurer_webhook()

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
