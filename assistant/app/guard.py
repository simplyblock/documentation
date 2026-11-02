"""Abuse and cost protection: per-IP rate limit, daily budget, Turnstile."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import re
import time
import urllib.parse
import urllib.request
from collections import deque

from .config import settings


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque] = {}

    def allow(self, key: str) -> bool:
        now = time.time()
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] > settings.rate_window:
            hits.popleft()
        if len(hits) >= settings.rate_limit:
            return False
        hits.append(now)
        if len(self._hits) > 50_000:  # drop idle entries
            for k in [k for k, v in self._hits.items() if not v][:10_000]:
                del self._hits[k]
        return True


class Budget:
    """Daily spend. Pre-answering has its own, smaller cap inside the total."""

    def __init__(self) -> None:
        self.day = dt.date.today()
        self.spent = 0.0
        self.prewarm_spent = 0.0

    def _roll(self) -> None:
        today = dt.date.today()
        if today != self.day:
            self.day, self.spent, self.prewarm_spent = today, 0.0, 0.0

    def available(self) -> bool:
        self._roll()
        return self.spent < settings.daily_budget_usd

    def prewarm_available(self) -> bool:
        return self.available() and self.prewarm_spent < settings.prewarm_daily_usd

    def add(self, usd: float, prewarm: bool = False) -> None:
        self._roll()
        self.spent += usd
        if prewarm:
            self.prewarm_spent += usd


def _verify_turnstile(token: str, ip: str) -> bool:
    data = urllib.parse.urlencode({"secret": settings.turnstile_secret, "response": token, "remoteip": ip}).encode()
    req = urllib.request.Request("https://challenges.cloudflare.com/turnstile/v0/siteverify", data=data)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return bool(json.loads(resp.read()).get("success"))


async def human(token: str, ip: str) -> bool:
    if not settings.turnstile_secret:
        return True
    if not token:
        return False
    try:
        return await asyncio.to_thread(_verify_turnstile, token, ip)
    except Exception:
        return False


limiter = RateLimiter()
budget = Budget()
