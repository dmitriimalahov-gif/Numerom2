FROM node:22.22.2-bookworm-slim

# Installation is the only phase with network access. Runtime uses --network none.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libnss3 libdbus-1-3 libatk1.0-0 libgbm1 libasound2 \
    libxrandr2 libxkbcommon0 libxfixes3 libxcomposite1 libxdamage1 \
    libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app/video
COPY video/package.json video/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY video/prepare-browser.mjs ./
RUN node prepare-browser.mjs
COPY packages /app/packages
COPY video ./
RUN node --input-type=module -e "import {compiledBundle} from './render.mjs'; await compiledBundle();" \
    && chown -R node:node /app/video/.cache
USER node
ENTRYPOINT ["node", "/app/video/render.mjs"]
