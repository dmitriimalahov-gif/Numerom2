FROM node:22-alpine AS builder

WORKDIR /app/frontend

# Копировать package files
COPY frontend/package*.json ./

# Установить зависимости
RUN npm install --legacy-peer-deps

# Копировать остальные файлы
COPY frontend/ .
COPY packages/api-client/ /app/packages/api-client/

# Собрать приложение
RUN npm run build

# Production stage
FROM nginx:alpine

# Копировать собранные файлы
COPY --from=builder /app/frontend/build /usr/share/nginx/html

# Копировать nginx конфиг
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
