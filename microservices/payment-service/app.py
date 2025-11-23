from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import stripe
import random
import string
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
import time  # для задержки

load_dotenv(dotenv_path=r"D:\VsProject\hotel_booking_system\microservices\payment-service\.env")

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5000", "http://localhost:5000"], supports_credentials=True)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

# Твой mail.ru (остаётся)
MAILRU_SMTP_HOST = "smtp.mail.ru"
MAILRU_SMTP_PORT = 465
MAILRU_EMAIL = os.getenv("MAILRU_EMAIL")
MAILRU_APP_PASSWORD = os.getenv("MAILRU_APP_PASSWORD")

def generate_ticket():
    prefix = "HB-"
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=9))
    return prefix + code[:4] + code[4:].lower()

# Генерация уникального ID для письма (UUID + случайный код)
def generate_message_id():
    uuid_part = str(uuid.uuid4())[:8]  # короткий UUID
    random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))  # случайный 6-символьный ID
    return f"{uuid_part}-{random_code}"

def send_email(to_email, guest_name, hotel_name, date_from, date_to, total, ticket):
    if not MAILRU_EMAIL or not MAILRU_APP_PASSWORD:
        print("Mail.ru не настроен — письмо не отправлено")
        return

    # УНИКАЛЬНЫЙ ID ДЛЯ ЭТОГО ПИСЬМА
    message_id = generate_message_id()
    random_delay = random.uniform(1, 3)  # случайная задержка 1-3 сек

    msg = MIMEMultipart()
    msg['From'] = f"HotelBook <{MAILRU_EMAIL}>"
    msg['To'] = to_email
    msg['Subject'] = f"Бронь подтверждена! #{ticket} (ID: {message_id})"  # уникальная тема

    body = f"""
Здравствуйте, {guest_name}!

Ваша бронь в отеле "{hotel_name}" успешно оплачена!

Заезд: {date_from}
Выезд: {date_to}
Сумма: {total:.2f} USD
Тикет: {ticket}

Уникальный ID брони: {message_id}  # ← случайный ID для уникальности

Спасибо, что выбрали HotelBook!

С уважением,
Команда HotelBook
https://hotelbook.md

[UUID: {str(uuid.uuid4())}]  # ← полный UUID для антиспама
    """.strip()

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        print(f"Отправка уникального письма на {to_email} (ID: {message_id})... задержка {random_delay:.1f}с")
        time.sleep(random_delay)  # задержка, чтобы не было подозрительно

        server = smtplib.SMTP_SSL(MAILRU_SMTP_HOST, MAILRU_SMTP_PORT)
        server.login(MAILRU_EMAIL, MAILRU_APP_PASSWORD)
        server.sendmail(MAILRU_EMAIL, to_email, msg.as_string())
        server.quit()

        print(f"ПИСЬМО УСПЕШНО ОТПРАВЛЕНО с уникальным ID {message_id} на {to_email}!")
    except Exception as e:
        print(f"Ошибка mail.ru: {e}")

# SMS — вывод в консоль с UUID (потом легко добавить локальный способ)
def send_sms(phone, guest_name, hotel_name, ticket, date_from="неизвестно"):
    sms_uuid = str(uuid.uuid4())[:8]
    message = f"SMS ID {sms_uuid}: HotelBook: Бронь #{ticket} в {hotel_name} подтверждена! Заезд {date_from}. Спасибо, {guest_name.split()[0]}!"
    print(f"[SMS ОТПРАВЛЕНО] На {phone}: {message}")
    # Здесь можно добавить локальный модем или Android-бот, если нужно

@app.route("/")
def index():
    return "Payment Service работает! Порт 5002"

@app.route("/create-payment", methods=["POST"])
def create_payment():
    data = request.json
    chosen_currency = data.get("currency", "usd")

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(float(data["total_amount_usd"]) * 100),
            currency=chosen_currency,
            metadata={
                "hotel_id": data["hotel_id"],
                "hotel_name": data["hotel_name"],
                "date_from": data["date_from"],
                "date_to": data["date_to"],
                "user_id": data.get("user_id", "unknown"),
                "guest_name": f"{data['guest']['first_name']} {data['guest']['last_name']}",
                "guest_email": data["guest"]["email"],
                "guest_phone": data["guest"]["phone"],
                "currency": chosen_currency
            }
        )

        return jsonify({
            "client_secret": intent.client_secret,
            "payment_url": request.url_root.rstrip("/") + "/pay/" + intent.id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/pay/<payment_intent_id>")
def pay_page(payment_intent_id):
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        meta = intent.metadata
        currency = intent.currency.upper()

        if intent.status == "succeeded":
            ticket = generate_ticket()

            guest_name = meta.get("guest_name", "Гость")
            hotel_name = meta.get("hotel_name", "Отель")
            email = meta.get("guest_email", "test@hotelbook.test")
            phone = meta.get("guest_phone", "+37300000000")
            date_from = meta.get("date_from", "неизвестно")

            send_email(email, guest_name, hotel_name, meta.get("date_from"), meta.get("date_to"), intent.amount / 100, ticket)
            send_sms(phone, guest_name, hotel_name, ticket, date_from)

            return render_template("success.html", ticket=ticket, hotel_name=hotel_name, guest_name=guest_name)

        return render_template("payment.html",
                               client_secret=intent.client_secret,
                               publishable_key=PUBLISHABLE_KEY,
                               hotel_name=request.args.get("hotel_name") or meta.get("hotel_name", ""),
                               date_from=request.args.get("date_from") or meta.get("date_from", ""),
                               date_to=request.args.get("date_to") or meta.get("date_to", ""),
                               total=f"{intent.amount / 100:.2f}",
                               amount=f"{intent.amount / 100:.2f}",
                               currency=currency,
                               guest_name=request.args.get("guest_name") or meta.get("guest_name", ""),
                               lang=request.args.get("lang", "rus"))
    except Exception as e:
        print(f"Ошибка в pay_page: {e}")
        return "Ошибка платежа", 400

if __name__ == "__main__":
    print("Запуск Payment Service на порту 5002...")
    app.run(port=5002, debug=True)