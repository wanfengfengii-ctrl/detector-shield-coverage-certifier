"""FastAPI 入口：接收原始 JSON，聚合校验错误，返回覆盖分析结果。"""

from __future__ import annotations

import json
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .geometry import analyze
from .validation import sort_issues, validate_document

app = FastAPI(title="屏蔽基板拼片质控 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvidenceRect(BaseModel):
    category: Literal["gap", "overlap"]
    left: int
    bottom: int
    right: int
    top: int


class AnalyzeResponse(BaseModel):
    status: Literal["exact", "gap", "overlap", "mixed"]
    gapArea: int = Field(ge=0)
    overlapArea: int = Field(ge=0)
    evidence: list[EvidenceRect]


class ErrorItem(BaseModel):
    pointer: str
    message: str


class ErrorResponse(BaseModel):
    errors: list[ErrorItem]


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/analyze",
    response_model=AnalyzeResponse,
    responses={422: {"model": ErrorResponse}},
)
async def analyze_board(request: Request) -> JSONResponse | AnalyzeResponse:
    raw = await request.body()
    if not raw.strip():
        return JSONResponse(
            status_code=422,
            content={"errors": [{"pointer": "", "message": "请求体为空"}]},
        )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return JSONResponse(
            status_code=422,
            content={
                "errors": [
                    {
                        "pointer": "",
                        "message": f"JSON 解析失败（第 {exc.lineno} 行第 "
                        f"{exc.colno} 列）：{exc.msg}",
                    }
                ]
            },
        )

    issues = sort_issues(validate_document(data))
    if issues:
        return JSONResponse(
            status_code=422,
            content={
                "errors": [
                    {"pointer": i.pointer, "message": i.message} for i in issues
                ]
            },
        )

    polygons = [
        [(int(p[0]), int(p[1])) for p in poly] for poly in data["polygons"]
    ]
    result = analyze(polygons, int(data["width"]), int(data["height"]))
    return AnalyzeResponse(**result)  # type: ignore[arg-type]
