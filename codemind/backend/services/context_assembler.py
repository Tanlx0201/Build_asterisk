from __future__ import annotations

from collections import defaultdict

from .retriever import RetrievalItem


class ContextAssembler:
    DEFAULT_CHARACTER_BUDGET = 120_000

    def assemble(
        self,
        chunks: list[RetrievalItem],
        character_budget: int = DEFAULT_CHARACTER_BUDGET,
    ) -> str:
        grouped: dict[str, list[RetrievalItem]] = defaultdict(list)
        for chunk in chunks:
            grouped[chunk.file_path].append(chunk)

        sections: list[str] = []
        for file_path, file_chunks in grouped.items():
            ordered = sorted(file_chunks, key=lambda chunk: chunk.line_range)
            sections.append(f"## {file_path}")
            for chunk in ordered:
                sections.append(f"- lines {chunk.line_range[0]}-{chunk.line_range[1]} ({chunk.source})")

        if not sections:
            return ""

        context_parts: list[str] = []
        current_length = 0
        for section in sections:
            candidate = section if not context_parts else f"\n{section}"
            if current_length + len(candidate) > character_budget:
                truncation_marker = "\n... [truncated]"
                if current_length + len(truncation_marker) <= character_budget:
                    context_parts.append(truncation_marker)
                break
            context_parts.append(candidate)
            current_length += len(candidate)
        return "".join(context_parts)
