from __future__ import annotations

from collections import defaultdict

from .retriever import RetrievalItem


class ContextAssembler:
    def assemble(self, chunks: list[RetrievalItem], token_budget: int = 120_000) -> str:
        grouped: dict[str, list[RetrievalItem]] = defaultdict(list)
        for chunk in chunks:
            grouped[chunk.file_path].append(chunk)

        sections: list[str] = []
        for file_path, file_chunks in grouped.items():
            ordered = sorted(file_chunks, key=lambda chunk: chunk.line_range)
            sections.append(f"## {file_path}")
            for chunk in ordered:
                sections.append(f"- lines {chunk.line_range[0]}-{chunk.line_range[1]} ({chunk.source})")

        context = "\n".join(sections)
        if len(context) > token_budget:
            return context[:token_budget]
        return context
