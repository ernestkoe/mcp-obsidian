from collections.abc import Sequence
from mcp.types import (
    Tool,
    ToolAnnotations,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import json
import os
from . import obsidian

api_key = os.getenv("OBSIDIAN_API_KEY", "")
obsidian_host = os.getenv("OBSIDIAN_HOST", "127.0.0.1")

if api_key == "":
    raise ValueError(
        f"OBSIDIAN_API_KEY environment variable required. Working directory: {os.getcwd()}"
    )

TOOL_LIST_FILES_IN_VAULT = "obsidian_list_files_in_vault"
TOOL_LIST_FILES_IN_DIR = "obsidian_list_files_in_dir"


class ToolHandler:
    def __init__(self, tool_name: str):
        self.name = tool_name

    def get_tool_description(self) -> Tool:
        raise NotImplementedError()

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        raise NotImplementedError()


class ListFilesInVaultToolHandler(ToolHandler):
    def __init__(self):
        super().__init__(TOOL_LIST_FILES_IN_VAULT)

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Lists all files and directories in the root directory of your Obsidian vault.",
            inputSchema={"type": "object", "properties": {}, "required": []},
            annotations=ToolAnnotations(
                readOnlyHint=True,
            ),
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)

        files = api.list_files_in_vault()

        return [
            TextContent(
                type="text", text=json.dumps(files, indent=2, ensure_ascii=False)
            )
        ]


class ListFilesInDirToolHandler(ToolHandler):
    def __init__(self):
        super().__init__(TOOL_LIST_FILES_IN_DIR)

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Lists all files and directories that exist in a specific Obsidian directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dirpath": {
                        "type": "string",
                        "description": "Path to list files from (relative to your vault root). Note that empty directories will not be returned.",
                    },
                },
                "required": ["dirpath"],
            },
            annotations=ToolAnnotations(
                readOnlyHint=True,
            ),
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "dirpath" not in args:
            raise RuntimeError("dirpath argument missing in arguments")

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)

        files = api.list_files_in_dir(args["dirpath"])

        return [
            TextContent(
                type="text", text=json.dumps(files, indent=2, ensure_ascii=False)
            )
        ]


class GetFileContentsToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_get_file_contents")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Return the content of a single file in your vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the relevant file (relative to your vault root).",
                        "format": "path",
                    },
                },
                "required": ["filepath"],
            },
            annotations=ToolAnnotations(
                readOnlyHint=True,
            ),
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "filepath" not in args:
            raise RuntimeError("filepath argument missing in arguments")

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)

        content = api.get_file_contents(args["filepath"])

        return [
            TextContent(
                type="text", text=json.dumps(content, indent=2, ensure_ascii=False)
            )
        ]


class SearchToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_simple_search")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="""Simple search for documents matching a specified text query across all files in the vault. 
            Use this tool when you want to do a simple text search""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to a simple search for in the vault.",
                    },
                    "context_length": {
                        "type": "integer",
                        "description": "How much context to return around the matching string (default: 100)",
                        "default": 100
                    },
                    "limit": {
                        "type": "integer",
                        "description": "How many contexts to return at most (default: 100)",
                        "default": 100
                    },
                },
                "required": ["query"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "query" not in args:
            raise RuntimeError("query argument missing in arguments")

        context_length = args.get("context_length", 100)
        limit = args.get("limit", 100)
        
        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        results = api.search(args["query"], context_length, limit)
        
        formatted_results = []
        total_results = 0
        for result in results:
            if total_results >= limit:
                break
            formatted_matches = []
            for match in result.get("matches", []):
                if total_results >= limit:
                    break
                context = match.get("context", "")
                match_pos = match.get("match", {})
                start = match_pos.get("start", 0)
                end = match_pos.get("end", 0)

                formatted_matches.append(
                    {"context": context, "match_position": {"start": start, "end": end}}
                )
                total_results = total_results + 1

            formatted_results.append(
                {
                    "filename": result.get("filename", ""),
                    "score": result.get("score", 0),
                    "matches": formatted_matches,
                }
            )

        return [
            TextContent(
                type="text",
                text=json.dumps(formatted_results, indent=2, ensure_ascii=False),
            )
        ]


class AppendContentToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_append_content")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Append content to a new or existing file in the vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file (relative to vault root)",
                        "format": "path",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to append to the file",
                    },
                },
                "required": ["filepath", "content"],
            },
            annotations=ToolAnnotations(
                destructiveHint=True,
            ),
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "filepath" not in args or "content" not in args:
            raise RuntimeError("filepath and content arguments required")

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        api.append_content(args.get("filepath", ""), args["content"])

        return [
            TextContent(
                type="text", text=f"Successfully appended content to {args['filepath']}"
            )
        ]


class PatchContentToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_patch_content")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Insert content into an existing note relative to a heading, block reference, or frontmatter field. For headings, automatically creates the heading if it doesn't exist, positioning it based on a template structure if available.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file (relative to vault root)",
                        "format": "path",
                    },
                    "operation": {
                        "type": "string",
                        "description": "Operation to perform (append, prepend, or replace)",
                        "enum": ["append", "prepend", "replace"],
                    },
                    "target_type": {
                        "type": "string",
                        "description": "Type of target to patch",
                        "enum": ["heading", "block", "frontmatter"],
                    },
                    "target": {
                        "type": "string",
                        "description": "Target identifier (heading path, block reference, or frontmatter field)",
                    },
                    "content": {"type": "string", "description": "Content to insert"},
                    "create_heading_if_missing": {
                        "type": "boolean",
                        "description": "If true (default), automatically create the heading when target_type is 'heading' and the heading doesn't exist. Set to false to get an error instead.",
                        "default": True,
                    },
                    "template_path": {
                        "type": "string",
                        "description": "Optional path to a template file that defines the heading order. If not specified, checks frontmatter 'template:' field, then falls back to folder convention (e.g., 'Daily Notes/*.md' uses 'Templates/Daily Notes.md').",
                    },
                    "use_template": {
                        "type": "boolean",
                        "description": "If true (default), use template to determine where to insert new headings. If false, always append to end.",
                        "default": True,
                    },
                },
                "required": [
                    "filepath",
                    "operation",
                    "target_type",
                    "target",
                    "content",
                ],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if not all(
            k in args
            for k in ["filepath", "operation", "target_type", "target", "content"]
        ):
            raise RuntimeError(
                "filepath, operation, target_type, target and content arguments required"
            )

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        api.patch_content(
            args.get("filepath", ""),
            args.get("operation", ""),
            args.get("target_type", ""),
            args.get("target", ""),
            args.get("content", ""),
            args.get("create_heading_if_missing", True),
            args.get("template_path"),
            args.get("use_template", True),
        )

        return [
            TextContent(
                type="text", text=f"Successfully patched content in {args['filepath']}"
            )
        ]


class PutContentToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_put_content")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Create a new file in your vault or update the content of an existing one in your vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the relevant file (relative to your vault root)",
                        "format": "path",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content of the file you would like to upload",
                    },
                },
                "required": ["filepath", "content"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "filepath" not in args or "content" not in args:
            raise RuntimeError("filepath and content arguments required")

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        api.put_content(args.get("filepath", ""), args["content"])

        return [
            TextContent(
                type="text", text=f"Successfully uploaded content to {args['filepath']}"
            )
        ]


class DeleteFileToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_delete_file")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Delete a file or directory from the vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file or directory to delete (relative to vault root)",
                        "format": "path",
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Confirmation to delete the file (must be true)",
                        "default": False,
                    },
                },
                "required": ["filepath", "confirm"],
            },
            annotations=ToolAnnotations(
                destructiveHint=True,
            ),
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "filepath" not in args:
            raise RuntimeError("filepath argument missing in arguments")

        if not args.get("confirm", False):
            raise RuntimeError("confirm must be set to true to delete a file")

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        api.delete_file(args["filepath"])

        return [
            TextContent(type="text", text=f"Successfully deleted {args['filepath']}")
        ]


class ComplexSearchToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_complex_search")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="""Complex search for documents using a JsonLogic query. 
           Supports standard JsonLogic operators plus 'glob' and 'regexp' for pattern matching. Results must be non-falsy.

           Use this tool when you want to do a complex search, e.g. for all documents with certain tags etc.
           ALWAYS follow query syntax in examples.

           Examples
            1. Match all markdown files
            {"glob": ["*.md", {"var": "path"}]}

            2. Match all markdown files with 1221 substring inside them
            {
              "and": [
                { "glob": ["*.md", {"var": "path"}] },
                { "regexp": [".*1221.*", {"var": "content"}] }
              ]
            }

            3. Match all markdown files in Work folder containing name Keaton
            {
              "and": [
                { "glob": ["*.md", {"var": "path"}] },
                { "regexp": [".*Work.*", {"var": "path"}] },
                { "regexp": ["Keaton", {"var": "content"}] }
              ]
            }
           """,
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "object",
                        "description": "JsonLogic query object (see examples in tool description)",
                    }
                },
                "required": ["query"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "query" not in args:
            raise RuntimeError("query argument missing in arguments")

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        results = api.search_json(args.get("query", ""))

        return [
            TextContent(
                type="text", text=json.dumps(results, indent=2, ensure_ascii=False)
            )
        ]


class BatchGetFileContentsToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_batch_get_file_contents")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Return the contents of multiple files in your vault, concatenated with headers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepaths": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "Path to a file (relative to your vault root)",
                            "format": "path",
                        },
                        "description": "List of file paths to read",
                    },
                },
                "required": ["filepaths"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "filepaths" not in args:
            raise RuntimeError("filepaths argument missing in arguments")

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        content = api.get_batch_file_contents(args["filepaths"])

        return [TextContent(type="text", text=content)]


class PeriodicNotesToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_get_periodic_note")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Get current periodic note for the specified period.",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "The period type (daily, weekly, monthly, quarterly, yearly)",
                        "enum": ["daily", "weekly", "monthly", "quarterly", "yearly"],
                    },
                    "as_json": {
                        "type": "boolean",
                        "description": "Whether to return JSON format with metadata (default: false)",
                        "default": False,
                    },
                },
                "required": ["period"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "period" not in args:
            raise RuntimeError("period argument missing in arguments")

        period = args["period"]
        valid_periods = ["daily", "weekly", "monthly", "quarterly", "yearly"]
        if period not in valid_periods:
            raise RuntimeError(
                f"Invalid period: {period}. Must be one of: {', '.join(valid_periods)}"
            )

        as_json = args.get("as_json", False)

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        content = api.get_periodic_note(period, as_json)

        if as_json:
            return [
                TextContent(
                    type="text", text=json.dumps(content, indent=2, ensure_ascii=False)
                )
            ]
        else:
            return [TextContent(type="text", text=content)]


class RecentPeriodicNotesToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_get_recent_periodic_notes")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Get most recent periodic notes for the specified period type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "The period type (daily, weekly, monthly, quarterly, yearly)",
                        "enum": ["daily", "weekly", "monthly", "quarterly", "yearly"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of notes to return (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 50,
                    },
                    "include_content": {
                        "type": "boolean",
                        "description": "Whether to include note content (default: false)",
                        "default": False,
                    },
                },
                "required": ["period"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "period" not in args:
            raise RuntimeError("period argument missing in arguments")

        period = args["period"]
        valid_periods = ["daily", "weekly", "monthly", "quarterly", "yearly"]
        if period not in valid_periods:
            raise RuntimeError(
                f"Invalid period: {period}. Must be one of: {', '.join(valid_periods)}"
            )

        limit = args.get("limit", 5)
        if not isinstance(limit, int) or limit < 1:
            raise RuntimeError(f"Invalid limit: {limit}. Must be a positive integer")

        include_content = args.get("include_content", False)
        if not isinstance(include_content, bool):
            raise RuntimeError(
                f"Invalid include_content: {include_content}. Must be a boolean"
            )

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        results = api.get_recent_periodic_notes(period, limit, include_content)

        return [
            TextContent(
                type="text", text=json.dumps(results, indent=2, ensure_ascii=False)
            )
        ]


class RecentChangesToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_get_recent_changes")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Get recently modified files in the vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of files to return (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "days": {
                        "type": "integer",
                        "description": "Only include files modified within this many days (default: 90)",
                        "minimum": 1,
                        "default": 90,
                    },
                },
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        limit = args.get("limit", 10)
        if not isinstance(limit, int) or limit < 1:
            raise RuntimeError(f"Invalid limit: {limit}. Must be a positive integer")

        days = args.get("days", 90)
        if not isinstance(days, int) or days < 1:
            raise RuntimeError(f"Invalid days: {days}. Must be a positive integer")

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        results = api.get_recent_changes(limit, days)

        return [
            TextContent(
                type="text", text=json.dumps(results, indent=2, ensure_ascii=False)
            )
        ]


class DataviewQueryToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_dataview_query")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Execute a Dataview DQL query against the vault. Requires the Dataview plugin.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The Dataview query string (e.g., 'TABLE title, status FROM #tag'). Note: Does not support TABLE WITHOUT ID queries.",
                    }
                },
                "required": ["query"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "query" not in args:
            raise RuntimeError("query argument missing")

        query = args["query"]
        if not isinstance(query, str):
            raise RuntimeError("query must be a string")

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        results = api.dataview_query(query)

        return [
            TextContent(
                type="text", text=json.dumps(results, indent=2, ensure_ascii=False)
            )
        ]


class GetActiveNoteToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_get_active")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Get content of the currently active note in Obsidian.",
            inputSchema={
                "type": "object",
                "properties": {
                    "as_json": {
                        "type": "boolean",
                        "description": "Whether to return JSON format with metadata (default: false)",
                        "default": False,
                    }
                },
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        as_json = args.get("as_json", False)

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        content = api.get_active_note(as_json)

        if as_json:
            return [
                TextContent(
                    type="text", text=json.dumps(content, indent=2, ensure_ascii=False)
                )
            ]
        else:
            return [TextContent(type="text", text=content)]


class ListCommandsToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_get_commands")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="List all available Obsidian commands from the command palette.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        commands = api.list_commands()

        # Format the commands for better readability
        commands_info = []
        if commands and "commands" in commands:
            for cmd in commands["commands"]:
                cmd_id = cmd.get("id", "")
                cmd_name = cmd.get("name", "")
                commands_info.append(f"ID: {cmd_id} | Name: {cmd_name}")

        result = (
            "\n".join(commands_info) if commands_info else "(no commands available)"
        )

        return [TextContent(type="text", text=result)]


class ExecuteCommandToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_execute_command")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Execute a specific Obsidian command by its ID. WARNING: Some commands may be destructive or change settings. Use with caution.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command_id": {
                        "type": "string",
                        "description": "The ID of the command to execute (use obsidian_get_commands to see available IDs)",
                    }
                },
                "required": ["command_id"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "command_id" not in args:
            raise RuntimeError("command_id argument required")

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        api.execute_command(args["command_id"])

        return [
            TextContent(
                type="text", text=f"Successfully executed command: {args['command_id']}"
            )
        ]


class OpenFileToolHandler(ToolHandler):
    def __init__(self):
        super().__init__("obsidian_open_file")

    def get_tool_description(self):
        return Tool(
            name=self.name,
            description="Open a file in Obsidian UI, optionally in a new leaf (tab/pane).",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Path to the file to open (relative to vault root)",
                    },
                    "new_leaf": {
                        "type": "boolean",
                        "description": "If true, opens in new tab/pane; if false, opens in current view (default: false)",
                        "default": False,
                    },
                },
                "required": ["filename"],
            },
        )

    def run_tool(
        self, args: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "filename" not in args:
            raise RuntimeError("filename argument required")

        filename = args["filename"]
        new_leaf = args.get("new_leaf", False)

        api = obsidian.Obsidian(api_key=api_key, host=obsidian_host)
        api.open_file(filename, new_leaf)

        return [
            TextContent(
                type="text",
                text=f"Successfully opened file: {filename} (new_leaf={new_leaf})",
            )
        ]
