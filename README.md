# MCP server for Obsidian

MCP server providing tools to interact with Obsidian via the Local REST API community plugin, including active note operations, periodic notes management, and command execution.

> **Note**: This is a maintained fork of [MarkusPfundstein/mcp-obsidian](https://github.com/MarkusPfundstein/mcp-obsidian).

## Roadmap to v1.0.0

This fork is in active development (`v0.x.x`). The `v1.0.0` release will mark the first stable API. Expect things to be in flux. I am adding tool coverage but will attempt to streamline them to keep our context footprint as small as possible. Currently, I am just exposing REST endpoints I think might be useful as tools, but expect some of these to change.

### Current Status (v0.4.x)
- 26 tools covering file operations, active notes, periodic notes, and commands
- Template-aware heading insertion
- Robust path encoding for special characters and Unicode

### Planned for v1.0.0
- [ ] **Streamlined tool surface** — Reduce token footprint by consolidating convenience wrappers (e.g., `patch_active` → `get_active` + `patch_content`)
- [ ] **Stable API contract** — Tool names, parameters, and behaviors locked for backwards compatibility
- [ ] **Comprehensive test coverage** — All tools tested with CI
- [ ] **Published to PyPI** — Available via `uvx mcp-obsidian-ek` with version pinning

### Breaking Changes Expected
The v1.0.0 release will likely remove convenience tools that can be accomplished with two-step workflows:
- `obsidian_post_active`, `obsidian_put_active`, `obsidian_patch_active`, `obsidian_delete_active`
- `obsidian_post_periodic`, `obsidian_put_periodic`, `obsidian_patch_periodic`, `obsidian_delete_periodic`

These operations will still be possible using `get_active`/`get_periodic_note` followed by the corresponding file operation.

<a href="https://glama.ai/mcp/servers/3wko1bhuek"><img width="380" height="200" src="https://glama.ai/mcp/servers/3wko1bhuek/badge" alt="server for Obsidian MCP server" /></a>

## Requirements

### Obsidian Plugins

| Plugin | Required | Notes |
|--------|----------|-------|
| [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) | Yes | v3.0+ recommended |
| [Periodic Notes](https://github.com/liamcain/obsidian-periodic-notes) | Optional | Required for weekly/monthly/quarterly/yearly notes |
| [Dataview](https://github.com/blacksmithgu/obsidian-dataview) | Optional | Required for `get_recent_changes` tool |

The core Daily Notes plugin (built into Obsidian) is sufficient for daily periodic notes.

## Tools

The server implements 26 tools to interact with Obsidian, organized by functionality:

#### File & Content Operations
- obsidian_list_files_in_vault: Lists all files and directories in the root directory of your Obsidian vault
- obsidian_list_files_in_dir: Lists all files and directories in a specific Obsidian directory
- obsidian_get_file_contents: Return the content of a single file in your vault
- obsidian_batch_get_file_contents: Return the contents of multiple files in your vault, concatenated with headers
- obsidian_simple_search: Search for documents matching a specified text query across all files in the vault
- obsidian_complex_search: Complex search for documents using JsonLogic queries with glob and regexp support
- obsidian_patch_content: Insert content into an existing note relative to a heading, block reference, or frontmatter field. Automatically creates missing headings with template-aware positioning
- obsidian_append_content: Append content to a new or existing file in the vault
- obsidian_put_content: Create a new file or update the content of an existing file in your vault
- obsidian_delete_file: Delete a file or directory from your vault

#### Active Note Operations
- obsidian_get_active: Get content of the currently active note in Obsidian
- obsidian_post_active: Append content to the currently active note
- obsidian_put_active: Replace entire content of the currently active note
- obsidian_patch_active: Insert/replace content in active note relative to a heading, block reference, or frontmatter field
- obsidian_delete_active: Delete the currently active note

#### Periodic Notes Management
- obsidian_get_periodic_note: Get current periodic note for specified period (daily/weekly/monthly/quarterly/yearly)
- obsidian_post_periodic: Append content to the current periodic note
- obsidian_put_periodic: Replace entire content of the current periodic note
- obsidian_patch_periodic: Insert/replace content in periodic note relative to a heading, block reference, or frontmatter field
- obsidian_delete_periodic: Delete the current periodic note

#### Commands & UI Control
- obsidian_get_commands: List all available Obsidian commands from the command palette
- obsidian_execute_command: Execute a specific Obsidian command by its ID
- obsidian_open_file: Open a file in Obsidian UI, optionally in a new tab/pane

#### Advanced Features
- obsidian_get_recent_periodic_notes: Get most recent periodic notes for specified period type
- obsidian_get_recent_changes: Get recently modified files in the vault
- obsidian_dataview_query: Execute a Dataview DQL query against the vault (requires Dataview plugin)

### Example prompts

It's good to first instruct Claude to use Obsidian. Then it will always call the tool.

#### File & Search Operations
- Get the contents of the last architecture call note and summarize them
- Search for all files where Azure CosmosDb is mentioned and quickly explain to me the context in which it is mentioned
- Summarize the last meeting notes and put them into a new note 'summary meeting.md'. Add an introduction so that I can send it via email
- Find all notes containing project deadlines and create a consolidated timeline

#### Active Note Operations  
- Add this meeting summary to the note I currently have open
- Replace the active note content with the updated version I'm about to provide
- Insert a new "Action Items" section under the "Meeting Notes" heading in my active document
- Append today's accomplishments to whatever note I have open right now

#### Periodic Notes Management
- Add today's tasks to my daily note
- Get the content of this week's weekly note and summarize the key points
- Create a monthly review section in my monthly periodic note with this quarter's achievements
- Append my standup update to today's daily note
- Show me what's in my quarterly note and help me plan the next quarter

#### Command Execution & UI Control
- Open my project notes in a new tab so I can reference them
- Execute the 'Toggle Reading View' command to switch the current view
- Show me all available Obsidian commands so I can see what's possible
- Open the file 'Projects/2024/planning.md' in a new pane
- Run the command to create a new note from my meeting template

## Path Encoding & Filename Support

The server includes robust path encoding that handles filenames with spaces, special characters, Unicode, and emojis. All file operations work seamlessly with complex filenames.

### Supported Filename Types

- **Spaces**: `Projects/2024 Q1/meeting notes.md`
- **Unicode characters**: `Área/configuração/São Paulo.md`  
- **Special characters**: `Research (2024)/data #1 & analysis + results.md`
- **Emojis**: `Projects 🚀/📘 documentation/notes ⭐.md`
- **Mixed types**: `Área (Special) & More + [Data] = Value #1 🚀.md`

### Technical Features

- **Idempotent**: Prevents double-encoding of already encoded paths
- **Unicode normalization**: Normalizes to NFC for cross-platform consistency
- **RFC 3986 compliant**: Preserves safe characters (-_.~) while encoding others  
- **Directory structure preservation**: Maintains "/" separators and trailing "/" slashes
- **Backward compatible**: No changes to existing simple filename behavior

### Example Operations

```python
# All these filename types work with any operation:
obsidian_get_file_contents("Projects/Meeting Notes 📝.md")
obsidian_append_content("Área/configuração.md", "New content")
obsidian_list_files_in_dir("Special (Folder) & More")
obsidian_patch_content("Research #1/data + analysis.md", ...)
obsidian_list_files_in_dir("Reports/2024/")
```

## Template-Aware Heading Insertion

When using `obsidian_patch_content` (or similar patch operations) to insert content under a heading that doesn't exist, the server automatically creates the heading. By default, it uses template-aware positioning to maintain consistent document structure.

### How It Works

1. **Auto-create missing headings**: When you patch content to a heading that doesn't exist, the heading is created automatically (enabled by default, can be disabled with `create_heading_if_missing: false`)

2. **Template detection**: The server looks for a template to determine where the new heading should be inserted:
   - First checks the note's frontmatter for a `template:` field
   - Falls back to folder convention: `Daily Notes/*.md` → `Templates/Daily Notes.md`

3. **Position-aware insertion**: If a template is found, the new heading is inserted in the correct position based on the template's heading order, rather than appended to the end

### Example

If your template (`Templates/Daily Notes.md`) has:
```markdown
## Todos
## Notes
## Journal
```

And your daily note only has `## Todos` and `## Journal`, patching content to `Notes` will insert it between them—not at the end.

### Frontmatter Template Reference

Add a `template:` field to your note's frontmatter to specify which template defines the heading structure:

```yaml
---
template: Daily Note.md
---
```

The server will look for `Templates/Daily Note.md` (or the full path if provided).

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `create_heading_if_missing` | `true` | Create the heading if it doesn't exist |
| `template_path` | auto-detect | Explicit path to template file |
| `use_template` | `true` | Use template for heading positioning |

### Disabling Template Positioning

To always append new headings to the end (original behavior), set `use_template: false`:

```python
obsidian_patch_content(
    filepath="Daily Notes/2024-01-15.md",
    operation="append",
    target_type="heading",
    target="New Section",
    content="Content here",
    use_template=False  # Always append to end
)
```

## Configuration

### Obsidian REST API Key

There are two ways to configure the environment with the Obsidian REST API Key. 

1. Add to server config (preferred)

```json
{
  "mcp-obsidian-ek": {
    "command": "uvx",
    "args": [
      "mcp-obsidian-ek"
    ],
    "env": {
      "OBSIDIAN_API_KEY": "<your_api_key_here>"
    }
  }
}
```

Note: `OBSIDIAN_HOST` (default: 127.0.0.1) and `OBSIDIAN_PORT` (default: 27124) are optional.

Sometimes Claude has issues detecting the location of uvx. You can use `which uvx` to find and paste the full path in the config.

2. Create a `.env` file in the working directory with the following required variables:

```
OBSIDIAN_API_KEY=your_api_key_here
OBSIDIAN_HOST=your_obsidian_host
OBSIDIAN_PORT=your_obsidian_port
```

Note:
- You can find the API key in the Obsidian plugin config
- Default port is 27124 if not specified
- Default host is 127.0.0.1 if not specified

## Quickstart

### Install

#### Obsidian REST API

You need the Obsidian REST API community plugin running: https://github.com/coddingtonbear/obsidian-local-rest-api

Install and enable it in the settings and copy the api key.

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development (from local repo)</summary>

```json
{
  "mcpServers": {
    "mcp-obsidian-ek": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-obsidian",
        "run",
        "mcp-obsidian-ek"
      ],
      "env": {
        "OBSIDIAN_API_KEY": "<your_api_key_here>"
      }
    }
  }
}
```
</details>

<details>
  <summary>Published (from PyPI)</summary>

```json
{
  "mcpServers": {
    "mcp-obsidian-ek": {
      "command": "uvx",
      "args": [
        "mcp-obsidian-ek"
      ],
      "env": {
        "OBSIDIAN_API_KEY": "<your_api_key_here>"
      }
    }
  }
}
```
</details>

## Development

### Building

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp-obsidian run mcp-obsidian-ek
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.

You can also watch the server logs with this command:

```bash
tail -n 20 -f ~/Library/Logs/Claude/mcp-server-mcp-obsidian-ek.log
```
