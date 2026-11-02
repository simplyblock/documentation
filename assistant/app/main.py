"""HTTP API of the docs command assistant.

POST /api/assistant/ask       {"question", "version", "turnstile"} -> Server-Sent Events
POST /api/assistant/feedback  {"question", "version", "helpful", "comment"}
GET  /api/assistant/health

Run: uvicorn app.main:app --host 0.0.0.0 --port 8080   (from assistant/)
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from . import agent, prewarm
from .cache import cache
from .config import settings
from .docs import library
from .guard import budget, human, limiter


@asynccontextmanager
async def lifespan(_app):
    task = asyncio.create_task(prewarm.loop(log))
    yield
    task.cancel()


app = FastAPI(title="simplyblock docs assistant", docs_url=None, redoc_url=None, lifespan=lifespan)
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["POST", "GET"],
        allow_headers=["content-type"],
    )


def log(event: str, **fields) -> None:
    line = json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event, **fields})
    if settings.log_file:
        with open(settings.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    else:
        print(line, file=sys.stdout, flush=True)


def client_ip(request: Request) -> str:
    if settings.trust_forwarded_for:
        fwd = request.headers.get("x-forwarded-for", "")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class Ask(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    version: str = Field(default="latest", max_length=64)
    turnstile: str = Field(default="", max_length=4096)


class Feedback(BaseModel):
    question: str = Field(max_length=2000)
    version: str = Field(default="latest", max_length=64)
    helpful: bool
    comment: str = Field(default="", max_length=2000)


def sse(event: dict) -> str:
    return f"event: {event['type']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"


_public = prewarm.public


@app.get("/api/assistant/health")
async def health() -> dict:
    return {"ok": True, "model": settings.model, "budget_left": budget.available(), "cached_answers": len(cache.items)}


@app.post("/api/assistant/ask")
async def ask(body: Ask, request: Request):
    question = " ".join(body.question.split())
    if len(question) > settings.max_question_chars:
        return JSONResponse({"error": f"Please keep the request under {settings.max_question_chars} characters."}, 400)
    version = await library.resolve(body.version)
    ip = client_ip(request)
    try:
        corpus = await library.corpus(version)
    except LookupError:
        return JSONResponse({"error": f"The assistant does not support documentation version {version}."}, 404)
    fp = agent.fingerprint()

    cached = cache.get(corpus, question, fp)
    if cached:
        log("ask", version=version, question=question, cached=True)

        async def replay():
            yield sse({**cached, "type": "answer", "cached": True})

        return StreamingResponse(replay(), media_type="text/event-stream", headers={"Cache-Control": "no-store"})

    if not limiter.allow(ip):
        return JSONResponse({"error": "Too many requests. Please try again in a few minutes."}, 429)
    if not budget.available():
        log("budget_exhausted", spent=round(budget.spent, 2))
        return JSONResponse({"error": "The assistant is resting for today. Please use the search or try again tomorrow."}, 503)
    if not await human(body.turnstile, ip):
        return JSONResponse({"error": "The browser check failed. Please reload the page and try again."}, 403)

    async def events():
        yield sse({"type": "status", "text": f"Reading the {version} documentation"})
        final: dict = {}
        try:
            async for event in agent.run(corpus, question):
                if event["type"] in ("answer", "error"):
                    final = event
                yield sse(_public(event))
        except Exception as exc:  # API errors, network
            final = {"type": "error", "cost": 0.0}
            log("error", version=version, question=question, error=f"{type(exc).__name__}: {exc}")
            yield sse({"type": "error", "message": "The assistant is not available right now. Please try again later."})
        cost = float(final.get("cost", 0.0))
        budget.add(cost)
        if final.get("type") == "answer" and final.get("pages"):
            cache.put(corpus, question, fp, _public(final), final["pages"])
        log(
            "ask", version=version, question=question, outcome=final.get("type"),
            status=(final.get("answer") or {}).get("status"), cost=round(cost, 4),
            tool_calls=final.get("tool_calls"), seconds=final.get("seconds"),
        )

    return StreamingResponse(
        events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@app.post("/api/assistant/feedback")
async def feedback(body: Feedback) -> dict:
    log("feedback", version=body.version, question=body.question, helpful=body.helpful, comment=body.comment)
    return {"ok": True}


if settings.static_site:
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=settings.static_site, html=True), name="site")
