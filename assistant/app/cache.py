"""Answer cache: similar questions, kept on disk, valid as long as its pages are unchanged.

* Similar questions share one answer. A question is reduced to a key: lowercase
  words without filler ("a", "my", "please", "new", "running", ...), simple
  plural and verb endings removed, a few synonyms merged, sorted. Numbers and
  every other word stay in the key, so "3 node" and "5 node", or "add" and
  "remove", never share an answer.
* An answer records the pages it was built from (read or cited) and their
  digests. It is served only while every one of those pages is unchanged in the
  current docs of that version, so a docs change retires exactly the answers it
  affects. A change of prompt, answer format, or model retires all of them.
* Entries are written to ASSISTANT_CACHE_FILE (when set), so restarts and
  redeploys keep them.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from pathlib import Path

from .config import settings
from .docs import Corpus

FILLER = {
    # articles, pronouns, prepositions, auxiliaries
    "a", "an", "the", "my", "our", "your", "me", "we", "i", "it", "its", "this", "that", "these", "those",
    "to", "on", "in", "into", "onto", "of", "for", "with", "at", "by", "from", "as", "and", "or",
    "is", "are", "be", "do", "does", "can", "could", "should", "would", "will", "want", "need", "like",
    "how", "what", "which", "please", "help", "show", "give", "tell", "steps", "step", "command", "commands",
    "way", "guide", "simplyblock", "sb", "up",
    # adjectives that do not change the procedure
    "new", "existing", "running", "current", "already", "live", "fresh",
}
SYNONYMS = {
    "k8s": "kubernetes", "ocp": "openshift", "installation": "install", "installing": "install",
    "nodes": "node", "clusters": "cluster", "volumes": "volume", "pvc": "volume", "pvcs": "volume",
    "snapshots": "snapshot", "disks": "disk", "drives": "disk", "drive": "disk", "dr": "disaster recovery",
    "removing": "remove", "delete": "remove", "deleting": "remove", "adding": "add", "creating": "create",
    "upgrading": "upgrade", "setup": "configure", "set": "configure", "configuring": "configure",
}
WORD_RE = re.compile(r"[a-z0-9][a-z0-9.+-]*")


def key(question: str) -> str:
    words = []
    for w in WORD_RE.findall(question.lower()):
        w = w.strip(".-+")
        if not w or w in FILLER:
            continue
        w = SYNONYMS.get(w, w)
        if not w.isdigit() and len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        w = SYNONYMS.get(w, w)
        words.extend(x for x in w.split() if x not in FILLER)
    return " ".join(sorted(set(words)))


class AnswerCache:
    def __init__(self, path: str = "") -> None:
        self.path = Path(path) if path else None
        self.items: dict[str, dict] = {}
        self._load()

    @staticmethod
    def _id(version: str, question: str) -> str:
        return f"{version}|{key(question)}"

    def _load(self) -> None:
        if not self.path or not self.path.exists():
            return
        try:
            self.items = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            self.items = {}

    def _save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".cache-")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False)
        os.replace(tmp, self.path)

    def valid(self, entry: dict, corpus: Corpus, fingerprint: str) -> bool:
        if entry.get("fingerprint") != fingerprint:
            return False
        if time.time() - entry.get("ts", 0) > settings.cache_ttl:
            return False
        pages = entry.get("pages") or {}
        if not pages:
            return False
        for path, digest in pages.items():
            page = corpus.find(path)
            if not page or page.digest != digest:
                return False
        return True

    def get(self, corpus: Corpus, question: str, fingerprint: str) -> dict | None:
        entry = self.items.get(self._id(corpus.version, question))
        if entry and self.valid(entry, corpus, fingerprint):
            return entry["event"]
        return None

    def put(self, corpus: Corpus, question: str, fingerprint: str, event: dict, pages: dict) -> None:
        self.items[self._id(corpus.version, question)] = {
            "question": question,
            "ts": time.time(),
            "fingerprint": fingerprint,
            "pages": pages,
            "event": event,
        }
        # Drop what can never be served again (another fingerprint, expired).
        now = time.time()
        self.items = {
            k: v for k, v in self.items.items()
            if v.get("fingerprint") == fingerprint and now - v.get("ts", 0) <= settings.cache_ttl
        }
        self._save()


cache = AnswerCache(settings.cache_file)
