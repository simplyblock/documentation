# Markdown mirrors

Every page of the documentation ships twice: as the themed HTML a human reads, and as a
Markdown twin an AI agent reads. The twin costs about 5% of what the HTML costs
(21.0 MB of HTML across 174 pages against 1.03 MB of Markdown), which is the difference
between an agent reading a page and an agent truncating it.

`md_mirror.py` is a MkDocs hook, registered in `mkdocs.yml`:

```yaml
hooks:
  - scripts/hooks/md_mirror.py
```

## What it writes

```
site/kubernetes/installation.md   twin of /kubernetes/installation/
site/kubernetes/index.md          twin of /kubernetes/
site/llms.txt                     index of every page, https://llmstxt.org/
site/llms-full.txt                the whole documentation in one file (~1 MB)
```

Mirrors are written into `site/`, so they ride into `deployment/<version>/` and up to the
web server with everything else. No CI change, no new dependency — the hook is standard
library only.

## Why a hook and not a copy of `docs/`

The source files are not the documentation. 64 of them contain Jinja: 295 occurrences of
`{{ cliname }}`, 9 of `{{ experimental }}`, and 7 `{% include %}` statements pulling in
`snippets/`. On top of that, `docs/reference/cli/` and `docs/reference/operator/` are
generated during the build and are not in the repository at all.

The hook runs on `on_page_markdown`, which fires after the macros plugin, so it sees the
same content the HTML does: `sbctl` instead of `{{ cliname }}`, snippets already inlined,
generated reference pages included.

## Why mirrors sit at the source path

`docs/kubernetes/installation.md` renders to `/kubernetes/installation/` and mirrors to
`site/kubernetes/installation.md`. Two things fall out of that layout for free:

- It answers the `<url>.md` convention that agents guess at, the one Anthropic, Cloudflare,
  and Mintlify-hosted documentation sites all follow.
- Every relative link in the source keeps working. All 332 internal links in the
  documentation point at sibling `.md` files, and between mirrors they resolve to exactly
  the same targets, so no link rewriting happens and nothing can silently break.

Section indexes are the one exception to `<url>.md`: `/kubernetes/` mirrors to
`/kubernetes/index.md`, because that is where the source file lives. Both spellings are
valid under the llms.txt convention, and the web server rules below serve either.

## Kill switches

```
MD_MIRROR=0             skip mirrors and index files entirely
MD_MIRROR_LLMS_TXT=0    skip llms.txt
MD_MIRROR_LLMS_FULL=0   skip llms-full.txt
```

No failure in the hook can fail a build. Every write is guarded and logged.

## Pages that cannot be mirrored

`docs/reference/api/reference.md` renders an interactive Swagger widget from
`openapi.json`, which has no meaningful Markdown form. Its mirror carries a pointer to the
specification instead. The substitution lives in the `STUBS` dictionary at the top of the
hook; add an entry there for any future page that renders to a JavaScript widget.

## Serving

The rules live in `deployment/.htaccess`. Three things matter.

**Content type.** Without `AddType text/markdown;charset=UTF-8 .md`, Apache sends the
mirrors as `application/octet-stream`: browsers download them and some agents drop them.

**Content negotiation.** A request carrying `Accept: text/markdown` gets the mirror of the
page it asked for; everything else keeps the HTML. This is the only discovery path that
requires the agent to know nothing at all — it requests the URL it already has. Claude Code,
Cursor, and OpenCode send that header today.

A URL without its trailing slash still redirects once (`/kubernetes/installation` →
`/kubernetes/installation/`) before the negotiation applies, because Apache canonicalizes
the directory URL first. Agents follow the redirect and land on the Markdown.

**Advertisement.** Each page carries `<link rel="alternate" type="text/markdown">` in its
head (from `templates/main.html`) and the same link as an HTTP `Link:` response header, for
clients that never parse HTML.

If the documentation ever moves off Apache, the nginx equivalent is:

```nginx
types { text/markdown  md; }
charset_types text/markdown text/plain text/css application/javascript;

# Empty for everyone but a client asking for Markdown, so the try_files below
# falls straight through to the HTML in the ordinary case.
map $http_accept $md {
    default        "";
    ~text/markdown ".md";
}

location ~ ^/(?<page>.+)/$ {
    try_files /$page$md /$page/index$md /$page/index.html =404;
}
```

## Verifying a deployment

```bash
curl -sI https://docs.simplyblock.io/latest/kubernetes/installation.md | grep -i content-type
# text/markdown; charset=utf-8

curl -sI https://docs.simplyblock.io/latest/kubernetes/installation/ | grep -i '^link'
# <...installation.md>; rel="alternate"; type="text/markdown", </latest/llms.txt>; rel="describedby"

curl -s -H 'Accept: text/markdown' https://docs.simplyblock.io/latest/kubernetes/installation/ | head -3
# front matter, not <!doctype html>

curl -s https://docs.simplyblock.io/llms.txt | head -20
```

## What was deliberately left out

The mirrors are not in `sitemap.xml`. They are alternates of pages already listed there,
and `rel="alternate"` is the signal that says so; listing both invites duplicate-content
handling for no gain.

They are also not `noindex`. A search engine that indexes a mirror is not a problem the
alternate relation does not already solve, and `X-Robots-Tag: noindex` would risk telling
the AI crawlers we are trying to reach that the file is not worth having.

Keep expectations for `llms.txt` itself modest: Google has stated Search ignores it, and
log studies put the share of `llms.txt` files that ever get requested in the low single
digits. It is written because it is free from the same loop that writes the mirrors. The
mirrors are the part that pays.
