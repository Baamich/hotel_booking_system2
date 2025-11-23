FROM python:3.11-slim

WORKDIR /app

# Копируем .env и requirements из корня проекта
COPY ../../requirements.txt .
COPY ../../.env* ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5002

CMD ["python", "app.py"]