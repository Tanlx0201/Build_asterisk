import tempfile
import unittest
from pathlib import Path

from codemind.backend.agents.query_analyzer import QueryAnalyzer, QueryIntent
from codemind.backend.pipelines.ingest import IngestionPipeline
from codemind.backend.services.chunker import SemanticChunker
from codemind.backend.services.parser import ASTParser


SAMPLE_CODE = '''
import os

class Service:
    def run(self):
        return helper(1)

def helper(value: int):
    if value > 0:
        return value
    return 0
'''


class CodeMindMinimalTests(unittest.TestCase):
    def test_query_analyzer_classifies_debugging(self):
        analyzer = QueryAnalyzer()
        result = analyzer.analyze("Why is login endpoint returning 500 in python service?")
        self.assertEqual(result.intent, QueryIntent.DEBUGGING)
        self.assertIn("python", result.target_languages)

    def test_parser_and_chunker_generate_function_chunks(self):
        with tempfile.TemporaryDirectory() as td:
            source_file = Path(td) / "sample.py"
            source_file.write_text(SAMPLE_CODE, encoding="utf-8")

            parser = ASTParser()
            parsed = parser.parse_file(source_file)
            chunker = SemanticChunker()
            chunks = chunker.build_chunks("repo-1", parsed, SAMPLE_CODE)

            self.assertGreaterEqual(len(parsed.functions), 2)
            self.assertTrue(any(chunk.chunk_type == "function" for chunk in chunks))

    def test_ingestion_pipeline_completes(self):
        with tempfile.TemporaryDirectory() as td:
            source_file = Path(td) / "sample.py"
            source_file.write_text(SAMPLE_CODE, encoding="utf-8")

            run = IngestionPipeline().run("repo-1", [str(source_file)])
            self.assertEqual(run.status, "completed")
            self.assertEqual(run.files_parsed, 1)
            self.assertEqual(run.files_failed, 0)


if __name__ == "__main__":
    unittest.main()
