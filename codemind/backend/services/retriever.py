from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Iterable

from codemind.backend.agents.query_analyzer import StructuredQuery


@dataclass(slots=True)
class RetrievalItem:
    source: str
    key: str
    file_path: str
    line_range: tuple[int, int]
    score: float
    payload: dict


class MultiSourceRetriever:
    def retrieve(self, query: StructuredQuery) -> list[RetrievalItem]:
        with ThreadPoolExecutor(max_workers=3) as executor:
            vector_future = executor.submit(self._vector_search, query)
            keyword_future = executor.submit(self._keyword_search, query)
            graph_future = executor.submit(self._graph_search, query)

            merged = self._rrf_merge(
                [vector_future.result(), keyword_future.result(), graph_future.result()],
            )
        return merged[:15]

    def _vector_search(self, query: StructuredQuery) -> list[RetrievalItem]:
        return [RetrievalItem("vector", f"v{i}", f"src/{keyword}.py", (1, 10), 1.0 - (i * 0.05), {"keyword": keyword}) for i, keyword in enumerate(query.keywords[:10])]

    def _keyword_search(self, query: StructuredQuery) -> list[RetrievalItem]:
        boosted = sorted(query.keywords, key=lambda value: ("function" not in value, "class" not in value))
        return [RetrievalItem("keyword", f"k{i}", f"docs/{keyword}.md", (1, 30), 1.0 - (i * 0.1), {"keyword": keyword}) for i, keyword in enumerate(boosted[:10])]

    def _graph_search(self, query: StructuredQuery) -> list[RetrievalItem]:
        return [RetrievalItem("graph", f"g{i}", f"graph/{module}.node", (0, 0), 0.9 - (i * 0.1), {"module": module}) for i, module in enumerate(query.target_modules_or_files[:10])]

    @staticmethod
    def _rrf_merge(result_lists: Iterable[list[RetrievalItem]], k: int = 60) -> list[RetrievalItem]:
        scores: dict[str, float] = {}
        by_key: dict[str, RetrievalItem] = {}
        for result_list in result_lists:
            for rank, item in enumerate(result_list, start=1):
                dedupe_key = f"{item.file_path}:{item.line_range}"
                by_key[dedupe_key] = item
                scores[dedupe_key] = scores.get(dedupe_key, 0.0) + (1.0 / (k + rank))

        return sorted(by_key.values(), key=lambda item: scores[f"{item.file_path}:{item.line_range}"], reverse=True)
