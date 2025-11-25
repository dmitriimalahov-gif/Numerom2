# Развертывание и настройка

## Обзор

Руководство по развертыванию NUMEROM в различных средах: от локальной разработки до продакшн сервера.

## Требования к системе

### Минимальные требования
- **CPU:** 2 ядра, 2.0 GHz
- **RAM:** 4 GB
- **Диск:** 50 GB свободного места
- **ОС:** Ubuntu 20.04+, CentOS 8+, или аналогичные

### Рекомендуемые требования
- **CPU:** 4 ядра, 2.4 GHz
- **RAM:** 8 GB
- **Диск:** 100 GB SSD
- **Сеть:** 100 Mbps
- **ОС:** Ubuntu 22.04 LTS

### Технологические зависимости

#### Backend
```bash
# Python 3.9+
python3 --version

# MongoDB 5.0+
mongod --version

# Дополнительные системные пакеты
sudo apt update
sudo apt install -y python3-pip python3-venv nodejs npm nginx certbot
```

#### Frontend
```bash
# Node.js 18+
node --version
npm --version

# Yarn (опционально)
npm install -g yarn
```

## Локальная разработка

### 1. Клонирование репозитория
```bash
git clone <repository_url>
cd Numerom2
```

### 2. Настройка Backend

#### Создание виртуального окружения
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

#### Установка зависимостей
```bash
pip install -r requirements.txt
```

#### Создание файла .env
```bash
# backend/.env
MONGO_URL=mongodb://localhost:27017
DB_NAME=numerom_dev
SECRET_KEY=your-super-secret-key-for-development
STRIPE_API_KEY=sk_test_your_stripe_test_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
ALLOWED_ORIGINS=["http://localhost:3000"]
DEBUG=true
```

#### Запуск MongoDB
```bash
# Ubuntu/Debian
sudo systemctl start mongod
sudo systemctl enable mongod

# Docker (альтернатива)
docker run -d -p 27017:27017 --name mongodb mongo:5.0
```

#### Запуск Backend сервера
```bash
python server.py
```

Сервер будет доступен на `http://localhost:8000`

### 3. Настройка Frontend

#### Установка зависимостей
```bash
cd frontend
npm install
# или
yarn install
```

#### Создание файла .env
```bash
# frontend/.env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
```

#### Запуск Frontend сервера
```bash
npm start
# или
yarn start
```

Приложение будет доступно на `http://localhost:3000`

## Docker развертывание

### 1. Docker Compose

#### Создание docker-compose.yml
```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:5.0
    container_name: numerom_mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_DATABASE: numerom
    networks:
      - numerom_network

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: numerom_backend
    ports:
      - "8000:8000"
    environment:
      MONGO_URL: mongodb://mongodb:27017
      DB_NAME: numerom
      SECRET_KEY: ${SECRET_KEY}
      STRIPE_API_KEY: ${STRIPE_API_KEY}
      STRIPE_WEBHOOK_SECRET: ${STRIPE_WEBHOOK_SECRET}
    depends_on:
      - mongodb
    volumes:
      - ./uploads:/app/uploads
    networks:
      - numerom_network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: numerom_frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000
      REACT_APP_STRIPE_PUBLISHABLE_KEY: ${STRIPE_PUBLISHABLE_KEY}
    depends_on:
      - backend
    networks:
      - numerom_network

  nginx:
    image: nginx:alpine
    container_name: numerom_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    networks:
      - numerom_network

volumes:
  mongodb_data:

networks:
  numerom_network:
    driver: bridge
```

#### Создание Dockerfile для Backend
```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание директории для загрузок
RUN mkdir -p /app/uploads

# Экспорт порта
EXPOSE 8000

# Команда запуска
CMD ["python", "server.py"]
```

#### Создание Dockerfile для Frontend
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Копирование package.json и package-lock.json
COPY package*.json ./

# Установка зависимостей
RUN npm ci --only=production

# Копирование кода и сборка
COPY . .
RUN npm run build

# Production стадия
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=build /app/build /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 2. Запуск Docker Compose
```bash
# Создание .env файла с переменными окружения
echo "SECRET_KEY=your-production-secret-key" > .env
echo "STRIPE_API_KEY=sk_live_your_live_key" >> .env
echo "STRIPE_PUBLISHABLE_KEY=pk_live_your_live_key" >> .env

# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка сервисов
docker-compose down
```

## Продакшн развертывание

### 1. Подготовка сервера

#### Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git nginx certbot python3-certbot-nginx
```

#### Установка Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### Установка Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Конфигурация Nginx

#### Создание конфигурации
```nginx
# /etc/nginx/sites-available/numerom
server {
    listen 80;
    server_name numerom.com www.numerom.com;

    # Редирект на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name numerom.com www.numerom.com;

    # SSL сертификаты
    ssl_certificate /etc/letsencrypt/live/numerom.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/numerom.com/privkey.pem;

    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Размер загружаемых файлов
    client_max_body_size 100M;

    # Frontend (статические файлы)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Статические файлы (загрузки)
    location /uploads {
        alias /var/www/numerom/uploads;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### Активация конфигурации
```bash
sudo ln -s /etc/nginx/sites-available/numerom /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. SSL сертификаты

#### Получение Let's Encrypt сертификата
```bash
sudo certbot --nginx -d numerom.com -d www.numerom.com
```

#### Автоматическое обновление
```bash
sudo crontab -e
# Добавить строку:
0 12 * * * /usr/bin/certbot renew --quiet
```

### 4. Настройка переменных окружения

#### Создание продакшн .env
```bash
# /var/www/numerom/.env
MONGO_URL=mongodb://localhost:27017
DB_NAME=numerom_production
SECRET_KEY=super-secure-production-key-change-this
STRIPE_API_KEY=sk_live_your_live_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_production_webhook_secret
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key
ALLOWED_ORIGINS=["https://numerom.com", "https://www.numerom.com"]
DEBUG=false
```

### 5. Systemd сервисы

#### Backend сервис
```ini
# /etc/systemd/system/numerom-backend.service
[Unit]
Description=NUMEROM Backend API
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/numerom/backend
Environment=PATH=/var/www/numerom/backend/venv/bin
EnvironmentFile=/var/www/numerom/.env
ExecStart=/var/www/numerom/backend/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Frontend сервис (если не используется Docker)
```ini
# /etc/systemd/system/numerom-frontend.service
[Unit]
Description=NUMEROM Frontend
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/numerom/frontend
Environment=NODE_ENV=production
EnvironmentFile=/var/www/numerom/.env
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Запуск сервисов
```bash
sudo systemctl daemon-reload
sudo systemctl enable numerom-backend
sudo systemctl enable numerom-frontend
sudo systemctl start numerom-backend
sudo systemctl start numerom-frontend

# Проверка статуса
sudo systemctl status numerom-backend
sudo systemctl status numerom-frontend
```

## Мониторинг и логирование

### 1. Настройка логов

#### Конфигурация Python логирования
```python
# backend/logging_config.py
import logging
import sys
from pathlib import Path

# Создание директории для логов
log_dir = Path("/var/log/numerom")
log_dir.mkdir(exist_ok=True, parents=True)

# Настройка форматирования
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Обработчики логов
file_handler = logging.FileHandler(log_dir / "backend.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

error_handler = logging.FileHandler(log_dir / "errors.log")
error_handler.setFormatter(formatter)
error_handler.setLevel(logging.ERROR)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Главный логгер
logger = logging.getLogger("numerom")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(error_handler)
logger.addHandler(console_handler)
```

### 2. Мониторинг системы

#### Установка мониторинга
```bash
# Установка htop для мониторинга ресурсов
sudo apt install htop

# Установка logrotate для ротации логов
sudo apt install logrotate
```

#### Конфигурация logrotate
```bash
# /etc/logrotate.d/numerom
/var/log/numerom/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload numerom-backend
    endscript
}
```

### 3. Мониторинг доступности

#### Простой скрипт проверки
```bash
#!/bin/bash
# /usr/local/bin/check_numerom.sh

API_URL="https://numerom.com/api/health"
FRONTEND_URL="https://numerom.com"

# Проверка API
if curl -f -s $API_URL > /dev/null; then
    echo "$(date): API доступен" >> /var/log/numerom/health.log
else
    echo "$(date): API недоступен!" >> /var/log/numerom/health.log
    # Отправка уведомления (email, Slack, Telegram)
fi

# Проверка Frontend
if curl -f -s $FRONTEND_URL > /dev/null; then
    echo "$(date): Frontend доступен" >> /var/log/numerom/health.log
else
    echo "$(date): Frontend недоступен!" >> /var/log/numerom/health.log
fi
```

#### Добавление в cron
```bash
sudo crontab -e
# Добавить:
*/5 * * * * /usr/local/bin/check_numerom.sh
```

## Резервное копирование

### 1. MongoDB резервные копии

#### Скрипт ежедневного бэкапа
```bash
#!/bin/bash
# /usr/local/bin/backup_mongodb.sh

BACKUP_DIR="/var/backups/numerom"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="numerom_production"

# Создание директории
mkdir -p $BACKUP_DIR

# Создание бэкапа
mongodump --db $DB_NAME --out $BACKUP_DIR/mongodb_$DATE

# Сжатие
tar -czf $BACKUP_DIR/mongodb_$DATE.tar.gz -C $BACKUP_DIR mongodb_$DATE
rm -rf $BACKUP_DIR/mongodb_$DATE

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "mongodb_*.tar.gz" -mtime +30 -delete

echo "$(date): Backup completed: mongodb_$DATE.tar.gz"
```

### 2. Резервное копирование файлов

#### Скрипт для файлов загрузок
```bash
#!/bin/bash
# /usr/local/bin/backup_uploads.sh

SOURCE_DIR="/var/www/numerom/uploads"
BACKUP_DIR="/var/backups/numerom"
DATE=$(date +%Y%m%d_%H%M%S)

# Синхронизация с rsync
rsync -av --delete $SOURCE_DIR/ $BACKUP_DIR/uploads_$DATE/

# Сжатие
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz -C $BACKUP_DIR uploads_$DATE
rm -rf $BACKUP_DIR/uploads_$DATE

echo "$(date): Files backup completed: uploads_$DATE.tar.gz"
```

### 3. Автоматизация бэкапов

#### Добавление в cron
```bash
sudo crontab -e
# Добавить:
0 2 * * * /usr/local/bin/backup_mongodb.sh >> /var/log/numerom/backup.log 2>&1
0 3 * * * /usr/local/bin/backup_uploads.sh >> /var/log/numerom/backup.log 2>&1
```

## Обновления и деплой

### 1. Автоматизированный деплой

#### Git hooks для автодеплоя
```bash
#!/bin/bash
# /var/www/numerom/.git/hooks/post-receive

cd /var/www/numerom

# Обновление backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Обновление frontend
cd ../frontend
npm ci --production
npm run build

# Перезапуск сервисов
sudo systemctl restart numerom-backend
sudo systemctl restart numerom-frontend

echo "$(date): Deployment completed" >> /var/log/numerom/deploy.log
```

### 2. Blue-Green деплой

#### Скрипт смены версий
```bash
#!/bin/bash
# /usr/local/bin/blue_green_deploy.sh

CURRENT_COLOR=$(readlink /var/www/numerom/current)
NEW_COLOR="blue"

if [[ $CURRENT_COLOR == *"blue"* ]]; then
    NEW_COLOR="green"
fi

echo "Deploying to $NEW_COLOR environment"

# Подготовка новой версии
rsync -av /var/www/numerom/staging/ /var/www/numerom/$NEW_COLOR/

# Тестирование новой версии
cd /var/www/numerom/$NEW_COLOR
# Запуск тестов

# Переключение трафика
ln -sfn /var/www/numerom/$NEW_COLOR /var/www/numerom/current
sudo systemctl reload nginx

echo "Deployment to $NEW_COLOR completed"
```

## Безопасность

### 1. Файрвол
```bash
# Настройка UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. Защита MongoDB
```bash
# Создание административного пользователя
mongo
use admin
db.createUser({
  user: "admin",
  pwd: "secure_password",
  roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"]
})

# Создание пользователя для приложения
use numerom_production
db.createUser({
  user: "numerom_app",
  pwd: "app_password",
  roles: ["readWrite"]
})
```

#### Включение аутентификации
```bash
# /etc/mongod.conf
security:
  authorization: enabled
```

### 3. Обновления безопасности
```bash
# Автоматические обновления безопасности
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Масштабирование

### 1. Горизонтальное масштабирование

#### Load Balancer с Nginx
```nginx
upstream backend {
    server 192.168.1.10:8000;
    server 192.168.1.11:8000;
    server 192.168.1.12:8000;
}

upstream frontend {
    server 192.168.1.10:3000;
    server 192.168.1.11:3000;
}

server {
    listen 80;
    
    location /api {
        proxy_pass http://backend;
    }
    
    location / {
        proxy_pass http://frontend;
    }
}
```

### 2. Кластер MongoDB
```yaml
# docker-compose.yml для MongoDB кластера
version: '3.8'

services:
  mongo1:
    image: mongo:5.0
    command: mongod --replSet rs0 --port 27017
    ports:
      - "27017:27017"
    
  mongo2:
    image: mongo:5.0
    command: mongod --replSet rs0 --port 27018
    ports:
      - "27018:27018"
    
  mongo3:
    image: mongo:5.0
    command: mongod --replSet rs0 --port 27019
    ports:
      - "27019:27019"
```

## Troubleshooting

### Частые проблемы

#### 1. MongoDB подключение
```bash
# Проверка статуса
sudo systemctl status mongod

# Проверка логов
sudo journalctl -u mongod

# Тест подключения
mongo --eval "db.stats()"
```

#### 2. Python зависимости
```bash
# Переустановка зависимостей
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Nginx ошибки
```bash
# Проверка конфигурации
sudo nginx -t

# Проверка логов
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

#### 4. SSL сертификаты
```bash
# Проверка сертификата
sudo certbot certificates

# Принудительное обновление
sudo certbot renew --force-renewal
```

### Команды диагностики
```bash
# Проверка портов
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :3000

# Проверка дискового пространства
df -h

# Проверка памяти
free -h

# Проверка процессов
ps aux | grep python
ps aux | grep node

# Проверка логов приложения
tail -f /var/log/numerom/backend.log
tail -f /var/log/numerom/errors.log
```

## Производительность

### 1. Оптимизация MongoDB
```javascript
// Создание индексов
db.users.createIndex({ "email": 1 }, { unique: true })
db.numerology_calculations.createIndex({ "user_id": 1, "created_at": -1 })
db.credit_transactions.createIndex({ "user_id": 1, "created_at": -1 })
```

### 2. Кеширование
```nginx
# Nginx кеширование статики
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. Мониторинг производительности
```bash
# Установка и настройка htop
sudo apt install htop iotop

# Мониторинг MongoDB
mongostat
mongotop
```


