#!/usr/bin/env bash
# 在 verify 容器内依次运行 pytest、Vitest、Playwright。
# 任一阶段失败则整体失败；全部通过退出码 0。
set -euo pipefail

BACKEND_DIR=/workspace/backend
FRONTEND_DIR=/workspace/frontend
API_URL="${API_URL:-http://api:8000/api/health}"
WEB_URL="${WEB_URL:-http://web/}"

wait_for() {
  local name="$1" url="$2" tries=120
  echo "==> 等待 ${name} (${url}) 就绪…"
  until curl -fsS --max-time 3 "$url" >/dev/null 2>&1; do
    tries=$((tries - 1))
    if [ "$tries" -le 0 ]; then
      echo "!!! ${name} 在限定时间内未就绪" >&2
      exit 1
    fi
    sleep 1
  done
  echo "==> ${name} 已就绪"
}

wait_for "api" "$API_URL"
wait_for "web" "$WEB_URL"

echo "=================== [1/3] pytest ==================="
cd "$BACKEND_DIR"
python3 -m pytest

echo "=================== [2/3] Vitest ==================="
cd "$FRONTEND_DIR"
npx vitest run

echo "================== [3/3] Playwright =================="
BASE_URL="$WEB_URL" npx playwright test

echo "======================================================"
echo "ALL TESTS PASSED ✔"
