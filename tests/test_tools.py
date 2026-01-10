import pytest
import responses
from mcp.types import TextContent

from mcp_obsidian import tools


class TestToolHandlerBase:
    """Tests for the ToolHandler base class and registration."""

    def test_tool_handler_has_name(self):
        handler = tools.ListFilesInVaultToolHandler()
        assert handler.name == "obsidian_list_files_in_vault"

    def test_tool_description_returns_tool(self):
        handler = tools.ListFilesInVaultToolHandler()
        tool = handler.get_tool_description()
        assert tool.name == "obsidian_list_files_in_vault"
        assert "vault" in tool.description.lower()


class TestListFilesInVaultToolHandler:
    """Tests for the list files in vault tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/",
            json={"files": ["note1.md", "note2.md", "folder/"]},
            status=200,
        )

        handler = tools.ListFilesInVaultToolHandler()
        result = handler.run_tool({})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "note1.md" in result[0].text


class TestListFilesInDirToolHandler:
    """Tests for the list files in directory tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/myfolder/",
            json={"files": ["file1.md", "file2.md"]},
            status=200,
        )

        handler = tools.ListFilesInDirToolHandler()
        result = handler.run_tool({"dirpath": "myfolder"})

        assert len(result) == 1
        assert "file1.md" in result[0].text

    def test_missing_dirpath_raises_error(self):
        handler = tools.ListFilesInDirToolHandler()

        with pytest.raises(RuntimeError, match="dirpath"):
            handler.run_tool({})


class TestGetFileContentsToolHandler:
    """Tests for the get file contents tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/note.md",
            body="# My Note\n\nContent here",
            status=200,
        )

        handler = tools.GetFileContentsToolHandler()
        result = handler.run_tool({"filepath": "note.md"})

        assert len(result) == 1
        assert "My Note" in result[0].text

    def test_missing_filepath_raises_error(self):
        handler = tools.GetFileContentsToolHandler()

        with pytest.raises(RuntimeError, match="filepath"):
            handler.run_tool({})


class TestSearchToolHandler:
    """Tests for the simple search tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.POST,
            f"{base_url}/search/simple/",
            json=[
                {
                    "filename": "note.md",
                    "score": 10,
                    "matches": [{"context": "test query here", "match": {"start": 5, "end": 10}}],
                }
            ],
            status=200,
        )

        handler = tools.SearchToolHandler()
        result = handler.run_tool({"query": "query"})

        assert len(result) == 1
        assert "note.md" in result[0].text
        assert "test query here" in result[0].text

    def test_missing_query_raises_error(self):
        handler = tools.SearchToolHandler()

        with pytest.raises(RuntimeError, match="query"):
            handler.run_tool({})


class TestAppendContentToolHandler:
    """Tests for the append content tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.POST,
            f"{base_url}/vault/note.md",
            status=204,
        )

        handler = tools.AppendContentToolHandler()
        result = handler.run_tool({"filepath": "note.md", "content": "New content"})

        assert len(result) == 1
        assert "Successfully" in result[0].text

    def test_missing_args_raises_error(self):
        handler = tools.AppendContentToolHandler()

        with pytest.raises(RuntimeError):
            handler.run_tool({"filepath": "note.md"})  # missing content

        with pytest.raises(RuntimeError):
            handler.run_tool({"content": "text"})  # missing filepath


class TestPutContentToolHandler:
    """Tests for the put content tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.PUT,
            f"{base_url}/vault/note.md",
            status=204,
        )

        handler = tools.PutContentToolHandler()
        result = handler.run_tool({"filepath": "note.md", "content": "Full content"})

        assert len(result) == 1
        assert "Successfully" in result[0].text


class TestDeleteFileToolHandler:
    """Tests for the delete file tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.DELETE,
            f"{base_url}/vault/note.md",
            status=204,
        )

        handler = tools.DeleteFileToolHandler()
        result = handler.run_tool({"filepath": "note.md", "confirm": True})

        assert len(result) == 1
        assert "Successfully deleted" in result[0].text

    def test_confirm_required(self):
        handler = tools.DeleteFileToolHandler()

        with pytest.raises(RuntimeError, match="confirm"):
            handler.run_tool({"filepath": "note.md", "confirm": False})

        with pytest.raises(RuntimeError, match="confirm"):
            handler.run_tool({"filepath": "note.md"})


class TestPatchContentToolHandler:
    """Tests for the patch content tool."""

    def test_run_tool(self, mock_responses, base_url):
        # New smarter patch uses GET+PUT for heading operations
        mock_responses.add(
            responses.GET,
            f"{base_url}/vault/note.md",
            body="# Section 1\n\nExisting content\n",
            status=200,
        )
        mock_responses.add(
            responses.PUT,
            f"{base_url}/vault/note.md",
            status=204,
        )

        handler = tools.PatchContentToolHandler()
        result = handler.run_tool({
            "filepath": "note.md",
            "operation": "append",
            "target_type": "heading",
            "target": "Section 1",
            "content": "New text",
        })

        assert len(result) == 1
        assert "Successfully" in result[0].text


class TestComplexSearchToolHandler:
    """Tests for the complex search tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.POST,
            f"{base_url}/search/",
            json=[{"filename": "note.md", "result": True}],
            status=200,
        )

        handler = tools.ComplexSearchToolHandler()
        result = handler.run_tool({"query": {"glob": ["*.md", {"var": "path"}]}})

        assert len(result) == 1
        assert "note.md" in result[0].text


