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
