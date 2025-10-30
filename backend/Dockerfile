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

# Сделать entrypoint скрипт исполняемым
RUN chmod +x docker-entrypoint.sh

# Открыть порт
EXPOSE 8000

# Использовать entrypoint для инициализации
ENTRYPOINT ["/app/docker-entrypoint.sh"]
