"""Hex AI service (FastAPI). Currently backed by a mock bot.

Run locally (from the ai/ directory):
    uvicorn app.main:app --reload --port 5000

Environment variables:
    BOT_STRATEGY   random | local            (default: local)
    BOT_SEED       integer, for repeatable moves (default: none)
    MOCK_DELAY_MS  e.g. "300-900" or "0"     (fake "thinking" time, default: 300-900)
"""

from __future__ import annotations

import asyncio
import os
import random
import time
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from .bots import MAX_SIZE, MIN_SIZE, Bot, InvalidPosition, MockBot


def _parse_delay(raw: str) -> tuple[int, int]:
    lo, _, hi = raw.partition("-")
    lo_ms = int(lo)
    hi_ms = int(hi) if hi else lo_ms
    return min(lo_ms, hi_ms), max(lo_ms, hi_ms)


_seed = os.getenv("BOT_SEED")
bot: Bot = MockBot(
    strategy=os.getenv("BOT_STRATEGY", "local"),
    seed=int(_seed) if _seed else None,
)
DELAY_MS = _parse_delay(os.getenv("MOCK_DELAY_MS", "300-900"))


class CamelModel(BaseModel):
    # camelCase in JSON (for TypeScript), snake_case in Python
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class MoveRequest(CamelModel):
    board: list[list[int]] = Field(
        description="n x n board: 0 empty, 1 red (top-bottom), 2 blue (left-right).",
        examples=[[[0, 0, 0], [0, 1, 0], [0, 0, 0]]],
    )
    to_move: Literal[1, 2] = Field(description="Player to move.", examples=[2])


class Move(CamelModel):
    row: int
    col: int


class MoveResponse(CamelModel):
    move: Move
    policy: list[list[float]] | None = Field(
        description="Move probability for every cell (heatmap)."
    )
    evaluation: float | None = Field(
        description="Position evaluation in [-1, 1] for the player to move."
    )
    bot: str
    thinking_ms: int


class HealthResponse(CamelModel):
    status: Literal["ok"]
    bot: str
    min_size: int
    max_size: int


app = FastAPI(title="Hex AI", version="0.1.0-mock")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok", bot=bot.name, min_size=MIN_SIZE, max_size=MAX_SIZE
    )


@app.post(
    "/move",
    response_model=MoveResponse,
    responses={422: {"description": "Invalid position"}},
)
async def move(req: MoveRequest) -> MoveResponse:
    started = time.perf_counter()
    try:
        result = bot.choose_move(req.board, req.to_move)
    except InvalidPosition as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Fake thinking time, so the frontend handles the "bot is thinking..." state from day one
    await asyncio.sleep(random.randint(*DELAY_MS) / 1000)

    return MoveResponse(
        move=Move(row=result.row, col=result.col),
        policy=result.policy,
        evaluation=result.evaluation,
        bot=result.bot,
        thinking_ms=round((time.perf_counter() - started) * 1000),
    )
