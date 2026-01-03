import logging
import os
import sys
from collections.abc import Sequence
from typing import Any

from dotenv import load_dotenv

# UTF-8 fix for Windows MCP STDIO communication
if sys.platform == "win32":
    if not os.environ.get("PYTHONIOENCODING"):
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

load_dotenv()

from . import tools  # Note: tools.py validates OBSIDIAN_API_KEY at import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-obsidian")

app = Server("mcp-obsidian")

tool_handlers = {}


def add_tool_handler(tool_class: tools.ToolHandler):
    global tool_handlers

    tool_handlers[tool_class.name] = tool_class


def get_tool_handler(name: str) -> tools.ToolHandler | None:
    if name not in tool_handlers:
        return None

    return tool_handlers[name]


add_tool_handler(tools.ListFilesInDirToolHandler())
add_tool_handler(tools.ListFilesInVaultToolHandler())
add_tool_handler(tools.GetFileContentsToolHandler())
add_tool_handler(tools.GetFileContentsByNameToolHandler())
add_tool_handler(tools.SearchToolHandler())
if not tools.read_only_mode:
    add_tool_handler(tools.PatchContentToolHandler())
if not tools.read_only_mode:
    add_tool_handler(tools.AppendContentToolHandler())
if not tools.read_only_mode:
    add_tool_handler(tools.PutContentToolHandler())
if not tools.read_only_mode:
    add_tool_handler(tools.DeleteFileToolHandler())
add_tool_handler(tools.ComplexSearchToolHandler())
add_tool_handler(tools.BatchGetFileContentsToolHandler())
add_tool_handler(tools.PeriodicNotesToolHandler())
add_tool_handler(tools.RecentPeriodicNotesToolHandler())
add_tool_handler(tools.RecentChangesToolHandler())
add_tool_handler(tools.DataviewQueryToolHandler())
add_tool_handler(tools.GetActiveNoteToolHandler())
if not tools.read_only_mode:
    add_tool_handler(tools.AppendToActiveToolHandler())
if not tools.read_only_mode:
    add_tool_handler(tools.ReplaceActiveNoteToolHandler())
if not tools.read_only_mode:
    add_tool_handler(tools.PatchActiveNoteToolHandler())
if not tools.read_only_mode:
    add_tool_handler(tools.DeleteActiveNoteToolHandler())
if not tools.read_only_mode:
    add_tool_handler(tools.AppendToPeriodicToolHandler())
if not tools.read_only_mode:
    add_tool_handler(tools.ReplacePeriodicNoteToolHandler())
if not tools.read_only_mode:
    add_tool_handler(tools.PatchPeriodicNoteToolHandler())
if not tools.read_only_mode:
    add_tool_handler(tools.DeletePeriodicNoteToolHandler())
add_tool_handler(tools.ListCommandsToolHandler())
if not tools.read_only_mode:
    add_tool_handler(tools.ExecuteCommandToolHandler())
add_tool_handler(tools.OpenFileToolHandler())


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""

    return [th.get_tool_description() for th in tool_handlers.values()]


@app.call_tool()
async def call_tool(
    name: str, arguments: Any
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for command line run."""

    if not isinstance(arguments, dict):
        raise RuntimeError("arguments must be dictionary")

    tool_handler = get_tool_handler(name)
    if not tool_handler:
        raise ValueError(f"Unknown tool: {name}")

    try:
        return tool_handler.run_tool(arguments)
    except Exception as e:
        logger.error(str(e))
        raise RuntimeError(f"Caught Exception. Error: {str(e)}")


async def main():
    # Import here to avoid issues with event loops
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
