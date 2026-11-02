"""Pre-answering: the most asked questions are answered before anyone asks again.

Every docs refresh period, for each version in ASSISTANT_PREWARM_VERSIONS, the
most frequent questions of the last 30 days (from the question log) plus a few
seed questions are checked against the cache. Each one without a valid cached
answer (new, or one of its pages changed with the last docs publish) is
answered now, one after another, within ASSISTANT_PREWARM_DAILY_USD.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections import Counter
from pathlib import Path

from . import agent
from .cache import cache, key
from .config import settings
from .docs import library
from .guard import budget

SEEDS = (
    "install on openshift 3 node cluster",
    "install simplyblock on EKS",
    "install simplyblock on GKE",
    "install simplyblock on Talos",
    "add a storage node to a running cluster",
    "set up disaster recovery between two sites",
    "create a volume with a snapshot schedule",
    "upgrade from R25 to R26",
    "air-gapped installation",
    "remove a previous installation",
)


def top_questions(version: str, n: int) -> list[str]:
    """Most asked questions for a version, one phrasing per key, then the seeds."""
    counts: Counter = Counter()
    phrasing: dict[str, str] = {}
    since = time.time() - 30 * 86400
    path = Path(settings.log_file) if settings.log_file else None
    if path and path.exists():
        with path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if ev.get("event") != "ask" or ev.get("version") != version:
                    continue
                if not (ev.get("cached") or ev.get("outcome") == "answer"):
                    continue
                try:
                    ts = time.mktime(time.strptime(ev["ts"], "%Y-%m-%dT%H:%M:%SZ"))
                except (KeyError, ValueError):
                    continue
                if ts < since:
                    continue
                k = key(ev.get("question", ""))
                if k:
                    counts[k] += 1
                    phrasing[k] = ev["question"]
    out = [phrasing[k] for k, _ in counts.most_common(n)]
    for q in SEEDS:
        if len(out) >= n:
            break
        if key(q) not in counts:
            out.append(q)
    return out[:n]


async def warm_version(name: str, log) -> int:
    version = await library.resolve(name)
    corpus = await library.corpus(version)
    fp = agent.fingerprint()
    answered = 0
    for question in top_questions(version, settings.prewarm_count):
        if cache.get(corpus, question, fp):
            continue
        if not budget.prewarm_available():
            log("prewarm_budget_exhausted", version=version, spent=round(budget.prewarm_spent, 2))
            break
        final: dict = {}
        try:
            async for ev in agent.run(corpus, question):
                if ev["type"] in ("answer", "error"):
                    final = ev
        except Exception as exc:
            log("prewarm_error", version=version, question=question, error=f"{type(exc).__name__}: {exc}")
            continue
        budget.add(float(final.get("cost", 0.0)), prewarm=True)
        if final.get("type") == "answer" and final.get("pages"):
            cache.put(corpus, question, fp, public(final), final["pages"])
            answered += 1
        log("prewarm", version=version, question=question, outcome=final.get("type"),
            cost=round(float(final.get("cost", 0.0)), 4), seconds=final.get("seconds"))
    return answered


def public(event: dict) -> dict:
    return {k: v for k, v in event.items() if k not in ("cost", "pages")}


async def loop(log) -> None:
    if not settings.prewarm_versions or settings.mock:
        return
    await asyncio.sleep(30)
    while True:
        for name in settings.prewarm_versions:
            try:
                await warm_version(name, log)
            except Exception as exc:
                log("prewarm_error", version=name, error=f"{type(exc).__name__}: {exc}")
        await asyncio.sleep(settings.refresh_seconds)
