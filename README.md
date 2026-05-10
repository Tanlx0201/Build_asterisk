# Build_asterisk

This repository now contains an initial scaffold for **CodeMind**, including a
minimal backend implementation for repository ingestion, parsing, semantic
chunking, retrieval context assembly, webhook validation, and architecture rule
configuration.

## Implemented scaffold

- `codemind/backend/agents/query_analyzer.py`
- `codemind/backend/services/parser.py`
- `codemind/backend/services/chunker.py`
- `codemind/backend/services/doc_parser.py`
- `codemind/backend/services/retriever.py`
- `codemind/backend/services/context_assembler.py`
- `codemind/backend/pipelines/ingest.py`
- `codemind/backend/api/routes/webhooks.py`
- `codemind/backend/config/architecture.yaml`
- `tests/unit/test_codemind_minimal.py`

## Run tests

```bash
cd /home/runner/work/Build_asterisk/Build_asterisk
python -m unittest tests/unit/test_codemind_minimal.py -v
```
