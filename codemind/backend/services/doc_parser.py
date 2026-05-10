from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(slots=True)
class DocChunk:
    file_path: str
    chunk_type: str
    heading_path: list[str]
    content: str


class DocumentParser:
    SUPPORTED_SUFFIXES = {".md", ".rst", ".adoc", ".yaml", ".yml", ".json"}

    def parse(self, path: str) -> list[DocChunk]:
        file_path = Path(path)
        suffix = file_path.suffix.lower()
        if file_path.name.lower().startswith("adr"):
            chunk_type = "adr"
        elif suffix in {".yaml", ".yml", ".json"}:
            chunk_type = "openapi"
        else:
            chunk_type = "doc"

        text = file_path.read_text(encoding="utf-8")
        if suffix == ".md":
            return self._parse_markdown(file_path.as_posix(), text, chunk_type)
        return [DocChunk(file_path.as_posix(), chunk_type, [], text)]

    @staticmethod
    def _parse_markdown(file_path: str, text: str, chunk_type: str) -> list[DocChunk]:
        chunks: list[DocChunk] = []
        current_headings: list[str] = []
        current_buffer: list[str] = []

        def flush() -> None:
            if current_buffer:
                chunks.append(
                    DocChunk(
                        file_path=file_path,
                        chunk_type=chunk_type,
                        heading_path=current_headings.copy(),
                        content="\n".join(current_buffer).strip(),
                    )
                )
                current_buffer.clear()

        for line in text.splitlines():
            match = re.match(r"^(#{1,6})\s+(.*)$", line)
            if match:
                flush()
                level = len(match.group(1))
                heading = match.group(2).strip()
                current_headings[:] = current_headings[: level - 1] + [heading]
            current_buffer.append(line)
        flush()
        return chunks
