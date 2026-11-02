"""Settings, all from environment variables (see assistant/README.md)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip()


@dataclass(frozen=True)
class Settings:
    # Where the published docs live; llms-full.txt and versions.json are read from here.
    docs_base: str = field(default_factory=lambda: _env("DOCS_BASE", "https://docs.simplyblock.io").rstrip("/"))
    refresh_seconds: int = field(default_factory=lambda: int(_env("DOCS_REFRESH_SECONDS", "1800")))

    # Claude. The API key comes from ANTHROPIC_API_KEY (read by the SDK).
    model: str = field(default_factory=lambda: _env("ASSISTANT_MODEL", "claude-opus-5-5"))
    effort: str = field(default_factory=lambda: _env("ASSISTANT_EFFORT", "medium"))
    max_turns: int = field(default_factory=lambda: int(_env("ASSISTANT_MAX_TURNS", "12")))
    # USD per million tokens, for the daily budget. Defaults: Claude Opus 5.5.
    price_in: float = field(default_factory=lambda: float(_env("ASSISTANT_PRICE_INPUT", "4.0")))
    price_out: float = field(default_factory=lambda: float(_env("ASSISTANT_PRICE_OUTPUT", "20.0")))
    price_cache_read: float = field(default_factory=lambda: float(_env("ASSISTANT_PRICE_CACHE_READ", "0.2")))
    price_cache_write: float = field(default_factory=lambda: float(_env("ASSISTANT_PRICE_CACHE_WRITE", "5.0")))

    # Abuse and cost protection.
    daily_budget_usd: float = field(default_factory=lambda: float(_env("ASSISTANT_DAILY_BUDGET_USD", "25")))
    rate_limit: int = field(default_factory=lambda: int(_env("ASSISTANT_RATE_LIMIT", "8")))  # questions ...
    rate_window: int = field(default_factory=lambda: int(_env("ASSISTANT_RATE_WINDOW", "600")))  # ... per seconds, per IP
    max_question_chars: int = field(default_factory=lambda: int(_env("ASSISTANT_MAX_QUESTION_CHARS", "400")))
    cache_ttl: int = field(default_factory=lambda: int(_env("ASSISTANT_CACHE_TTL", "86400")))
    trust_forwarded_for: bool = field(default_factory=lambda: _env("ASSISTANT_TRUST_FORWARDED_FOR", "1") == "1")
    turnstile_secret: str = field(default_factory=lambda: _env("TURNSTILE_SECRET", ""))
    # Browser origins allowed to call the API (comma separated). Same-origin needs none.
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(o.strip() for o in _env("ASSISTANT_CORS_ORIGINS", "").split(",") if o.strip())
    )

    # Answer from canned data without calling Claude (UI and API development).
    mock: bool = field(default_factory=lambda: _env("ASSISTANT_MOCK", "0") == "1")
    # Local development: serve a built site (mkdocs build output) next to the API.
    static_site: str = field(default_factory=lambda: _env("ASSISTANT_STATIC_SITE", ""))
    # Questions, feedback, and usage are logged as JSON lines here (stdout when empty).
    log_file: str = field(default_factory=lambda: _env("ASSISTANT_LOG_FILE", ""))


settings = Settings()
