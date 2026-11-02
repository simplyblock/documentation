"""Abuse and cost protection: per-IP rate limit, answer cache, daily budget, Turnstile."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import re
import time
import urllib.parse
import urllib.request
from collections import OrderedDict, deque

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


class AnswerCache:
    """Identical questions (per docs version) are answered once per TTL."""

    def __init__(self, size: int = 1000) -> None:
        self._items: OrderedDict[tuple[str, str], tuple[float, dict]] = OrderedDict()
        self._size = size

    @staticmethod
    def key(version: str, question: str) -> tuple[str, str]:
        q = re.sub(r"[^\w\s-]", " ", question.lower())
        return version, " ".join(q.split())

    def get(self, version: str, question: str) -> dict | None:
        k = self.key(version, question)
        item = self._items.get(k)
        if not item or time.time() - item[0] > settings.cache_ttl:
            return None
        self._items.move_to_end(k)
        return item[1]

    def put(self, version: str, question: str, answer: dict) -> None:
        k = self.key(version, question)
        self._items[k] = (time.time(), answer)
        self._items.move_to_end(k)
        while len(self._items) > self._size:
            self._items.popitem(last=False)


class Budget:
    def __init__(self) -> None:
        self.day = dt.date.today()
        self.spent = 0.0

    def _roll(self) -> None:
        today = dt.date.today()
        if today != self.day:
            self.day, self.spent = today, 0.0

    def available(self) -> bool:
        self._roll()
        return self.spent < settings.daily_budget_usd

    def add(self, usd: float) -> None:
        self._roll()
        self.spent += usd


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
cache = AnswerCache()
budget = Budget()
