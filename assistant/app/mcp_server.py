"""MCP endpoint: the documentation as tools for any MCP client.

Mounted at ``/mcp`` by main.py (Streamable HTTP, stateless, no auth). The
tools are the same ones the Command Assistant's agent uses, over the same
corpus (``llms-full.txt`` of each published docs version), so an agent in
Claude Code, Cursor, or Claude.ai searches and reads the docs the way the
assistant does, and always the version that is currently published.

    claude mcp add --transport http simplyblock-docs https://docs-assistant.simplyblock.io/mcp
"""

from __future__ import annotations

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import Field

from .config import settings
from .docs import Corpus, library
from .events import log

INSTRUCTIONS = (
    "Tools over the simplyblock documentation (docs.simplyblock.io): a software-defined NVMe-over-TCP "
    "block storage platform for Kubernetes and Linux. Start with search_docs using specific terms "
    "(commands, resource names, platform names), then read_page for the pages that matter. Every result "
    "carries the URL of the page to cite. The version parameter selects a documentation version; omit it "
    "for the latest release. Commands and configuration must be copied from the pages, not guessed."
)

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)

Version = Annotated[
    str,
    Field(description="Documentation version, such as 'latest', 'dev', or '25.10'. See list_versions.", max_length=64),
]

server = MCPServer(
    name="simplyblock-docs",
    title="simplyblock documentation",
    instructions=INSTRUCTIONS,
    website_url=settings.docs_base,
)


async def _corpus(version: str) -> Corpus:
    name = (version or "latest").strip("/")
    known = await library.versions()
    if name not in known:
        raise ToolError(f"no documentation version {version!r}; call list_versions for the published ones")
    try:
        return await library.corpus(known[name])
    except LookupError as exc:
        raise ToolError(str(exc)) from exc


@server.tool(annotations=READ_ONLY)
async def search_docs(
    query: Annotated[str, Field(description="Search terms", min_length=1, max_length=500)],
    version: Version = "latest",
    limit: Annotated[int, Field(description="Maximum number of results", ge=1, le=25)] = 8,
) -> dict:
    """Full-text search over the simplyblock documentation.

    Returns the best matching sections (page path, page title, section heading, snippet, URL).
    Use specific terms: product names, commands, resource kinds, platform names. Read the
    matching pages with read_page.
    """
    corpus = await _corpus(version)
    results = []
    for r in corpus.search(query, limit=limit):
        anchor = _anchor(corpus, r)
        results.append({**r, "url": corpus.page_url(r["page"]) + (f"#{anchor}" if anchor else "")})
    log("mcp_search", version=corpus.version, query=query, results=len(results))
    return {"version": corpus.version, "results": results}


def _anchor(corpus: Corpus, result: dict) -> str:
    page = corpus.pages.get(result["page"])
    if not page or not result["section"]:
        return ""
    for anchor, heading in page.headings.items():
        if heading == result["section"]:
            return anchor
    return ""


@server.tool(annotations=READ_ONLY)
async def read_page(
    page: Annotated[str, Field(description="Page path or URL, as returned by search_docs or list_pages", max_length=500)],
    version: Version = "latest",
    offset: Annotated[int, Field(description="Character offset; 0 for the start of the page", ge=0)] = 0,
) -> dict:
    """Read a documentation page as Markdown.

    Long pages are returned in chunks; when next_offset is set, call again with that offset
    for the rest of the page.
    """
    corpus = await _corpus(version)
    result = corpus.read(page, offset)
    if "error" in result:
        raise ToolError(result["error"])
    result["url"] = corpus.page_url(result["page"])
    result["version"] = corpus.version
    return result


@server.tool(annotations=READ_ONLY)
async def list_pages(
    prefix: Annotated[str, Field(description="Path prefix, such as 'kubernetes/installation/'; empty for all pages", max_length=500)] = "",
    version: Version = "latest",
) -> dict:
    """List documentation pages (path, title, URL) whose path starts with a prefix."""
    corpus = await _corpus(version)
    pages = [{**p, "url": corpus.page_url(p["page"])} for p in corpus.list_pages(prefix)]
    return {"version": corpus.version, "pages": pages}


@server.tool(annotations=READ_ONLY)
async def list_versions() -> dict:
    """List the published documentation versions and their aliases (such as 'latest')."""
    return {"versions": await library.catalog()}


MCP_PATH = "/mcp"


def routes() -> list:
    """The Starlette route of the MCP endpoint, added to the API's router.

    Added as a route rather than mounted as a sub-application, so that a POST
    to the exact path /mcp is served instead of redirected to /mcp/, which not
    every MCP client follows.

    Stateless: every request stands alone, so no session affinity is needed
    behind the proxy. JSON responses rather than SSE: nothing streams here.
    The host-header check is off because the service sits behind TLS on a
    public hostname rather than on localhost.
    """
    inner = server.streamable_http_app(
        streamable_http_path=MCP_PATH,
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
    return list(inner.routes)
