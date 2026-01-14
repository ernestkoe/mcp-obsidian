# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server that enables AI assistants to interact with Obsidian vaults via the [Local REST API community plugin](https://github.com/coddingtonbear/obsidian-local-rest-api).

## Development Commands

```bash
# Sync dependencies and update lockfile
uv sync

# Run the server locally (for development)
uv run mcp-obsidian

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_obsidian.py -v

# Run a specific test
uv run pytest tests/test_obsidian.py::TestObsidianClient::test_get_file_contents -v

# Type checking
uv run pyright src/

# Debug with MCP Inspector
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp-obsidian run mcp-obsidian

# View server logs (macOS)
tail -n 20 -f ~/Library/Logs/Claude/mcp-server-mcp-obsidian.log
```

## Architecture

The codebase follows a simple three-layer structure:

1. **`server.py`** - MCP server setup and request routing. Registers tool handlers and dispatches incoming tool calls. Entry point is `main()` which runs the stdio server.

2. **`tools.py`** - Tool handler classes. Each tool extends `ToolHandler` base class with:
   - `get_tool_description()` - Returns MCP `Tool` schema
   - `run_tool(args)` - Executes the tool logic

3. **`obsidian.py`** - HTTP client for Obsidian's Local REST API. The `Obsidian` class wraps all REST endpoints with `_safe_call()` for error handling.

### Adding a New Tool

1. Create a new `ToolHandler` subclass in `tools.py`
2. Implement `get_tool_description()` with the tool's JSON schema
3. Implement `run_tool()` calling the appropriate `Obsidian` client method
4. Register the handler in `server.py` via `add_tool_handler()`

### Environment Configuration

Required: `OBSIDIAN_API_KEY`

Optional (with defaults):
- `OBSIDIAN_HOST` (default: 127.0.0.1)
- `OBSIDIAN_PORT` (default: 27124)
- `OBSIDIAN_PROTOCOL` (default: https)

## Feature Development Process

Follow TDD (Test-Driven Development) for new features:

1. **Branch** - `git checkout -b feature/short-name`
2. **PRD** - Write `docs/PRD-feature-name.md` documenting:
   - Problem statement
   - Proposed solution
   - Test cases
3. **Tests** - Write failing tests based on PRD test cases
4. **Implement** - Write code until tests pass
5. **Verify** - `uv run pytest` (all tests green)
6. **Commit** - Descriptive commit message
7. **PR** - `gh pr create`
8. **Validate** - Test against real vault (optional but recommended)
9. **Merge** - `gh pr merge --squash --delete-branch`

PRDs live in `docs/` and serve as documentation for why changes were made.

## Architectural Decisions

### No Community Plugin Dependencies

**Rule**: Only rely on core Local REST API endpoints. Do not add features that require additional Obsidian community plugins.

**Rationale**:
- Reduces friction for users (only one plugin to install)
- Avoids breaking when community plugins change APIs
- Keeps the MCP server portable and predictable

**Current violations to address**:
1. `obsidian_dataview_query` - requires Dataview plugin → deprecate/remove
2. `obsidian_get_recent_changes` - requires Dataview plugin → reimplement using file metadata
3. Periodic Notes (weekly/monthly/quarterly/yearly) - requires Periodic Notes plugin → implement via folder conventions or file patterns

**Allowed**: Core Daily Notes (built into Obsidian) works without additional plugins.
