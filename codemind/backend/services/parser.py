from __future__ import annotations

import ast
from dataclasses import dataclass, field
import logging
from pathlib import Path
import re
from typing import Iterable


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CodeRange:
    line_start: int
    line_end: int


@dataclass(slots=True)
class FunctionInfo:
    name: str
    params: list[str]
    return_type: str | None
    line_range: CodeRange
    complexity_score: int
    calls: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ClassInfo:
    name: str
    parents: list[str]
    line_range: CodeRange


@dataclass(slots=True)
class ImportInfo:
    module: str
    symbols: list[str]
    is_relative: bool


@dataclass(slots=True)
class ParseResult:
    file_path: str
    language: str
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    imports: list[ImportInfo]
    exports: list[str]
    long_strings: list[str]
    todos: list[str]


class ASTParser:
    MIN_LONG_STRING_LENGTH = 50

    SUPPORTED_LANGUAGES = {
        ".py": "python",
        ".ts": "typescript",
        ".js": "javascript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".cs": "c#",
        ".cpp": "c++",
        ".cc": "c++",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sql": "sql",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".tf": "terraform",
        "Dockerfile": "dockerfile",
    }

    TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b.*")

    def parse_file(self, path: str | Path) -> ParseResult:
        file_path = str(path)
        suffix = Path(file_path).suffix
        language = self.SUPPORTED_LANGUAGES.get(suffix) or self.SUPPORTED_LANGUAGES.get(Path(file_path).name, "unknown")
        source = Path(file_path).read_text(encoding="utf-8")

        if language == "python":
            return self._parse_python(file_path, source)

        return ParseResult(
            file_path=file_path,
            language=language,
            functions=[],
            classes=[],
            imports=[],
            exports=self._extract_exports(source),
            long_strings=self._extract_long_strings(source),
            todos=self.TODO_PATTERN.findall(source),
        )

    def _parse_python(self, file_path: str, source: str) -> ParseResult:
        tree = ast.parse(source)
        functions: list[FunctionInfo] = []
        classes: list[ClassInfo] = []
        imports: list[ImportInfo] = []
        long_strings: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                calls = [n.func.id for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
                functions.append(
                    FunctionInfo(
                        name=node.name,
                        params=[a.arg for a in node.args.args],
                        return_type=ast.unparse(node.returns) if node.returns else None,
                        line_range=CodeRange(node.lineno, getattr(node, "end_lineno", node.lineno)),
                        complexity_score=self._complexity(node),
                        calls=calls,
                    )
                )
            elif isinstance(node, ast.ClassDef):
                classes.append(
                    ClassInfo(
                        name=node.name,
                        parents=[ast.unparse(base) for base in node.bases],
                        line_range=CodeRange(node.lineno, getattr(node, "end_lineno", node.lineno)),
                    )
                )
            elif isinstance(node, ast.Import):
                imports.append(ImportInfo(module="", symbols=[alias.name for alias in node.names], is_relative=False))
            elif isinstance(node, ast.ImportFrom):
                imports.append(
                    ImportInfo(
                        module=node.module or "",
                        symbols=[alias.name for alias in node.names],
                        is_relative=(node.level or 0) > 0,
                    )
                )
            elif (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and len(node.value) > self.MIN_LONG_STRING_LENGTH
            ):
                long_strings.append(node.value)

        todos = [match.group(0) for match in self.TODO_PATTERN.finditer(source)]

        return ParseResult(
            file_path=file_path,
            language="python",
            functions=functions,
            classes=classes,
            imports=imports,
            exports=self._extract_exports(source),
            long_strings=long_strings,
            todos=todos,
        )

    @staticmethod
    def _complexity(function_node: ast.AST) -> int:
        branches = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.BoolOp, ast.Match)
        return 1 + sum(1 for n in ast.walk(function_node) if isinstance(n, branches))

    @staticmethod
    def _extract_exports(source: str) -> list[str]:
        export_match = re.search(r"__all__\s*=\s*\[(.*?)\]", source, flags=re.DOTALL)
        if not export_match:
            return []
        names = re.findall(r"['\"]([^'\"]+)['\"]", export_match.group(1))
        return names

    def _extract_long_strings(self, source: str) -> list[str]:
        min_length_plus_one = self.MIN_LONG_STRING_LENGTH + 1
        pattern = re.compile(
            rf"\"\"\"(.*?)\"\"\"|'''(.*?)'''|\"([^\"]{{{min_length_plus_one},}})\"|'([^']{{{min_length_plus_one},}})'",
            re.DOTALL,
        )
        long_strings: list[str] = []
        for match in pattern.finditer(source):
            value = next((group for group in match.groups() if group), "")
            if len(value) > self.MIN_LONG_STRING_LENGTH:
                long_strings.append(value)
        return long_strings


def parse_repository_files(paths: Iterable[str]) -> list[ParseResult]:
    parser = ASTParser()
    results: list[ParseResult] = []
    for path in paths:
        try:
            results.append(parser.parse_file(path))
        except Exception as exc:
            logger.warning("Failed parsing %s (%s): %s", path, type(exc).__name__, exc)
            continue
    return results
