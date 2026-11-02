"""Run sample questions through the assistant and write a review report.

Every run calls Claude (costs money). Usage, from assistant/:

    ANTHROPIC_API_KEY=... python -m eval.run_eval [--version dev] [--only 1,3]

Writes eval-results/<timestamp>.json and .md: per question the answer, how
many commands are verbatim from the docs, tool calls, time, and cost.
Read the Markdown report next to the cited pages before changing the prompt.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

from app import agent
from app.docs import library

QUESTIONS = [
    "install on openshift 3 node cluster",
    "install simplyblock on EKS",
    "add a storage node to a running cluster",
    "set up disaster recovery between two sites",
    "create a volume with a snapshot schedule",
    "upgrade from R25 to R26",
    "air-gapped installation",
    "how do I install it",  # should ask which platform
    "configure a mysql database replica",  # not covered
]


def to_markdown(results: list[dict]) -> str:
    out = ["# Command Assistant evaluation", ""]
    for r in results:
        out.append(f"## {r['question']}")
        out.append("")
        if r.get("error"):
            out += [f"**Error:** {r['error']}", ""]
            continue
        a = r["answer"]
        cmds = [c for s in a["steps"] for c in s["commands"]]
        ok = sum(1 for c in cmds if c["verified"])
        out.append(
            f"status `{a['status']}` · {len(a['steps'])} steps · {ok}/{len(cmds)} commands verbatim · "
            f"{r['tool_calls']} tool calls · {r['seconds']} s · ${r['cost']:.3f}"
        )
        out.append("")
        if a.get("question"):
            out += [f"> {a['question']}", ""]
        for i, s in enumerate(a["steps"], 1):
            src = s["source"]
            out.append(f"{i}. **{s['title']}** ({src.get('url') or src.get('page')})  ")
            out.append(f"   {s['explanation']}")
            for c in s["commands"]:
                mark = "docs" if c["verified"] else "ADAPTED"
                out.append(f"   ```{c['language']}  # {mark}")
                out += ["   " + line for line in c["code"].splitlines()]
                out.append("   ```")
            if s.get("note"):
                out.append(f"   _Note: {s['note']}_")
        out.append("")
    return "\n".join(out)


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="dev")
    ap.add_argument("--only", default="", help="comma-separated 1-based question numbers")
    args = ap.parse_args()
    picks = [int(x) for x in args.only.split(",") if x] or range(1, len(QUESTIONS) + 1)

    version = await library.resolve(args.version)
    corpus = await library.corpus(version)
    results = []
    for n in picks:
        q = QUESTIONS[n - 1]
        print(f"[{n}] {q}", flush=True)
        entry: dict = {"question": q}
        try:
            async for ev in agent.run(corpus, q):
                if ev["type"] == "status":
                    print("    ", ev["text"], flush=True)
                elif ev["type"] == "answer":
                    entry.update(answer=ev["answer"], cost=ev["cost"], tool_calls=ev["tool_calls"],
                                 seconds=ev["seconds"], model=ev["model"])
                elif ev["type"] == "error":
                    entry.update(error=ev["message"], cost=ev.get("cost", 0))
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
        print(f"     -> {entry.get('error') or entry['answer']['status']}  ${entry.get('cost', 0):.3f}", flush=True)
        results.append(entry)

    out = Path("eval-results")
    out.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (out / f"{stamp}.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / f"{stamp}.md").write_text(to_markdown(results), encoding="utf-8")
    total = sum(r.get("cost", 0) for r in results)
    print(f"total ${total:.2f}; report: {out / (stamp + '.md')}")


if __name__ == "__main__":
    asyncio.run(main())
