# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- version list -->

## v0.6.1 (2026-01-03)

### Bug Fixes

- Disable OIDC attestations for PyPI publish
  ([`9a81efb`](https://github.com/ernestkoe/mcp-obsidian-ek/commit/9a81efba27585ef5c3b0e3ae61f224b16b8015ce))


## v0.6.0 (2026-01-03)

### Features

- Prepare for PyPI publishing as mcp-obsidian-ek
  ([#2](https://github.com/ernestkoe/mcp-obsidian-ek/pull/2),
  [`0391497`](https://github.com/ernestkoe/mcp-obsidian-ek/commit/039149781a83c74221466115774ecd4dd284a42d))

* refactor: Streamline tools to reduce token footprint by 30%

- Remove 8 redundant write tools for active/periodic notes (use filepath-based tools after GET
  instead) - Dedupe complex_search examples (remove from parameter schema) - Remove unused methods
  from obsidian.py client - Update tests to match reduced tool set

Tools: 26 → 18 | Tokens: ~3,514 → ~2,447 (-30%)

Removed tools: - obsidian_post_active, obsidian_put_active, obsidian_patch_active,
  obsidian_delete_active - obsidian_post_periodic, obsidian_put_periodic, obsidian_patch_periodic,
  obsidian_delete_periodic

Workflow: Use obsidian_get_active or obsidian_get_periodic_note (with as_json=true) to get the
  filepath, then use standard file tools (append_content, put_content, etc.)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

* feat: Prepare for PyPI publishing as mcp-obsidian-ek

- Rename package to mcp-obsidian-ek (upstream owns mcp-obsidian on PyPI) - Add dual CLI entry
  points: mcp-obsidian-ek (new) + mcp-obsidian (compat) - Add PyPI publish step to release workflow
  - Add v1.0.0 roadmap to README - Update all config examples with new package name - Remove
  inconsistent title annotations from tools - Simplify config examples (optional host/port)

* fix: Add hatch build config for renamed package

---------

Co-authored-by: Claude Opus 4.5 <noreply@anthropic.com>


## v0.5.0 (2026-01-03)

### Features

- Add template-aware heading auto-creation for patch_content
  ([`88a9fea`](https://github.com/ernestkoe/mcp-obsidian/commit/88a9fea15fcee5b11dfb0cc3ad974a74d522229a))

- Auto-create missing headings when patching (create_heading_if_missing) - Detect templates from
  frontmatter or folder conventions - Position new headings based on template structure
  (use_template) - Add explicit template_path parameter for custom templates - Add tests for new
  functionality

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>


## v0.4.0 (2025-12-31)

### Features

- Add 'limit' of contexts to return in simple search
  ([`aa3e962`](https://github.com/ernestkoe/mcp-obsidian/commit/aa3e962b658e80802302aa9041ad8b907b24f856))


## v0.3.1 (2025-12-29)

### Bug Fixes

- Update .atlas manifest with correct repo URL
  ([`06b771a`](https://github.com/ernestkoe/mcp-obsidian/commit/06b771a767f7e75b674ea48d14626152b77efaa3))

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>


## v0.3.0 (2025-12-29)

### Bug Fixes

- Remove build_command from semantic-release config
  ([`ec40b32`](https://github.com/ernestkoe/mcp-obsidian/commit/ec40b32eb0bcaaca46ad48ce042122401e8feab1))

The semantic-release action runs in its own container without uv. Since we're not publishing to
  PyPI, we don't need to build.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

- Remove PyPI publishing from release workflow
  ([`203568e`](https://github.com/ernestkoe/mcp-obsidian/commit/203568eb5f9b272196e11fc0598b7fb6a5ed4ff0))

Not publishing to PyPI, only GitHub Releases.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

### Features

- Add semantic-release for automated versioning
  ([`63d7c01`](https://github.com/ernestkoe/mcp-obsidian/commit/63d7c01252d8b655da6e5de8eda76830b5950969))

- Add python-semantic-release to dev dependencies - Configure semantic-release in pyproject.toml -
  Create GitHub Actions release workflow with PyPI publishing - Add CHANGELOG.md with version
  history - Add __version__ to package __init__.py - Update CI to only run on pull requests (release
  workflow handles main)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>


## [0.2.1] - 2025-12-29

### Added
- Test suite with 70 tests covering Obsidian client and all tool handlers
- GitHub Actions CI workflow (Python 3.11-3.13, pyright, pytest)
- Semantic release automation for versioning
- Tool annotations (readOnlyHint, destructiveHint) for 5 tools
- `obsidian_dataview_query` tool for executing Dataview DQL queries
- Windows UTF-8 fix for MCP STDIO communication
- Character encoding fix (`ensure_ascii=False`) for non-ASCII content

### Fixed
- JSONDecodeError on non-JSON HTTP error responses
- Code formatting with ruff (consistent 4-space indentation)
- Removed duplicate API key validation

### Changed
- Upgraded mcp dependency from 1.1.0 to 1.24.0+
- Added ruff and python-semantic-release to dev dependencies

## [0.2.0] - 2024-12-XX (Original Project)

### Added
- Active note operations (get, post, put, patch, delete)
- Periodic notes management (daily, weekly, monthly, quarterly, yearly)
- Command execution tools
- Recent periodic notes and recent changes tools
- Path encoding for Unicode filenames, spaces, emojis

## [0.1.0] - 2024-XX-XX (Original Project)

### Added
- Initial MCP server implementation
- Basic vault file operations (list, get, search, append, patch, put, delete)
- Obsidian Local REST API integration
