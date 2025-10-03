FROM node:22-alpine AS builder

WORKDIR /app

# Копировать package files
COPY package*.json ./

# Установить зависимости
RUN npm install --legacy-peer-deps

# Копировать остальные файлы
COPY . .

# Собрать приложение
RUN npm run build

# Production stage
FROM nginx:alpine

# Копировать собранные файлы
COPY --from=builder /app/build /usr/share/nginx/html

# Копировать nginx конфиг
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
