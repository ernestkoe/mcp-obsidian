# PRD: Smarter Heading Patch

## Problem Statement

The current `patch_content` function relies on the Obsidian Local REST API's PATCH endpoint for inserting content at specific headings. This endpoint has known bugs:

1. **Unreliable heading targeting** - Inconsistent behavior with newlines
2. **Wiki link failures** - Headings containing `[[wikilinks]]` fail as targets
3. **Unpredictable insertion** - Content may be inserted in wrong locations

These issues make the `obsidian_patch_content` tool unreliable for the primary use case: appending content under specific headings in daily notes.

## Current Behavior

```
Client calls patch_content("file.md", "append", "heading", "Todos", "- [ ] New task")
    ↓
MCP server sends PATCH request to REST API
    ↓
REST API attempts to find heading and insert content
    ↓
❌ Buggy behavior - content may be misplaced or operation fails
```

The current code has a fallback for when headings don't exist (error 40080), which bypasses the PATCH endpoint by doing read→modify→write. This fallback works reliably but only triggers for missing headings.

## Proposed Solution

Bypass the REST API PATCH endpoint entirely for heading operations. Implement a read→parse→modify→write cycle on the MCP server side.

### New Behavior

```
Client calls patch_content("file.md", "append", "heading", "Todos", "- [ ] New task")
    ↓
MCP server GETs file content
    ↓
Parse heading structure (already implemented: _parse_heading_structure)
    ↓
Find target heading and its boundary (next same-level or higher heading)
    ↓
Insert content at correct position
    ↓
PUT entire modified file back
    ↓
✅ Reliable, predictable behavior
```

## Technical Design

### New Method: `_patch_heading_content`

Location: `obsidian.py`

```python
def _patch_heading_content(
    self,
    filepath: str,
    operation: str,  # "append" | "prepend" | "replace"
    target_heading: str,  # e.g., "Todos" or "Notes::Subsection"
    content: str,
) -> None:
    """Patch content at a heading using read-modify-write pattern."""
```

### Algorithm

1. **Read** file content via `get_file_contents`
2. **Parse** heading structure via `_parse_heading_structure`
3. **Find target** heading by matching text (support `::` nested syntax)
4. **Determine boundary** - next heading at same or higher level, or EOF
5. **Modify** content based on operation:
   - `append`: Insert before boundary
   - `prepend`: Insert immediately after heading line
   - `replace`: Replace everything between heading and boundary
6. **Write** via `put_content`

### Heading Boundary Detection

```markdown
## Todos           ← Target heading (level 2)
- [ ] Existing     ← Content belongs to Todos
### Subsection     ← Still belongs to Todos (level 3 > 2)
- [ ] Sub item
## Notes           ← Boundary (level 2 = target level)
```

The boundary is the next heading with level ≤ target level, or end of file.

### Edge Cases

| Case | Behavior |
|------|----------|
| Heading not found | Fall back to `_create_heading_and_append` (existing behavior) |
| Heading at EOF | Append to end of file |
| Nested heading `A::B` | Find `## A`, then `### B` within A's section |
| Multiple same headings | Use first match (document this limitation) |
| Heading with wiki links | Works - we parse the actual markdown, not use REST API |

## Changes to `patch_content`

Modify the existing `patch_content` method to:

1. For `target_type == "heading"`: Use new `_patch_heading_content`
2. For `target_type == "block"` or `"frontmatter"`: Keep using REST API PATCH (these work fine)

## Testing

### Unit Tests

1. `test_patch_heading_append` - Append content under existing heading
2. `test_patch_heading_prepend` - Prepend content under existing heading
3. `test_patch_heading_replace` - Replace heading content
4. `test_patch_heading_boundary_detection` - Verify correct boundary finding
5. `test_patch_heading_with_wikilinks` - Headings containing `[[links]]` work
6. `test_patch_heading_nested` - `Parent::Child` syntax works
7. `test_patch_heading_not_found` - Falls back to create heading
8. `test_patch_heading_at_eof` - Heading is last in file

### Integration Tests

Manual verification with real Obsidian vault:
- Append todo to daily note `## Todos` section
- Append note to `## Notes` section
- Handle headings with wiki links like `## [[Project Name]]`

## Success Criteria

1. `obsidian_patch_content` with `target_type: heading` works reliably
2. Wiki links in headings no longer cause failures
3. Content is inserted at correct position (not misplaced)
4. Existing tests continue to pass
5. No changes required to Obsidian Local REST API plugin

## Non-Goals

- Changing behavior of `block` or `frontmatter` target types
- Modifying the Obsidian Local REST API plugin
- Supporting multiple headings with same name (use first match)

## Rollout

1. Implement in feature branch
2. Run full test suite
3. Manual testing with real vault
4. Merge to main
5. Release new version
