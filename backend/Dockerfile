FROM python:3.12-slim

WORKDIR /app

# Установить зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Скопировать код
COPY . .

# Создать директорию для загрузок
RUN mkdir -p uploads

# Открыть порт
EXPOSE 8000

# Запустить приложение
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