class TestBatchGetFileContentsToolHandler:
    """Tests for the batch get file contents tool."""

    def test_run_tool(self, mock_responses, base_url):
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

        handler = tools.BatchGetFileContentsToolHandler()
        result = handler.run_tool({"filepaths": ["note1.md", "note2.md"]})

        assert len(result) == 1
        assert "Content 1" in result[0].text
        assert "Content 2" in result[0].text


class TestPeriodicNotesToolHandler:
    """Tests for the periodic notes tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.GET,
            f"{base_url}/periodic/daily/",
            body="# Daily Note",
            status=200,
        )

        handler = tools.PeriodicNotesToolHandler()
        result = handler.run_tool({"period": "daily"})

        assert len(result) == 1
        assert "Daily Note" in result[0].text

    def test_invalid_period_raises_error(self):
        handler = tools.PeriodicNotesToolHandler()

        with pytest.raises(RuntimeError, match="Invalid period"):
            handler.run_tool({"period": "hourly"})


class TestRecentPeriodicNotesToolHandler:
    """Tests for the recent periodic notes tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.GET,
            f"{base_url}/periodic/daily/recent",
            json=[{"path": "daily/2024-01-01.md"}],
            status=200,
        )

        handler = tools.RecentPeriodicNotesToolHandler()
        result = handler.run_tool({"period": "daily", "limit": 5})

        assert len(result) == 1
        assert "2024-01-01" in result[0].text


class TestRecentChangesToolHandler:
    """Tests for the recent changes tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.POST,
            f"{base_url}/search/",
            json=[{"filename": "recent.md", "result": {}}],
            status=200,
        )

        handler = tools.RecentChangesToolHandler()
        result = handler.run_tool({"limit": 10, "days": 30})

        assert len(result) == 1
        assert "recent.md" in result[0].text


class TestDataviewQueryToolHandler:
    """Tests for the Dataview query tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.POST,
            f"{base_url}/search/",
            json=[{"filename": "note.md", "title": "My Note"}],
            status=200,
        )

        handler = tools.DataviewQueryToolHandler()
        result = handler.run_tool({"query": "TABLE title FROM #tag"})

        assert len(result) == 1
        assert "My Note" in result[0].text

    def test_missing_query_raises_error(self):
        handler = tools.DataviewQueryToolHandler()

        with pytest.raises(RuntimeError, match="query"):
            handler.run_tool({})


# ============================================================================
# Active Note Tools (from PR #77)
# ============================================================================

class TestGetActiveNoteToolHandler:
    """Tests for the get active note tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.GET,
            f"{base_url}/active/",
            body="# Active Note Content",
            status=200,
        )

        handler = tools.GetActiveNoteToolHandler()
        result = handler.run_tool({})

        assert len(result) == 1
        assert "Active Note Content" in result[0].text

    def test_run_tool_as_json(self, mock_responses, base_url):
        mock_responses.add(
            responses.GET,
            f"{base_url}/active/",
            json={"content": "# Active Note", "path": "note.md"},
            status=200,
        )

        handler = tools.GetActiveNoteToolHandler()
        result = handler.run_tool({"as_json": True})

        assert len(result) == 1
        assert "note.md" in result[0].text


# ============================================================================
# Commands & UI Control Tools (from PR #77)
# ============================================================================

class TestListCommandsToolHandler:
    """Tests for the list commands tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.GET,
            f"{base_url}/commands/",
            json={
                "commands": [
                    {"id": "app:open-vault", "name": "Open another vault"},
                    {"id": "editor:toggle-source", "name": "Toggle source mode"},
                ]
            },
            status=200,
        )

        handler = tools.ListCommandsToolHandler()
        result = handler.run_tool({})

        assert len(result) == 1
        assert "app:open-vault" in result[0].text
        assert "Open another vault" in result[0].text

    def test_empty_commands(self, mock_responses, base_url):
        mock_responses.add(
            responses.GET,
            f"{base_url}/commands/",
            json={"commands": []},
            status=200,
        )

        handler = tools.ListCommandsToolHandler()
        result = handler.run_tool({})

        assert len(result) == 1
        assert "no commands" in result[0].text.lower()


class TestExecuteCommandToolHandler:
    """Tests for the execute command tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.POST,
            f"{base_url}/commands/editor%3Atoggle-source/",
            status=204,
        )

        handler = tools.ExecuteCommandToolHandler()
        result = handler.run_tool({"command_id": "editor:toggle-source"})

        assert len(result) == 1
        assert "Successfully" in result[0].text
        assert "editor:toggle-source" in result[0].text

    def test_missing_command_id_raises_error(self):
        handler = tools.ExecuteCommandToolHandler()

        with pytest.raises(RuntimeError, match="command_id"):
            handler.run_tool({})


class TestOpenFileToolHandler:
    """Tests for the open file tool."""

    def test_run_tool(self, mock_responses, base_url):
        mock_responses.add(
            responses.POST,
            f"{base_url}/open/note.md",
            status=204,
        )

        handler = tools.OpenFileToolHandler()
        result = handler.run_tool({"filename": "note.md"})

        assert len(result) == 1
        assert "Successfully" in result[0].text
        assert "note.md" in result[0].text

    def test_run_tool_new_leaf(self, mock_responses, base_url):
        mock_responses.add(
            responses.POST,
            f"{base_url}/open/Projects/todo.md",
            status=204,
        )

        handler = tools.OpenFileToolHandler()
        result = handler.run_tool({"filename": "Projects/todo.md", "new_leaf": True})

        assert len(result) == 1
        assert "new_leaf=True" in result[0].text

    def test_missing_filename_raises_error(self):
        handler = tools.OpenFileToolHandler()

        with pytest.raises(RuntimeError, match="filename"):
            handler.run_tool({})
