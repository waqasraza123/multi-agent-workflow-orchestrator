# Architecture overview

## Purpose

The platform is a backend-first multi-agent execution system that turns a user goal into a persisted run, generates a plan, advances deterministic turns, executes tools, records evidence, verifies completion, and produces a final output.

## Layering

### API layer
FastAPI routes expose the platform workflow and translate application errors into HTTP responses.

### Application layer
The service layer coordinates repositories, state transitions, planning, turns, tools, verification, approvals, and final output synthesis.

### Contracts layer
Contracts define the stable request, response, and domain models used across the platform.

### Orchestration layer
State transition functions own run-state mutation rules for tasks and evidence.

### Planning layer
Planning generates deterministic task sequences from the run goal and workflow type.

### Agent runtime layer
The deterministic runtime advances a task through one turn and proposes tool calls.

### Tools layer
The registry executes deterministic tool adapters and returns structured tool outputs.

### Storage layer
Repositories persist run state, events, approvals, plans, turns, tool calls, verifications, and outputs.
The platform supports both in-memory and SQL-backed implementations behind the same service boundary.

### Config layer
Settings select the storage backend and database URL.

## Current execution flow

1. create run
2. generate plan
3. register tasks
4. advance deterministic turns
5. persist tool calls and evidence
6. verify run
7. finalize output
8. persist terminal completed state

## Current storage modes

- memory
- sql

SQL mode currently targets SQLite locally and keeps a Postgres-ready repository boundary through SQLAlchemy models and sessions.
