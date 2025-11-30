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
    r = requests.post(PPLX_URL, json=payload, headers=headers)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def send_message(chat_id, text):
    requests.post(f"{TG_URL}/sendMessage", json={"chat_id": chat_id, "text": text})


def send_menu(chat_id):
    buttons = {
        "keyboard": [
            [{"text": "Спросить нейросеть"}],
            [{"text": "Помощь"}]
        ],
        "resize_keyboard": True
    }
    requests.post(f"{TG_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": "Добро пожаловать! Выберите действие:",
        "reply_markup": buttons
    })


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if text == "/start":
            send_menu(chat_id)
        elif text == "Помощь":
            send_message(chat_id, "Напишите любой вопрос — я задам его Perplexity AI.")
        elif text == "Спросить нейросеть":
            send_message(chat_id, "Введите ваш вопрос.")
        else:
            try:
                answer = ask_perplexity(text)
            except Exception as e:
                answer = f"Ошибка: {e}"

            send_message(chat_id, answer)

    return "ok"
