import re
import requests
import urllib.parse
from urllib.parse import quote, unquote
import unicodedata
import os
from typing import Any


class HeadingNotFoundError(Exception):
    """Raised when a target heading is not found in a file."""

    pass


class Obsidian:
    def __init__(
        self,
        api_key: str,
        protocol: str = os.getenv("OBSIDIAN_PROTOCOL", "https").lower(),
        host: str = str(os.getenv("OBSIDIAN_HOST", "127.0.0.1")),
        port: int = int(os.getenv("OBSIDIAN_PORT", "27124")),
        verify_ssl: bool = False,
    ):
        self.api_key = api_key

        if protocol == "http":
            self.protocol = "http"
        else:
            self.protocol = (
                "https"  # Default to https for any other value, including 'https'
            )

        self.host = host
        self.port = port
        self.verify_ssl = verify_ssl
        self.timeout = (3, 6)

    def get_base_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    def _get_headers(self) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return headers

    def _safe_call(self, f) -> Any:
        try:
            return f()
        except requests.HTTPError as e:
            # Try to parse JSON error response, fall back to raw text
            error_data = {}
            if e.response.content:
                try:
                    error_data = e.response.json()
                except ValueError:
                    # Response is not JSON (e.g., plain text "Not Found")
                    raw_text = e.response.text.strip()
                    raise Exception(
                        f"HTTP {e.response.status_code}: {raw_text or 'Unknown error'}"
                    )
            code = error_data.get("errorCode", -1)
            message = error_data.get("message", "<unknown>")
            raise Exception(f"Error {code}: {message}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def _encode_path(self, path: str) -> str:
        """Encode path segments while preserving directory separators and trailing slashes.

        Features:
        - Idempotent: Prevents double-encoding of already encoded paths
        - Unicode normalization: Converts NFD to NFC for consistency
        - RFC 3986 compliant: Preserves safe characters (-_.~)
        - Preserves directory structure: "/" separators and trailing "/" maintained

        Args:
            path: File or directory path (relative to vault root)

        Returns:
            URL-encoded path with preserved "/" separators and trailing slash

        Examples:
            "simple.md" → "simple.md"
            "Reports/2024/" → "Reports/2024/" (trailing slash preserved)
            "Área/çãõ/test.md" → "%C3%81rea/%C3%A7%C3%A3%C3%B5/test.md"
            "already%20encoded/" → "already%20encoded/" (idempotent)
            "emoji/📘 notes.md" → "emoji/%F0%9F%93%98%20notes.md"
        """
        if not path:
            return ""

        # Record if path had trailing slash before processing
        had_trailing_slash = path.endswith("/")

        # Split path into segments, removing empty segments
        segments = [seg for seg in path.strip("/").split("/") if seg]

        # RFC 3986 unreserved characters that don't need encoding
        safe_chars = "-_.~"

        encoded_segments = []
        for segment in segments:
            # Prevent double-encoding by decoding first
            segment = unquote(segment)

            # Normalize Unicode (NFD → NFC) for consistency across platforms
            segment = unicodedata.normalize("NFC", segment)

            # Encode segment while preserving safe characters
            encoded_segment = quote(segment, safe=safe_chars)
            encoded_segments.append(encoded_segment)

        # Join segments and restore trailing slash if originally present
        encoded_path = "/".join(encoded_segments)
        if had_trailing_slash and encoded_segments:
            encoded_path += "/"

        return encoded_path

    def list_files_in_vault(self) -> Any:
        url = f"{self.get_base_url()}/vault/"

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.json()["files"]

        return self._safe_call(call_fn)

    def list_files_in_dir(self, dirpath: str) -> Any:
        encoded_path = self._encode_path(dirpath)
        # Ensure exactly one trailing slash for directory endpoint
        if not encoded_path.endswith("/"):
            encoded_path += "/"
        url = f"{self.get_base_url()}/vault/{encoded_path}"

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.json()["files"]

        return self._safe_call(call_fn)

    def get_file_contents(self, filepath: str) -> Any:
        encoded_path = self._encode_path(filepath)
        url = f"{self.get_base_url()}/vault/{encoded_path}"

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.text

        return self._safe_call(call_fn)

    def get_batch_file_contents(self, filepaths: list[str]) -> str:
        """Get contents of multiple files and concatenate them with headers.

        Args:
            filepaths: List of file paths to read

        Returns:
            String containing all file contents with headers
        """
        result = []

        for filepath in filepaths:
            try:
                content = self.get_file_contents(filepath)
                result.append(f"# {filepath}\n\n{content}\n\n---\n\n")
            except Exception as e:
                # Add error message but continue processing other files
                result.append(
                    f"# {filepath}\n\nError reading file: {str(e)}\n\n---\n\n"
                )

        return "".join(result)

    def search(self, query: str, context_length: int = 100, limit: int = 100) -> Any:
        url = f"{self.get_base_url()}/search/simple/"
        params = {"query": query, "contextLength": context_length, "limit": limit}

        def call_fn():
            response = requests.post(
                url,
                headers=self._get_headers(),
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)

    def append_content(self, filepath: str, content: str) -> Any:
        encoded_path = self._encode_path(filepath)
        url = f"{self.get_base_url()}/vault/{encoded_path}"

        def call_fn():
            response = requests.post(
                url,
                headers=self._get_headers() | {"Content-Type": "text/markdown"},
                data=content,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)

    def patch_content(
        self,
        filepath: str,
        operation: str,
        target_type: str,
        target: str,
        content: str,
        create_heading_if_missing: bool = True,
        template_path: str | None = None,
        use_template: bool = True,
    ) -> Any:
        # For heading operations, use the smarter read-modify-write approach
        # This bypasses the buggy REST API PATCH endpoint
        if target_type == "heading":
            try:
                return self._patch_heading_content(filepath, operation, target, content)
            except HeadingNotFoundError:
                # Heading doesn't exist - create it if allowed
                if create_heading_if_missing:
                    return self._create_heading_and_append(
                        filepath,
                        target,
                        content,
                        template_path=template_path,
                        use_template=use_template,
                    )
                else:
                    raise Exception(f"Error 40080: Heading '{target}' not found")

        # For block and frontmatter operations, use the REST API PATCH endpoint
        encoded_path = self._encode_path(filepath)
        url = f"{self.get_base_url()}/vault/{encoded_path}"

        headers = self._get_headers() | {
            "Content-Type": "text/markdown",
            "Operation": operation,
            "Target-Type": target_type,
            "Target": urllib.parse.quote(target),
        }

        try:
            response = requests.patch(
                url,
                headers=headers,
                data=content,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return None
        except requests.HTTPError as e:
            raise Exception(self._format_http_error(e))
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def _format_http_error(self, e: requests.HTTPError) -> str:
        """Format an HTTP error into a readable message."""
        if e.response is not None and e.response.content:
            try:
                error_data = e.response.json()
                code = error_data.get("errorCode", -1)
                message = error_data.get("message", "<unknown>")
                return f"Error {code}: {message}"
            except ValueError:
                raw_text = e.response.text.strip()
                return f"HTTP {e.response.status_code}: {raw_text or 'Unknown error'}"
        return f"HTTP error: {str(e)}"

    def _parse_frontmatter(self, content: str) -> dict[str, Any]:
        """Parse YAML frontmatter from markdown content.

        Args:
            content: Markdown content that may contain frontmatter

        Returns:
            Dictionary of frontmatter fields, empty dict if none found
        """
        if not content.startswith("---"):
            return {}

        # Find the closing ---
        end_match = re.search(r"\n---\s*\n", content[3:])
        if not end_match:
            return {}

        frontmatter_text = content[4 : end_match.start() + 3]
        result: dict[str, Any] = {}

        # Simple YAML parsing for key: value pairs
        for line in frontmatter_text.split("\n"):
            line = line.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value:
                    result[key] = value

        return result

    def _get_template_for_file(self, filepath: str, content: str) -> str | None:
        """Get template path from frontmatter or folder convention.

        Args:
            filepath: Path to the file
            content: File content (to avoid re-reading)

        Returns:
            Template path if found, None otherwise
        """
        # 1. Check frontmatter for 'template:' field
        frontmatter = self._parse_frontmatter(content)
        if "template" in frontmatter:
            template_path = frontmatter["template"]
            # Handle relative paths - assume Templates/ folder if not specified
            if not template_path.startswith("Templates/"):
                template_path = f"Templates/{template_path}"
            return template_path

        # 2. Folder convention: Daily Notes/*.md -> Templates/Daily Notes.md
        if "/" in filepath:
            folder = filepath.rsplit("/", 1)[0]
            convention_template = f"Templates/{folder}.md"
            # Check if template exists by trying to read it
            try:
                self.get_file_contents(convention_template)
                return convention_template
            except Exception:
                pass

        return None

    def _parse_heading_structure(self, content: str) -> list[tuple[int, str, int]]:
        """Parse markdown to extract heading hierarchy with line positions.

        Args:
            content: Markdown content

        Returns:
            List of (level, heading_text, line_number) tuples
        """
        headings: list[tuple[int, str, int]] = []
        lines = content.split("\n")

        for i, line in enumerate(lines):
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append((level, text, i))

        return headings

    def _find_insertion_point(
        self,
        current_headings: list[tuple[int, str, int]],
        template_headings: list[tuple[int, str, int]],
        target_heading: str,
        target_level: int,
    ) -> int | None:
        """Find line number where heading should be inserted based on template order.

        Args:
            current_headings: Headings in the current file
            template_headings: Headings from the template
            target_heading: The heading text to insert
            target_level: The heading level (e.g., 2 for ##)

        Returns:
            Line number for insertion, or None if should append to end
        """
        # Find target heading position in template
        template_index = None
        for i, (level, text, _) in enumerate(template_headings):
            if text == target_heading and level == target_level:
                template_index = i
                break

        if template_index is None:
            # Heading not in template, append to end
            return None

        # Find the heading that should come AFTER our target in the template
        next_template_headings = []
        for i in range(template_index + 1, len(template_headings)):
            level, text, _ = template_headings[i]
            # Only consider same or higher level headings as boundaries
            if level <= target_level:
                next_template_headings.append((level, text))
                break

        # Find where any of those "next" headings appear in current content
        for level, text, line_num in current_headings:
            for next_level, next_text in next_template_headings:
                if text == next_text and level == next_level:
                    # Insert before this heading
                    return line_num

        # Also check if there's a heading BEFORE our target in template
        # and find where that section ends
        for i in range(template_index - 1, -1, -1):
            prev_level, prev_text, _ = template_headings[i]
            if prev_level <= target_level:
                # Find this heading in current content
                for level, text, line_num in current_headings:
                    if text == prev_text and level == prev_level:
                        # Find the end of this section (next same-level heading)
                        for lvl, txt, ln in current_headings:
                            if ln > line_num and lvl <= level:
                                return ln
                        # No next heading, will append
                        return None
                break

        return None

    def _find_heading_boundary(
        self,
        lines: list[str],
        headings: list[tuple[int, str, int]],
        target_line: int,
        target_level: int,
    ) -> int:
        """Find the line number where a heading's content ends.

        The boundary is the line before the next heading at the same or higher level,
        or the end of the file.

        Args:
            lines: All lines in the file
            headings: Parsed heading structure (level, text, line_num)
            target_line: Line number of the target heading
            target_level: Level of the target heading (e.g., 2 for ##)

        Returns:
            Line number where content should be inserted (for append) or
            where the section ends
        """
        for level, _, line_num in headings:
            if line_num > target_line and level <= target_level:
                # Found next same-level or higher heading
                return line_num
        # No boundary found - section extends to end of file
        return len(lines)

    def _find_heading_in_structure(
        self,
        headings: list[tuple[int, str, int]],
        target: str,
    ) -> tuple[int, int, int] | None:
        """Find a heading in the parsed structure.

        Supports nested syntax like "Parent::Child" for finding subheadings.

        Args:
            headings: Parsed heading structure (level, text, line_num)
            target: Heading text to find, or "Parent::Child" for nested

        Returns:
            Tuple of (level, text, line_num) or None if not found
        """
        parts = target.split("::")

        if len(parts) == 1:
            # Simple heading - find first match
            for level, text, line_num in headings:
                if text == target:
                    return (level, text, line_num)
            return None

        # Nested heading - find parent first, then child within parent's scope
        parent_target = parts[0]
        child_target = parts[-1]

        parent = None
        for level, text, line_num in headings:
            if text == parent_target:
                parent = (level, text, line_num)
                break

        if parent is None:
            return None

        parent_level, _, parent_line = parent

        # Find child within parent's scope
        for level, text, line_num in headings:
            if line_num <= parent_line:
                continue
            # Stop if we hit a heading at parent's level or higher
            if level <= parent_level:
                break
            if text == child_target:
                return (level, text, line_num)

        return None

    def _patch_heading_content(
        self,
        filepath: str,
        operation: str,
        target: str,
        content: str,
    ) -> Any:
        """Patch content at a heading using read-modify-write pattern.

        This bypasses the REST API PATCH endpoint which has known bugs with
        heading targeting. Instead, we read the file, parse the structure,
        modify it, and write it back.

        Args:
            filepath: Path to the file
            operation: "append", "prepend", or "replace"
            target: Heading text (e.g., "Todos" or "Notes::Subsection")
            content: Content to insert

        Returns:
            None on success

        Raises:
            Exception: If heading is not found (triggers fallback to create)
        """
        # Read current content
        current_content = self.get_file_contents(filepath)
        lines = current_content.split("\n")

        # Parse heading structure
        headings = self._parse_heading_structure(current_content)

        # Find target heading
        found = self._find_heading_in_structure(headings, target)

        if found is None:
            # Heading not found - raise exception to trigger fallback
            raise HeadingNotFoundError(f"Heading '{target}' not found in {filepath}")

        target_level, _, target_line = found

        # Find boundary (where this heading's content ends)
        boundary_line = self._find_heading_boundary(
            lines, headings, target_line, target_level
        )

        # Perform the operation
        if operation == "append":
            # Insert content just before the boundary
            # Find the last non-empty line before boundary to insert after
            insert_line = boundary_line

            # Ensure content starts with newline if needed
            if not content.startswith("\n"):
                content = "\n" + content

            lines.insert(insert_line, content.rstrip("\n"))

        elif operation == "prepend":
            # Insert content immediately after the heading line
            insert_line = target_line + 1

            # Ensure content ends with newline
            if not content.endswith("\n"):
                content = content + "\n"

            lines.insert(insert_line, content.strip("\n"))

        elif operation == "replace":
            # Replace everything between heading and boundary
            # Keep the heading line, replace lines after it up to boundary
            new_lines = lines[: target_line + 1]

            # Add the new content
            content_lines = content.strip("\n").split("\n")
            new_lines.extend(content_lines)

            # Add back everything from boundary onwards
            new_lines.extend(lines[boundary_line:])
            lines = new_lines

        else:
            raise ValueError(f"Unknown operation: {operation}")

        # Write back
        new_content = "\n".join(lines)
        return self.put_content(filepath, new_content)

    def _insert_heading_at_position(
        self,
        filepath: str,
        content: str,
        heading: str,
        heading_content: str,
        line_number: int,
        heading_level: int,
    ) -> Any:
        """Insert a heading at a specific line position.

        Args:
            filepath: Path to the file
            content: Current file content
            heading: Heading text
            heading_content: Content to add under the heading
            line_number: Line number to insert at
            heading_level: Level of heading (2 for ##, 3 for ###, etc.)

        Returns:
            Result of put_content
        """
        lines = content.split("\n")
        heading_prefix = "#" * heading_level
        new_section = f"\n{heading_prefix} {heading}{heading_content}\n"

        # Insert before the specified line
        lines.insert(line_number, new_section)
        new_content = "\n".join(lines)

        return self.put_content(filepath, new_content)

    def _create_heading_and_append(
        self,
        filepath: str,
        heading: str,
        content: str,
        template_path: str | None = None,
        use_template: bool = True,
    ) -> Any:
        """Create a missing heading and insert content, using template for positioning.

        Args:
            filepath: Path to the file
            heading: The heading text (without # prefix), supports :: for nesting
            content: Content to add under the heading
            template_path: Optional explicit template path
            use_template: Whether to use template for heading position (default: True)
        """
        # Determine heading level from the target (e.g., "Todos" -> "## Todos")
        # Default to h2 for top-level headings
        heading_parts = heading.split("::")
        heading_level = len(heading_parts) + 1  # h2 for top-level, h3 for nested, etc.
        final_heading = heading_parts[-1]  # Use the last part as the heading text

        # Read current file contents
        current_content = self.get_file_contents(filepath)

        # Try to find template and use it for positioning
        if use_template:
            template = template_path or self._get_template_for_file(
                filepath, current_content
            )

            if template:
                try:
                    template_content = self.get_file_contents(template)
                    template_headings = self._parse_heading_structure(template_content)
                    current_headings = self._parse_heading_structure(current_content)

                    insertion_point = self._find_insertion_point(
                        current_headings,
                        template_headings,
                        final_heading,
                        heading_level,
                    )

                    if insertion_point is not None:
                        return self._insert_heading_at_position(
                            filepath,
                            current_content,
                            final_heading,
                            content,
                            insertion_point,
                            heading_level,
                        )
                except Exception:
                    # Template not found or error reading it, fall through to append
                    pass

        # Fallback: append to end
        heading_prefix = "#" * heading_level
        new_section = f"\n\n{heading_prefix} {final_heading}{content}"
        new_content = current_content.rstrip() + new_section

        return self.put_content(filepath, new_content)

    def put_content(self, filepath: str, content: str) -> Any:
        encoded_path = self._encode_path(filepath)
        url = f"{self.get_base_url()}/vault/{encoded_path}"

        def call_fn():
            response = requests.put(
                url,
                headers=self._get_headers() | {"Content-Type": "text/markdown"},
                data=content,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)

    def delete_file(self, filepath: str) -> Any:
        """Delete a file or directory from the vault.

        Args:
            filepath: Path to the file to delete (relative to vault root)

        Returns:
            None on success
        """
        encoded_path = self._encode_path(filepath)
        url = f"{self.get_base_url()}/vault/{encoded_path}"

        def call_fn():
            response = requests.delete(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)

    def search_json(self, query: dict) -> Any:
        url = f"{self.get_base_url()}/search/"

        headers = self._get_headers() | {
            "Content-Type": "application/vnd.olrapi.jsonlogic+json"
        }

        def call_fn():
            response = requests.post(
                url,
                headers=headers,
                json=query,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)

    def get_periodic_note(self, period: str, as_json: bool = False) -> Any:
        """Get current periodic note for the specified period.

        Args:
            period: The period type (daily, weekly, monthly, quarterly, yearly)
            as_json: Whether to return JSON format with metadata (default: False)

        Returns:
            Content of the periodic note (text or JSON)
        """
        url = f"{self.get_base_url()}/periodic/{period}/"

        def call_fn():
            headers = self._get_headers()
            if as_json:
                headers["Accept"] = "application/vnd.olrapi.note+json"
            response = requests.get(
                url, headers=headers, verify=self.verify_ssl, timeout=self.timeout
            )
            response.raise_for_status()

            if as_json:
                return response.json()
            return response.text

        return self._safe_call(call_fn)

    def get_recent_periodic_notes(
        self, period: str, limit: int = 5, include_content: bool = False
    ) -> Any:
        """Get most recent periodic notes for the specified period type.

        Args:
            period: The period type (daily, weekly, monthly, quarterly, yearly)
            limit: Maximum number of notes to return (default: 5)
            include_content: Whether to include note content (default: False)

        Returns:
            List of recent periodic notes
        """
        url = f"{self.get_base_url()}/periodic/{period}/recent"
        params = {"limit": limit, "includeContent": include_content}

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.json()

        return self._safe_call(call_fn)

    def get_recent_changes(self, limit: int = 10, days: int = 90) -> Any:
        """Get recently modified files in the vault.

        Args:
            limit: Maximum number of files to return (default: 10)
            days: Only include files modified within this many days (default: 90)

        Returns:
            List of recently modified files with metadata
        """
        # Build the DQL query
        query_lines = [
            "TABLE file.mtime",
            f"WHERE file.mtime >= date(today) - dur({days} days)",
            "SORT file.mtime DESC",
            f"LIMIT {limit}",
        ]

        # Join with proper DQL line breaks
        dql_query = "\n".join(query_lines)

        # Make the request to search endpoint
        url = f"{self.get_base_url()}/search/"
        headers = self._get_headers() | {
            "Content-Type": "application/vnd.olrapi.dataview.dql+txt"
        }

        def call_fn():
            response = requests.post(
                url,
                headers=headers,
                data=dql_query.encode("utf-8"),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)

    def dataview_query(self, dql_query: str) -> Any:
        """Execute a Dataview DQL query against the vault.

        Args:
            dql_query: The Dataview query string (e.g., "TABLE title, status FROM #tag")

        Returns:
            Query results as JSON

        Note:
            Requires the Dataview plugin to be installed in Obsidian.
        """
        url = f"{self.get_base_url()}/search/"
        headers = self._get_headers() | {
            "Content-Type": "application/vnd.olrapi.dataview.dql+txt"
        }

        def call_fn():
            response = requests.post(
                url,
                headers=headers,
                data=dql_query.encode("utf-8"),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)

    def get_active_note(self, as_json: bool = False) -> Any:
        """Get content of the currently active note in Obsidian.

        Args:
            as_json: Whether to return JSON format with metadata (default: False)

        Returns:
            Content of the active note (text or JSON)
        """
        url = f"{self.get_base_url()}/active/"

        def call_fn():
            headers = self._get_headers()
            if as_json:
                headers["Accept"] = "application/vnd.olrapi.note+json"
            response = requests.get(
                url, headers=headers, verify=self.verify_ssl, timeout=self.timeout
            )
            response.raise_for_status()

            if as_json:
                return response.json()
            return response.text

        return self._safe_call(call_fn)

    def list_commands(self) -> Any:
        """List all available Obsidian commands from the command palette.

        Returns:
            List of available commands with their IDs and names
        """
        url = f"{self.get_base_url()}/commands/"

        def call_fn():
            response = requests.get(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        return self._safe_call(call_fn)

    def execute_command(self, command_id: str) -> Any:
        """Execute a specific Obsidian command by its ID.

        Args:
            command_id: The ID of the command to execute

        Returns:
            None on success

        Warning:
            Some commands may be destructive or change Obsidian settings.
            Use with caution and verify command IDs with list_commands().
        """
        url = f"{self.get_base_url()}/commands/{urllib.parse.quote(command_id)}/"

        def call_fn():
            response = requests.post(
                url,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)

    def open_file(self, filename: str, new_leaf: bool = False) -> Any:
        """Open a file in Obsidian UI.

        Args:
            filename: Path to the file to open (relative to vault root)
            new_leaf: If True, opens in new tab/pane; if False, opens in current view

        Returns:
            None on success
        """
        encoded_filename = self._encode_path(filename)
        url = f"{self.get_base_url()}/open/{encoded_filename}"
        params = {"newLeaf": str(new_leaf).lower()}

        def call_fn():
            response = requests.post(
                url,
                headers=self._get_headers(),
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return None

        return self._safe_call(call_fn)
