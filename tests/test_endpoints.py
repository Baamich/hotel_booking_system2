import requests
import time

BASE = "http://localhost:5000"
AI = "http://localhost:5001"
PAY = "http://localhost:5002"

def test_main_app_alive():
    r = requests.get(BASE + "/")
    assert r.status_code in [200, 302]

def test_ai_assistant_ping():
    r = requests.post(AI + "/chat", json={"message": "ping", "lang": "eng"})
    assert r.status_code == 200
    assert r.json()["reply"] == "pong"

def test_ai_assistant_chat():
    r = requests.post(AI + "/chat", json={"message": "Привет", "lang": "rus"})
    assert r.status_code == 200
    assert "reply" in r.json()

def test_payment_service_alive():
    r = requests.get(PAY + "/")
    assert r.status_code == 200
    assert "Payment Service работает" in r.text