"""Render the Command Assistant widget.

Replaces the marker ``<!-- sb:command-assistant -->`` in a page with the form
that ``docs/assets/javascripts/assistant.js`` drives. The API endpoint and the
optional Cloudflare Turnstile site key come from ``extra.assistant`` in
``mkdocs.yml``; the API itself lives in ``assistant/`` (see its README).
"""

from __future__ import annotations

import html

MARKER = "<!-- sb:command-assistant -->"
EXAMPLES = (
    "install on openshift 3 node cluster",
    "add a storage node to a running cluster",
    "set up disaster recovery between two sites",
    "create a volume with a snapshot schedule",
)


def _widget(config) -> str:
    opts = (config.get("extra") or {}).get("assistant") or {}
    api = html.escape(str(opts.get("api") or "/api/assistant"), quote=True)
    sitekey = html.escape(str(opts.get("turnstile_sitekey") or ""), quote=True)
    examples = "".join(f'<button type="button">{html.escape(e)}</button>' for e in EXAMPLES)
    return (
        f'<div class="sb-assistant" data-sb-assistant data-api="{api}" data-turnstile="{sitekey}">'
        '<form class="sb-assistant__form" data-sb-assistant-form>'
        '<label class="sb-assistant__label" for="sb-assistant-q">What do you want to do?</label>'
        '<div class="sb-assistant__row">'
        '<input id="sb-assistant-q" class="sb-assistant__input" name="q" type="text" maxlength="400" '
        'autocomplete="off" placeholder="install on openshift 3 node cluster" required>'
        '<button class="md-button md-button--primary sb-assistant__submit" type="submit">Show commands</button>'
        "</div>"
        f'<div class="sb-assistant__examples" data-sb-assistant-examples><span>Try:</span>{examples}</div>'
        '<div class="sb-assistant__turnstile" data-sb-assistant-turnstile></div>'
        "</form>"
        '<div class="sb-assistant__progress" data-sb-assistant-progress hidden></div>'
        '<div class="sb-assistant__result" data-sb-assistant-result aria-live="polite"></div>'
        "<noscript>The Command Assistant needs JavaScript. All procedures are also in the navigation.</noscript>"
        "</div>"
    )


def on_page_markdown(markdown: str, *, page, config, files) -> str:
    if MARKER not in markdown:
        return markdown
    return markdown.replace(MARKER, _widget(config))
