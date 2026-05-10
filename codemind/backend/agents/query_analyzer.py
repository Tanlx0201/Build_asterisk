from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import List


class QueryIntent(str, Enum):
    CODE_SEARCH = "CODE_SEARCH"
    EXPLANATION = "EXPLANATION"
    DEBUGGING = "DEBUGGING"
    ARCHITECTURE = "ARCHITECTURE"
    COMPARISON = "COMPARISON"


@dataclass(slots=True)
class StructuredQuery:
    original_question: str
    intent: QueryIntent
    keywords: List[str] = field(default_factory=list)
    semantic_query: str = ""
    target_languages: List[str] = field(default_factory=list)
    target_modules_or_files: List[str] = field(default_factory=list)
    time_constraint: str | None = None


class QueryAnalyzer:
    """Lightweight deterministic query analyzer for RAG routing."""

    _LANGUAGE_ALIASES = {
        "python": "python",
        "typescript": "typescript",
        "javascript": "javascript",
        "go": "go",
        "rust": "rust",
        "java": "java",
        "c#": "c#",
        "cpp": "c++",
        "c++": "c++",
        "ruby": "ruby",
        "php": "php",
        "swift": "swift",
        "kotlin": "kotlin",
        "scala": "scala",
        "sql": "sql",
        "yaml": "yaml",
        "dockerfile": "dockerfile",
        "terraform": "terraform",
    }

    def analyze(self, question: str) -> StructuredQuery:
        normalized = question.lower().strip()
        intent = self._classify_intent(normalized)
        keywords = [k for k in re.findall(r"[a-zA-Z_][a-zA-Z0-9_\-/]{2,}", normalized) if k not in {"what", "where", "when", "with", "does", "the", "and"}]
        target_languages = [lang for key, lang in self._LANGUAGE_ALIASES.items() if key in normalized]
        target_modules = re.findall(r"(?:module|file|service)\s+([\w./-]+)", normalized)
        time_constraint = "recent" if "recent" in normalized or "last sprint" in normalized else None
        return StructuredQuery(
            original_question=question,
            intent=intent,
            keywords=keywords[:12],
            semantic_query=question,
            target_languages=sorted(set(target_languages)),
            target_modules_or_files=target_modules,
            time_constraint=time_constraint,
        )

    @staticmethod
    def _classify_intent(normalized_question: str) -> QueryIntent:
        if any(token in normalized_question for token in ("where", "find", "locate", "search")):
            return QueryIntent.CODE_SEARCH
        if any(token in normalized_question for token in ("why", "error", "exception", "500", "bug", "debug")):
            return QueryIntent.DEBUGGING
        if any(token in normalized_question for token in ("depend", "architecture", "layer", "module")):
            return QueryIntent.ARCHITECTURE
        if " vs " in normalized_question or "compare" in normalized_question:
            return QueryIntent.COMPARISON
        return QueryIntent.EXPLANATION
