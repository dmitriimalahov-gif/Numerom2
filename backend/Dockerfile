FROM python:3.12-slim

WORKDIR /app

# Установить системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установить зависимости
COPY requirements.txt .
# Компилятор нужен для сборки timezonefinder
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

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
