FROM python:3.11-slim

WORKDIR /app

# Копируем только содержимое текущей папки ai_assistant (app.py и т.д.)
COPY . .

# Копируем нужные файлы/папки из корня проекта
COPY ../translations.py .
COPY ../currencies.py .
COPY ../chat_service.py .
COPY ../config.py .
COPY ../models ./models

# Если есть папка utils — копируем, если нет — просто игнорируем ошибку
RUN mkdir -p utils && cp -r ../utils/* utils/ 2>/dev/null || echo "utils folder not found - skipping"

# requirements.txt (у тебя уже есть в папке ai_assistant)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5001

CMD ["python", "app.py"]