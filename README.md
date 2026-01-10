# MCP server for Obsidian

MCP server providing tools to interact with Obsidian via the Local REST API community plugin.

> **Note**: This is a maintained fork of [MarkusPfundstein/mcp-obsidian](https://github.com/MarkusPfundstein/mcp-obsidian).

## Installation

### 1. Install the Obsidian Plugin

Install and enable the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) community plugin in Obsidian. Copy the API key from the plugin settings.

### 2. Add to Your MCP Client

Add this server to your MCP client configuration. Examples for common clients:

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uvx",
      "args": ["mcp-obsidian-ek"],
      "env": {
        "OBSIDIAN_API_KEY": "<your_api_key_here>"
      }
    }
  }
}
```

**Claude Code** (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uvx",
      "args": ["mcp-obsidian-ek"],
      "env": {
        "OBSIDIAN_API_KEY": "<your_api_key_here>"
      }
    }
  }
}
```

> **Tip**: If `uvx` isn't found, use `which uvx` to get the full path and use that instead.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OBSIDIAN_API_KEY` | Yes | — | API key from Local REST API plugin |
| `OBSIDIAN_HOST` | No | `127.0.0.1` | Obsidian host address |
| `OBSIDIAN_PORT` | No | `27124` | Obsidian REST API port |

## Requirements

| Obsidian Plugin | Required | Notes |
|-----------------|----------|-------|
| [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) | Yes | v3.0+ recommended |
| [Periodic Notes](https://github.com/liamcain/obsidian-periodic-notes) | Optional | For weekly/monthly/quarterly/yearly (being removed in v1.0) |
| [Dataview](https://github.com/blacksmithgu/obsidian-dataview) | Optional | For `get_recent_changes` tool (being removed in v1.0) |

The core Daily Notes plugin (built into Obsidian) is sufficient for daily periodic notes.

> **v1.0 Goal**: Zero community plugin dependencies beyond Local REST API. All features will work with core Obsidian only.

## Tools

18 tools organized by functionality:

### File & Content Operations
| Tool | Description |
|------|-------------|
| `obsidian_list_files_in_vault` | List all files and directories in vault root |
| `obsidian_list_files_in_dir` | List files in a specific directory |
| `obsidian_get_file_contents` | Get content of a single file |
| `obsidian_batch_get_file_contents` | Get contents of multiple files |
| `obsidian_simple_search` | Text search across all files |
| `obsidian_complex_search` | JsonLogic queries with glob/regexp |
| `obsidian_append_content` | Append to a file |
| `obsidian_patch_content` | Insert content relative to heading/block/frontmatter |
| `obsidian_put_content` | Create or replace a file |
| `obsidian_delete_file` | Delete a file or directory |

### Active Note & Periodic Notes
| Tool | Description |
|------|-------------|
| `obsidian_get_active` | Get the currently open note |
| `obsidian_get_periodic_note` | Get daily/weekly/monthly/quarterly/yearly note |
| `obsidian_get_recent_periodic_notes` | Get recent periodic notes |

### Commands & UI
| Tool | Description |
|------|-------------|
| `obsidian_get_commands` | List available Obsidian commands |
| `obsidian_execute_command` | Execute a command by ID |
| `obsidian_open_file` | Open a file in Obsidian UI |

### Advanced
| Tool | Description |
|------|-------------|
| `obsidian_get_recent_changes` | Recently modified files (requires Dataview) |
| `obsidian_dataview_query` | Execute DQL queries (requires Dataview) |

## Example Prompts

**File operations:**
- "Get the contents of my last meeting note and summarize it"
- "Search for all files mentioning 'project deadlines'"
- "Create a new note called 'summary.md' with this content"

**Active note & periodic notes:**
- "What note do I have open? Summarize it"
- "Show me this week's weekly note"
- "What did I write in my daily notes last week?"

**Commands & UI:**
- "Open my project notes in a new tab"
- "Show me all available Obsidian commands"

## Advanced Features

### Path Encoding

Handles filenames with spaces, special characters, Unicode, and emojis:

```
Projects/2024 Q1/meeting notes.md
Área/configuração/São Paulo.md
Research (2024)/data #1 & analysis.md
Projects/documentation/notes.md
```

### Template-Aware Heading Insertion

When using `obsidian_patch_content` to insert content under a heading that doesn't exist, the heading is auto-created in the correct position based on your template structure.

**How it works:**
1. Checks the note's frontmatter for a `template:` field
2. Falls back to folder convention: `Daily Notes/*.md` uses `Templates/Daily Notes.md`
3. Inserts new headings in template order (not appended to end)

**Example:** If your template has `## Todos`, `## Notes`, `## Journal` and your note only has Todos and Journal, patching to "Notes" inserts it between them.

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `create_heading_if_missing` | `true` | Auto-create missing headings |
| `template_path` | auto | Explicit template path |
| `use_template` | `true` | Use template for positioning |

---

## Project Status

This fork is in active development (`v0.x.x`). The API may change before v1.0.0.

### Current (v0.6.x)
- 18 tools with ~30% reduced token footprint
- Template-aware heading insertion
- Robust path encoding
- Published to PyPI as `mcp-obsidian-ek`

### Planned for v1.0.0
- [x] Streamlined tool surface
- [x] Published to PyPI
- [ ] Stable API contract
- [ ] Comprehensive test coverage
- [ ] **No community plugin dependencies** - remove Dataview requirement, use file metadata for recent changes
- [ ] Periodic notes via folder conventions (no Periodic Notes plugin required)

### Breaking Changes from v0.4.x
These convenience tools were removed (use `get_active`/`get_periodic_note` + file operations instead):
- `obsidian_post_active`, `obsidian_put_active`, `obsidian_patch_active`, `obsidian_delete_active`
- `obsidian_post_periodic`, `obsidian_put_periodic`, `obsidian_patch_periodic`, `obsidian_delete_periodic`

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, architecture overview, and how to add new tools.

<a href="https://glama.ai/mcp/servers/3wko1bhuek"><img width="380" height="200" src="https://glama.ai/mcp/servers/3wko1bhuek/badge" alt="MCP server for Obsidian" /></a>
