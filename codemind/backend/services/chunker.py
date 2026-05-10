from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .parser import ParseResult


@dataclass(slots=True)
class CodeChunk:
    repo_id: str
    file_path: str
    chunk_type: str
    symbol_name: str | None
    parent_symbol: str | None
    line_start: int
    line_end: int
    language: str
    complexity_score: float | None
    content: str
    context_window: str


class SemanticChunker:
    """AST-aware chunker that groups by symbols rather than token windows."""

    def build_chunks(self, repo_id: str, parse_result: ParseResult, source_text: str) -> list[CodeChunk]:
        lines = source_text.splitlines()
        chunks: list[CodeChunk] = []

        if parse_result.imports:
            header_end = min(max((f.line_range.line_start for f in parse_result.functions), default=1) - 1, len(lines))
            chunks.append(
                CodeChunk(
                    repo_id=repo_id,
                    file_path=parse_result.file_path,
                    chunk_type="module_header",
                    symbol_name=None,
                    parent_symbol=None,
                    line_start=1,
                    line_end=max(1, header_end),
                    language=parse_result.language,
                    complexity_score=None,
                    content="\n".join(lines[: max(1, header_end)]),
                    context_window="",
                )
            )

        for function in parse_result.functions:
            content = "\n".join(lines[function.line_range.line_start - 1 : function.line_range.line_end])
            chunks.append(
                CodeChunk(
                    repo_id=repo_id,
                    file_path=parse_result.file_path,
                    chunk_type="function",
                    symbol_name=function.name,
                    parent_symbol=None,
                    line_start=function.line_range.line_start,
                    line_end=function.line_range.line_end,
                    language=parse_result.language,
                    complexity_score=float(function.complexity_score),
                    content=content,
                    context_window="imports: " + ", ".join(imp.module or "." for imp in parse_result.imports),
                )
            )

        for class_info in parse_result.classes:
            content = "\n".join(lines[class_info.line_range.line_start - 1 : class_info.line_range.line_end])
            chunks.append(
                CodeChunk(
                    repo_id=repo_id,
                    file_path=parse_result.file_path,
                    chunk_type="class",
                    symbol_name=class_info.name,
                    parent_symbol=None,
                    line_start=class_info.line_range.line_start,
                    line_end=class_info.line_range.line_end,
                    language=parse_result.language,
                    complexity_score=None,
                    content=content,
                    context_window="parents: " + ", ".join(class_info.parents),
                )
            )

        return self._group_small_functions(chunks)

    @staticmethod
    def _group_small_functions(chunks: Iterable[CodeChunk]) -> list[CodeChunk]:
        grouped: list[CodeChunk] = []
        carry: list[CodeChunk] = []

        for chunk in sorted(chunks, key=lambda c: (c.file_path, c.line_start)):
            if chunk.chunk_type == "function" and (chunk.line_end - chunk.line_start + 1) < 10:
                carry.append(chunk)
                if len(carry) >= 2:
                    merged = CodeChunk(
                        repo_id=chunk.repo_id,
                        file_path=chunk.file_path,
                        chunk_type="function",
                        symbol_name=" + ".join(c.symbol_name or "" for c in carry),
                        parent_symbol=None,
                        line_start=carry[0].line_start,
                        line_end=carry[-1].line_end,
                        language=chunk.language,
                        complexity_score=sum((c.complexity_score or 0) for c in carry),
                        content="\n\n".join(c.content for c in carry),
                        context_window=carry[-1].context_window,
                    )
                    grouped.append(merged)
                    carry = []
                continue

            if carry:
                grouped.extend(carry)
                carry = []
            grouped.append(chunk)

        if carry:
            grouped.extend(carry)
        return grouped
