"""CodeMaker Coach API — FastAPI 진입점.

라우터(problems, submissions, hints, community, auth)는 이후 브랜치에서 추가된다.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.gateway import StubAgentGateway, get_agent_gateway
from app.routers import problems_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="CodeMaker Coach API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://100.65.149.96:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problems_router)


@app.get("/health")
def health() -> dict:
    """헬스체크 + 현재 AI 게이트웨이 모드 표시."""
    gateway = get_agent_gateway()
    mode = "stub" if isinstance(gateway, StubAgentGateway) else "live"
    return {"status": "ok", "agent_mode": mode}
