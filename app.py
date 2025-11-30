import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
PERPLEXITY_API_KEY = os.environ["PERPLEXITY_API_KEY"]

TG_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
PPLX_URL = "https://api.perplexity.ai/chat/completions"


def ask_perplexity(prompt: str) -> str:
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300
    }

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(PPLX_URL, json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def send_message(chat_id, text):
    try:
        requests.post(
            f"{TG_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15
        )
    except Exception:
        pass


def send_menu(chat_id):
    buttons = {
        "keyboard": [
            [{"text": "Спросить нейросеть"}],
            [{"text": "Помощь"}]
        ],
        "resize_keyboard": True
    }

    requests.post(
        f"{TG_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": "Добро пожаловать! Выберите действие:",
            "reply_markup": buttons
        },
        timeout=15
    )


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    message = update.get("message")
    if not message:
        return "ok"

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return "ok"

    text = message.get("text", "").strip()

    if text == "/start":
        send_menu(chat_id)
    elif text == "Помощь":
        send_message(chat_id, "Напишите любой вопрос — я задам его Perplexity AI.")
    elif text == "Спросить нейросеть":
        send_message(chat_id, "Введите ваш вопрос.")
    elif text:
        try:
            answer = ask_perplexity(text)
        except Exception as e:
            answer = f"Ошибка: {e}"
        send_message(chat_id, answer)

    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
