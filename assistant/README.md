# Command Assistant API

Backend of the [Command Assistant](../docs/assistant/index.md) page. A reader describes a task ("install on
openshift 3 node cluster"); Claude searches and reads the documentation of the reader's version and returns the
commands to run, in order, each step linked to the page it comes from.

```
browser (docs page)  --POST /api/assistant/ask-->  this service  --Messages API-->  Claude
                     <--Server-Sent Events-------  tools: search_docs, read_page, list_pages
                                                   corpus: <DOCS_BASE>/<version>/llms-full.txt
```

| File                 | Role                                                                    |
|----------------------|-------------------------------------------------------------------------|
| `app/main.py`        | HTTP API: `/ask` (SSE), `/feedback`, `/health`                          |
| `app/agent.py`       | System prompt, tools, answer schema, agent loop, command verification   |
| `app/docs.py`        | Loads `llms-full.txt` per docs version, BM25 search, page reader        |
| `app/guard.py`       | Per-IP rate limit, answer cache, daily budget, Cloudflare Turnstile     |
| `app/config.py`      | Settings from environment variables                                     |
| `eval/run_eval.py`   | Sample questions → review report                                        |

## How answers stay grounded

* The only source is the published documentation of the reader's version (`llms-full.txt`, written by
  `scripts/hooks/md_mirror.py`). Claude has no web access and no other tools.
* The prompt requires commands to be copied verbatim, with placeholders, and every step to cite a page.
* After the answer, every command is checked: when each of its lines appears as a whole line in the docs, it is
  shown as **from the docs**; otherwise as **adapted**, so the reader knows to check it.
* Unclear requests get one clarifying question; requests the docs do not cover get `not_covered` and the closest pages.

## Configuration

| Variable                        | Default                        | Meaning                                              |
|---------------------------------|--------------------------------|------------------------------------------------------|
| `ANTHROPIC_API_KEY`             | (required)                     | Key of the simplyblock service account               |
| `ASSISTANT_MODEL`               | `claude-opus-5-5`              | Model; `claude-sonnet-5-5` is about half the price   |
| `ASSISTANT_EFFORT`              | `medium`                       | `low` … `max`                                        |
| `ASSISTANT_PRICE_*`             | Opus 5.5 prices                | USD per million tokens, for the budget; set with the model |
| `ASSISTANT_DAILY_BUDGET_USD`    | `25`                           | Stops answering (503) for the rest of the UTC day    |
| `ASSISTANT_RATE_LIMIT` / `_WINDOW` | `8` / `600`                 | Questions per IP per window (seconds)                |
| `ASSISTANT_CACHE_TTL`           | `86400`                        | Same question + version is answered from cache       |
| `ASSISTANT_TRUST_FORWARDED_FOR` | `1`                            | Take the client IP from `X-Forwarded-For` (behind a proxy) |
| `TURNSTILE_SECRET`              | empty (off)                    | Cloudflare Turnstile secret; set `extra.assistant.turnstile_sitekey` in `mkdocs.yml` to match |
| `ASSISTANT_CORS_ORIGINS`        | empty                          | Only needed when the API is on another origin        |
| `DOCS_BASE`                     | `https://docs.simplyblock.io`  | Where `versions.json` and `<version>/llms-full.txt` are read |
| `ASSISTANT_LOG_FILE`            | stdout                         | JSON lines: questions, outcome, cost, feedback       |
| `ASSISTANT_MOCK`                | `0`                            | `1`: canned answers, no Claude call                  |
| `ASSISTANT_STATIC_SITE`         | empty                          | Serve a built site next to the API (local testing)   |

The page calls `extra.assistant.api` from `mkdocs.yml` (default `/api/assistant`, same origin as the docs).

## Running locally

```bash
cd assistant
python -m venv .venv && .venv/bin/pip install -r requirements.txt
mkdocs build -d /tmp/site          # from the repository root
ASSISTANT_STATIC_SITE=/tmp/site ANTHROPIC_API_KEY=... .venv/bin/uvicorn app.main:app --port 8765
# open http://localhost:8765/assistant/   (ASSISTANT_MOCK=1 works without a key)
```

Review answer quality before changing the prompt or the model (every run costs money):

```bash
ANTHROPIC_API_KEY=... python -m eval.run_eval --version dev
```

## Deployment

The docs web server only serves static files, so the API runs on its own host,
`docs-assistant.simplyblock.io`: an EC2 instance (`t4g.small`, eu-central-1, tag `Name=docs-assistant`) with Docker.
Caddy terminates TLS with a Let's Encrypt certificate and proxies `/api/assistant/*` to the API container. The docs page
calls it cross-origin (`extra.assistant.api` in `mkdocs.yml`, allowed by `ASSISTANT_CORS_ORIGINS`).

| File                     | Role                                                                      |
|--------------------------|---------------------------------------------------------------------------|
| `deploy/user-data.sh`    | First boot: Docker, clone of the repository, settings, first deploy        |
| `deploy/deploy.sh`       | Pull, build, read the key, (re)start the API and Caddy                     |
| `deploy/Caddyfile`       | TLS and routing                                                            |

* The Anthropic key is stored in SSM Parameter Store as the SecureString `/docs-assistant/anthropic-api-key`. The
  instance role `docs-assistant-ec2` may read only that parameter (plus SSM Session Manager access, no SSH).
* Settings are in `/opt/docs-assistant/config.env` on the host; questions and feedback are logged to
  `/var/log/docs-assistant/assistant.jsonl`.
* DNS: `docs-assistant.simplyblock.io` is an A record (DNS only, not proxied) to the instance's Elastic IP.

Redeploy after a change is merged:

```bash
aws ssm send-command --region eu-central-1 --document-name AWS-RunShellScript   --targets Key=tag:Name,Values=docs-assistant   --parameters 'commands=["BRANCH=main bash /opt/docs-assistant/src/assistant/deploy/deploy.sh"]'
```

Rotate the key: put the new value into the SSM parameter, then redeploy.
