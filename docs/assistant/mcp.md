---
title: "MCP Server"
description: "The simplyblock documentation as an MCP server, so AI agents in Claude Code, Cursor, Claude.ai, and other MCP clients search and read it directly."
weight: 10595
---

The documentation is published as a [Model Context Protocol](https://modelcontextprotocol.io/){:target="_blank" rel="noopener"} (MCP) server, so an
AI agent can search and read it instead of answering from memory. The server runs on the same host as the
[Command Assistant](index.md) and is public. No account, key, or token is required.

```plain title="Endpoint"
{{ config.extra.assistant.mcp }}
```

The transport is Streamable HTTP. Every request stands alone, so the endpoint works from any MCP client that
supports remote servers, including Claude Code, Claude.ai and Claude Desktop (as a custom connector), Cursor, Visual
Studio Code, and Windsurf.

## Setup

Claude Code registers the server with one command:

```bash title="Registering the server in Claude Code"
claude mcp add --transport http simplyblock-docs {{ config.extra.assistant.mcp }}
```

Cursor, Visual Studio Code, Windsurf, and most other clients read a JSON configuration. The entry is the same in each
of them, apart from the name of the file:

```json title="Entry for JSON-configured clients"
{
  "mcpServers": {
    "simplyblock-docs": {
      "url": "{{ config.extra.assistant.mcp }}"
    }
  }
}
```

In Claude.ai and Claude Desktop, the URL is added under **Settings > Connectors > Add custom connector**.

## Tools

| Tool            | Arguments                   | Returns                                                                  |
|-----------------|-----------------------------|--------------------------------------------------------------------------|
| `search_docs`   | `query`, `version`, `limit` | The best matching sections: page, title, section heading, snippet, URL   |
| `read_page`     | `page`, `version`, `offset` | The page as Markdown, read in chunks with `offset` when it is long       |
| `list_pages`    | `prefix`, `version`         | Path, title, and URL of the pages whose path starts with `prefix`        |
| `list_versions` |                             | The published documentation versions and their aliases, such as `latest` |

The `version` argument selects a documentation version and defaults to `latest`. Every published version is
available, so an agent can be pointed at the version that is installed in a cluster. The content is the same
Markdown that is served next to every page of the documentation, and it is refreshed within minutes of a
documentation release.

## Example

A request such as "install simplyblock on a three-node Red Hat OpenShift cluster, the cluster runs version 25.10"
leads an agent to call `search_docs` with the terms of the request, read the matching installation pages with
`read_page`, and answer with the documented commands, each linked to the page it was taken from.

!!! warning "Check Before Running"
    The agent, not the documentation, composes the answer. Commands and configuration must be compared with the
    linked pages before they are run on a production system.
