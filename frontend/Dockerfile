# ---- 构建阶段 ----
FROM node:22-bookworm-slim AS build
WORKDIR /app

# Web 构建不需要 Playwright 浏览器二进制
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html vite.config.ts tsconfig.json ./
COPY src ./src
RUN npm run build

# ---- 运行阶段 ----
FROM nginx:1.27-bookworm

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
