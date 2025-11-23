from pydantic import BaseModel
from datetime import date
from typing import Optional

class CreatePaymentRequest(BaseModel):
    hotel_id: str
    hotel_name: str
    date_from: date
    date_to: date
    total_amount_usd: float       # сумма в USD (мы будем принимать в USD, потом можно конвертировать)
    currency: str = "usd"         # usd, eur, ron, rub и т.д.
    user_id: str
    user_email: str
    user_name: Optional[str] = None
    success_url: str              # куда редиректить после успешной оплаты
    cancel_url: str               # куда при отмене