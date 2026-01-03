import pytest
import responses
from mcp_obsidian.obsidian import Obsidian


class TestObsidianClient:
    """Tests for the Obsidian REST API client."""

    def test_get_base_url_https(self, api_key):
        client = Obsidian(api_key=api_key, protocol="https", host="127.0.0.1", port=27124)
        assert client.get_base_url() == "https://127.0.0.1:27124"

    def test_get_base_url_http(self, api_key):
        client = Obsidian(api_key=api_key, protocol="http", host="localhost", port=8080)
        assert client.get_base_url() == "http://localhost:8080"

    def test_protocol_defaults_to_https(self, api_key):
        client = Obsidian(api_key=api_key, protocol="invalid", host="127.0.0.1", port=27124)
        assert client.protocol == "https"

    def test_list_files_in_vault(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/",
            json={"files": ["note1.md", "note2.md", "folder/"]},
            status=200,
        )

        result = obsidian_client.list_files_in_vault()
        assert result == ["note1.md", "note2.md", "folder/"]

    def test_list_files_in_dir(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/folder/",
            json={"files": ["file1.md", "file2.md"]},
            status=200,
        )

        result = obsidian_client.list_files_in_dir("folder")
        assert result == ["file1.md", "file2.md"]

    def test_get_file_contents(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/note.md",
            body="# My Note\n\nContent here",
            status=200,
        )

        result = obsidian_client.get_file_contents("note.md")
        assert result == "# My Note\n\nContent here"

    def test_get_batch_file_contents(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/note1.md",
            body="Content 1",
            status=200,
        )
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/note2.md",
            body="Content 2",
            status=200,
        )

        result = obsidian_client.get_batch_file_contents(["note1.md", "note2.md"])
        assert "# note1.md" in result
        assert "Content 1" in result
        assert "# note2.md" in result
        assert "Content 2" in result

    def test_get_batch_file_contents_with_error(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/note1.md",
            body="Content 1",
            status=200,
        )
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/missing.md",
            json={"errorCode": 40401, "message": "File not found"},
            status=404,
        )

        result = obsidian_client.get_batch_file_contents(["note1.md", "missing.md"])
        assert "Content 1" in result
        assert "Error reading file" in result

    def test_search(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.POST,
            f"{base_url}/search/simple/",
            json=[
                {
                    "filename": "note.md",
                    "score": 10,
                    "matches": [{"context": "test content", "match": {"start": 0, "end": 4}}],
                }
            ],
            status=200,
        )

        result = obsidian_client.search("test")
        assert len(result) == 1
        assert result[0]["filename"] == "note.md"

    def test_append_content(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.POST,
            f"{base_url}/vault/note.md",
            status=204,
        )

        result = obsidian_client.append_content("note.md", "New content")
        assert result is None

    def test_put_content(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.PUT,
            f"{base_url}/vault/note.md",
            status=204,
        )

        result = obsidian_client.put_content("note.md", "Full content")
        assert result is None

    def test_patch_content(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.PATCH,
            f"{base_url}/vault/note.md",
            status=200,
        )

        result = obsidian_client.patch_content(
            "note.md", "append", "heading", "Section 1", "New text"
        )
        assert result is None

    def test_patch_content_creates_missing_heading(
        self, obsidian_client, base_url, mock_responses
    ):
        """Test that patch_content creates a missing heading by default."""
        # First call fails with invalid-target error
        mock_responses.add(
            responses.PATCH,
            f"{base_url}/vault/note.md",
            json={"errorCode": 40080, "message": "invalid-target"},
            status=400,
        )
        # Then we read the file
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/note.md",
            body="# My Note\n\nExisting content",
            status=200,
        )
        # And write with the new heading
        mock_responses.add(
            responses.PUT,
            f"{base_url}/vault/note.md",
            status=200,
        )

        result = obsidian_client.patch_content(
            "note.md", "append", "heading", "New Section", "\nNew text"
        )
        assert result is None

        # Verify the PUT was called with the heading added
        put_call = mock_responses.calls[-1]
        assert "## New Section" in put_call.request.body
        assert "New text" in put_call.request.body

    def test_patch_content_does_not_create_heading_when_disabled(
        self, obsidian_client, base_url, mock_responses
    ):
        """Test that patch_content raises error when create_heading_if_missing=False."""
        mock_responses.add(
            responses.PATCH,
            f"{base_url}/vault/note.md",
            json={"errorCode": 40080, "message": "invalid-target"},
            status=400,
        )

        with pytest.raises(Exception, match="40080"):
            obsidian_client.patch_content(
                "note.md",
                "append",
                "heading",
                "Missing Section",
                "New text",
                create_heading_if_missing=False,
            )

    def test_patch_content_nested_heading_level(
        self, obsidian_client, base_url, mock_responses
    ):
        """Test that nested headings (e.g., 'Parent::Child') get proper heading level."""
        mock_responses.add(
            responses.PATCH,
            f"{base_url}/vault/note.md",
            json={"errorCode": 40080, "message": "invalid-target"},
            status=400,
        )
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/note.md",
            body="# My Note\n\nContent",
            status=200,
        )
        mock_responses.add(
            responses.PUT,
            f"{base_url}/vault/note.md",
            status=200,
        )

        result = obsidian_client.patch_content(
            "note.md", "append", "heading", "Parent::Child", "\nNested content"
        )
        assert result is None

        # Nested heading should be h3 (### Child)
        put_call = mock_responses.calls[-1]
        assert "### Child" in put_call.request.body

    def test_parse_frontmatter(self, obsidian_client):
        """Test parsing YAML frontmatter from markdown."""
        content = """---
template: Daily Note.md
title: My Note
---

# Content here
"""
        result = obsidian_client._parse_frontmatter(content)
        assert result["template"] == "Daily Note.md"
        assert result["title"] == "My Note"

    def test_parse_frontmatter_empty(self, obsidian_client):
        """Test parsing content without frontmatter."""
        content = "# Just a heading\n\nNo frontmatter here"
        result = obsidian_client._parse_frontmatter(content)
        assert result == {}

    def test_parse_heading_structure(self, obsidian_client):
        """Test extracting heading hierarchy from markdown."""
        content = """# Title

## Section A
Content here

## Section B

### Subsection B1
More content

## Section C
"""
        result = obsidian_client._parse_heading_structure(content)
        assert len(result) == 5
        assert result[0] == (1, "Title", 0)
        assert result[1] == (2, "Section A", 2)
        assert result[2] == (2, "Section B", 5)
        assert result[3] == (3, "Subsection B1", 7)
        assert result[4] == (2, "Section C", 10)

    def test_find_insertion_point_basic(self, obsidian_client):
        """Test finding insertion point based on template order."""
        # Template has: Section A, Section B, Section C
        template_headings = [
            (2, "Section A", 0),
            (2, "Section B", 2),
            (2, "Section C", 4),
        ]
        # Current file has: Section A, Section C (missing B)
        current_headings = [
            (2, "Section A", 0),
            (2, "Section C", 3),
        ]
        # Section B should be inserted before Section C (line 3)
        result = obsidian_client._find_insertion_point(
            current_headings, template_headings, "Section B", 2
        )
        assert result == 3

    def test_find_insertion_point_not_in_template(self, obsidian_client):
        """Test that headings not in template return None (append to end)."""
        template_headings = [(2, "Section A", 0), (2, "Section B", 2)]
        current_headings = [(2, "Section A", 0)]
        result = obsidian_client._find_insertion_point(
            current_headings, template_headings, "Unknown Section", 2
        )
        assert result is None

    def test_get_template_from_frontmatter(
        self, obsidian_client, base_url, mock_responses
    ):
        """Test getting template path from frontmatter."""
        content = """---
template: Daily Note.md
---

# Content
"""
        result = obsidian_client._get_template_for_file("Daily Notes/2024-01-01.md", content)
        assert result == "Templates/Daily Note.md"

    def test_get_template_from_folder_convention(
        self, obsidian_client, base_url, mock_responses
    ):
        """Test folder-based template detection."""
        # Mock the template file exists
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/Templates/Daily%20Notes.md",
            body="# Template\n\n## Todos\n\n## Notes",
            status=200,
        )

        result = obsidian_client._get_template_for_file(
            "Daily Notes/2024-01-01.md", "# Content without frontmatter"
        )
        assert result == "Templates/Daily Notes.md"

    def test_patch_content_uses_template_for_positioning(
        self, obsidian_client, base_url, mock_responses
    ):
        """Test that missing headings are inserted at template-defined position."""
        # First patch fails - heading doesn't exist
        mock_responses.add(
            responses.PATCH,
            f"{base_url}/vault/Daily%20Notes/2024-01-01.md",
            json={"errorCode": 40080, "message": "invalid-target"},
            status=400,
        )
        # Read current file (has Section A and Section C, missing B)
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/Daily%20Notes/2024-01-01.md",
            body="---\ntemplate: Daily Note.md\n---\n\n# Daily Note\n\n## Section A\nContent A\n\n## Section C\nContent C",
            status=200,
        )
        # Read template
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/Templates/Daily%20Note.md",
            body="# Daily Note\n\n## Section A\n\n## Section B\n\n## Section C",
            status=200,
        )
        # Write updated file
        mock_responses.add(
            responses.PUT,
            f"{base_url}/vault/Daily%20Notes/2024-01-01.md",
            status=200,
        )

        result = obsidian_client.patch_content(
            "Daily Notes/2024-01-01.md",
            "append",
            "heading",
            "Section B",
            "\nNew content",
            use_template=True,
        )
        assert result is None

        # Verify the PUT was called and Section B was inserted
        put_call = mock_responses.calls[-1]
        assert "## Section B" in put_call.request.body

    def test_patch_content_template_disabled(
        self, obsidian_client, base_url, mock_responses
    ):
        """Test that template is not used when use_template=False."""
        mock_responses.add(
            responses.PATCH,
            f"{base_url}/vault/note.md",
            json={"errorCode": 40080, "message": "invalid-target"},
            status=400,
        )
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/note.md",
            body="# Note\n\n## Existing",
            status=200,
        )
        mock_responses.add(
            responses.PUT,
            f"{base_url}/vault/note.md",
            status=200,
        )

        result = obsidian_client.patch_content(
            "note.md",
            "append",
            "heading",
            "New Section",
            "\nContent",
            use_template=False,
        )
        assert result is None

        # Verify heading was appended to end (not template-positioned)
        put_call = mock_responses.calls[-1]
        body = put_call.request.body
        # New section should be at the end after existing content
        assert body.endswith("## New Section\nContent")

    def test_delete_file(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.DELETE,
            f"{base_url}/vault/note.md",
            status=204,
        )

        result = obsidian_client.delete_file("note.md")
        assert result is None

    def test_search_json(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.POST,
            f"{base_url}/search/",
            json=[{"filename": "note.md", "result": True}],
            status=200,
        )

        query = {"glob": ["*.md", {"var": "path"}]}
        result = obsidian_client.search_json(query)
        assert len(result) == 1

    def test_get_periodic_note(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.GET,
            f"{base_url}/periodic/daily/",
            body="# Daily Note\n\nToday's content",
            status=200,
        )

        result = obsidian_client.get_periodic_note("daily")
        assert "Daily Note" in result

    def test_get_recent_periodic_notes(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.GET,
            f"{base_url}/periodic/daily/recent",
            json=[{"path": "daily/2024-01-01.md"}, {"path": "daily/2024-01-02.md"}],
            status=200,
        )

        result = obsidian_client.get_recent_periodic_notes("daily", limit=2)
        assert len(result) == 2

    def test_get_recent_changes(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.POST,
            f"{base_url}/search/",
            json=[{"filename": "recent.md", "result": {"file.mtime": "2024-01-01"}}],
            status=200,
        )

        result = obsidian_client.get_recent_changes(limit=5, days=30)
        assert len(result) == 1


class TestObsidianErrorHandling:
    """Tests for error handling in the Obsidian client."""

    def test_http_error_with_json_response(self, obsidian_client, base_url, mock_responses):
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/missing.md",
            json={"errorCode": 40401, "message": "File not found"},
            status=404,
        )

        with pytest.raises(Exception) as exc_info:
            obsidian_client.get_file_contents("missing.md")

        assert "40401" in str(exc_info.value)
        assert "File not found" in str(exc_info.value)

    def test_http_error_without_json_response(self, obsidian_client, base_url, mock_responses):
        """Test that non-JSON error responses are handled gracefully."""
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/error.md",
            body="Internal Server Error",
            status=500,
        )

        with pytest.raises(Exception) as exc_info:
            obsidian_client.get_file_contents("error.md")

        assert "HTTP 500" in str(exc_info.value)
        assert "Internal Server Error" in str(exc_info.value)

    def test_connection_error(self, api_key):
        client = Obsidian(api_key=api_key, host="nonexistent.host", port=9999)

        with pytest.raises(Exception) as exc_info:
            client.list_files_in_vault()

        assert "Request failed" in str(exc_info.value)
