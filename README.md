# 高能射线探测器 · 屏蔽基板拼片质控

从空仓库实现的全栈应用：粘贴/上传描述基板与正交简单多边形拼片的 JSON，
后端以**纯整数条带扫描**找出漏缝（缺口）与叠压，前端以 React + SVG
按基板尺寸作 viewBox、固定翻转纵轴后叠绘拼片与证据。

## 技术栈

- **后端**：Python 3.12 · FastAPI · Pydantic（仅响应模型）· Uvicorn
- **几何**：纯 Python 整数运算，无栅格、无浮点面积、无几何布尔库
- **前端**：TypeScript · React 18 · Vite 6 · 纯 SVG（无 Canvas/栅格）
- **测试**：pytest（后端 38 例）· Vitest（前端 10 例）· Playwright（e2e 6 例）
- **运行**：Docker Compose 三个服务 `api` / `web` / `verify`

## 快速开始

```bash
docker compose up --build web api
# 浏览器打开 http://localhost:8080
```

运行全部自动化校验（pytest + Vitest + Playwright，一次性容器，退出码反映结果）：

```bash
docker compose run --build --rm verify
```

## 请求 / 响应

`POST /api/analyze`

```json
{
  "width": 20,
  "height": 10,
  "polygons": [
    [[0, 0], [12, 0], [12, 10], [0, 10]],
    [[8, 0], [20, 0], [20, 10], [8, 10]]
  ]
}
```

| 字段 | 约束 |
| --- | --- |
| `width` / `height` | 1–10000 的整数 |
| `polygons` | 最多 80 个正交简单多边形 |
| 每个多边形 | 4–120 个整数顶点 `[x, y]`，坐标 ∈ [0, 宽/高] |
| 闭合 | 序列隐式闭合，**不得**重复首点 |

成功（本例两片在 `[8,12]` 叠压且铺满整板）：

```json
{
  "status": "overlap",
  "gapArea": 0,
  "overlapArea": 40,
  "evidence": [
    {"category": "overlap", "left": 8, "bottom": 0, "right": 12, "top": 10}
  ]
}
```

`status ∈ {exact, gap, overlap, mixed}`；面积均为**整数**。

### 422 错误聚合

结构、越界、零长度边、斜边、首点重复、顶点数超限等所有问题一次性返回，
按 **JSON Pointer 码点序**排列，页面保留输入并清除旧结果：

```json
{
  "errors": [
    {"pointer": "/polygons/0/0", "message": "存在斜边，正交多边形的边必须水平或竖直"},
    {"pointer": "/width", "message": "width 必须是 1 至 10000 之间的整数"}
  ]
}
```

## 算法

1. 以 `0`、宽度及所有顶点横坐标切分竖条带；在开条带内部取整数代表点。
2. 正交多边形只有水平边会与竖直线横交，交点 y 即整数；奇偶配对得各拼片
   在该条带内的纵区间（竖直边位于切分线上，不在开区间内）。
3. 区间端点事件求覆盖重数：`0=缺口`、`1=正常`、`≥2=叠压`。
4. 条带内合并**同类且相邻**的纵区间（异类相邻只是零面积接触，忽略）。
5. 仅当**连续条带**的（类别, 纵区间）签名完全相同时横向合并为证据矩形；
   面积 = 整数宽 × 整数高。
6. 证据按 `类别 → 左 → 下 → 右 → 上` 排序。

## SVG 可视化

`<svg viewBox="0 0 宽 高">`，内层 `<g transform="translate(0,H) scale(1,-1)">`
对输入坐标固定翻转纵轴后统一叠绘：拼片为半透明多边形，缺口证据琥珀色、
叠压证据红色描边矩形；组内无文字，避免镜像。

## 目录结构

```
backend/            FastAPI 应用、整数几何引擎、pytest
  app/geometry.py   条带扫描核心
  app/validation.py 聚合校验 + JSON Pointer 排序
  app/main.py       /api/analyze、422 错误响应、Pydantic 模型
frontend/           React + Vite + TS + SVG、Vitest、Playwright
  src/components/BoardSvg.tsx
  e2e/app.spec.ts
verify/             三合一验证容器（Dockerfile + run-tests.sh）
docker-compose.yml  api / web / verify
```

## 本地开发（无需 Docker）

```bash
# 后端
cd backend && python3 -m venv --without-pip .venv && \
  .venv/bin/python get-pip.py && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest

# 前端
cd frontend && npm install
npx vitest run
npm run dev          # /api 代理到 http://localhost:8000

# e2e：先起 api 与 npm run preview，再
BASE_URL=http://localhost:4173 npx playwright test
```
