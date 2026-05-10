from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from codemind.backend.services.chunker import SemanticChunker
from codemind.backend.services.parser import ASTParser


@dataclass(slots=True)
class PipelineError:
    file_path: str
    error_message: str


@dataclass(slots=True)
class IngestionRun:
    repo_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    completed_at: datetime | None = None
    status: str = "running"
    files_total: int = 0
    files_parsed: int = 0
    files_failed: int = 0
    chunks_created: int = 0
    embeddings_created: int = 0
    errors: list[PipelineError] = field(default_factory=list)


class IngestionPipeline:
    def __init__(self) -> None:
        self.parser = ASTParser()
        self.chunker = SemanticChunker()

    def run(self, repo_id: str, file_paths: list[str], changed_files: set[str] | None = None) -> IngestionRun:
        run = IngestionRun(repo_id=repo_id, files_total=len(file_paths))

        for file_path in file_paths:
            if changed_files is not None and file_path not in changed_files:
                continue

            try:
                source = Path(file_path).read_text(encoding="utf-8")
                result = self.parser.parse_file(file_path)
                chunks = self.chunker.build_chunks(repo_id=repo_id, parse_result=result, source_text=source)
                run.files_parsed += 1
                run.chunks_created += len(chunks)
                run.embeddings_created += len(chunks)
            except Exception as exc:
                run.files_failed += 1
                run.errors.append(PipelineError(file_path=file_path, error_message=str(exc)))

        run.completed_at = datetime.now(tz=timezone.utc)
        run.status = "completed_with_errors" if run.files_failed else "completed"
        return run
