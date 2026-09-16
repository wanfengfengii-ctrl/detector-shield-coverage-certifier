# syntax=docker/dockerfile:1
# 验证服务：在同一容器内运行 pytest、Vitest、Playwright。
# 官方 Playwright 镜像已预装 Node、Chromium 及全部系统库。
FROM mcr.microsoft.com/playwright:v1.63.0-noble

USER root

ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace

# Python 3.12（noble 自带）+ pip 与 curl（等待服务就绪），用于 pytest
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip curl \
    && rm -rf /var/lib/apt/lists/*

# 后端依赖（含 pytest、httpx）；requirements-dev 通过 -r 引用 requirements
COPY backend/requirements.txt backend/requirements-dev.txt /workspace/backend/
RUN python3 -m pip install --no-cache-dir --break-system-packages \
    -r /workspace/backend/requirements-dev.txt

# 前端依赖（含 vitest、@playwright/test）
COPY frontend/package.json frontend/package-lock.json /workspace/frontend/
RUN cd /workspace/frontend && npm ci

# 源码与测试
COPY backend /workspace/backend
COPY frontend /workspace/frontend
COPY verify /workspace/verify

RUN chmod +x /workspace/verify/run-tests.sh

CMD ["bash", "/workspace/verify/run-tests.sh"]
