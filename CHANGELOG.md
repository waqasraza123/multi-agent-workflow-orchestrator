# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

- repo governance and release metadata polish
- GitHub community health files
- release documentation alignment

## 0.1.0 - 2026-03-16

### Added
- backend first run lifecycle with planning, execution, verification, and finalization
- deterministic turn execution and deterministic tool execution
- SQL backed durable persistence with SQLite local support
- provider backed LLM turn execution with execution backend selection
- fake provider and OpenAI compatible provider adapter
- persisted LLM call artifacts, usage, retry metadata, and fallback metadata
- FastAPI endpoints for turns, tool calls, approvals, verifications, outputs, and LLM call inspection
- smoke flows for memory, SQL, and fake LLM execution

### Quality
- strict mypy, Ruff, and pytest coverage
- release check target for local validation
