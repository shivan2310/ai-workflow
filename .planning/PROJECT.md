# AutoPilot AI (InnoTech)

## What This Is

AutoPilot AI is an agentic AI-powered workflow automation system built as a functional, reliable MVP for an InnoTech innovation project. It takes natural-language requests (such as organizing technical workshops), constructs validated multi-step execution plans, runs deterministic tools in dependency order, enforces strict arithmetic and safety verification, tracks execution state in SQLite, and presents live progress and final reports through an intuitive React dashboard.

## Core Value

Deterministic reliability in agentic execution: natural-language planning coupled with zero-hallucination arithmetic, verified tool execution, strict dependency gating, and persistent auditability.

## Requirements

### Validated

*(None yet — baseline project initialization)*

### Active

- [ ] **PLAN-01**: AI Planner generates structured JSON execution plans from natural language requests.
- [ ] **PLAN-02**: Planner identifies discrete tasks, dependencies, expected outputs, and constraints.
- [ ] **PLAN-03**: All model responses validated strictly against Pydantic schemas.
- [ ] **PLAN-04**: Robust fallback handling for malformed JSON and Ollama server unavailability.
- [ ] **ORCH-01**: Orchestrator executes tasks respecting topological dependency order.
- [ ] **ORCH-02**: Workflow and task lifecycle states tracked (`queued`, `planning`, `running`, `awaiting_approval`, `completed`, `failed`, `cancelled`).
- [ ] **ORCH-03**: Workflow state, task outputs, and execution logs persisted in SQLite via SQLAlchemy.
- [ ] **ORCH-04**: Error handling, safe retries, and cascade blocking of dependent tasks on upstream failure.
- [ ] **TOOL-01**: `calculate_budget` computes totals in Python and checks configured budget ceiling.
- [ ] **TOOL-02**: `create_tasks` persists preparation items, deadlines, and owners into SQLite.
- [ ] **TOOL-03**: `draft_email` renders tailored workshop invitation templates without external dispatch.
- [ ] **SAFE-01**: Pure Python verification for all math (LLM is never trusted for calculations).
- [ ] **SAFE-02**: Approval checkpoint gate before irreversible or simulated external actions.
- [ ] **DASH-01**: Frontend dashboard with natural-language input, budget limit, and attendee count inputs.
- [ ] **DASH-02**: Live execution timeline showing task status progression and execution logs.
- [ ] **DASH-03**: Inspection panels for budget verification breakdown, task table, and rendered email draft.
- [ ] **DASH-04**: Final workflow summary report view and explicit error diagnosis panels.
- [ ] **API-01**: Typed REST endpoints (`GET /api/health`, `POST /api/workflows`, `GET /api/workflows/{id}`, `GET /api/workflows/{id}/report`).

### Out of Scope

- **Paid AI APIs (OpenAI, Anthropic, Gemini Cloud)** — Zero external billing; uses local Ollama or deterministic fallback mock.
- **External Side Effects (Real Email Sending / Payment Gateways)** — Safety constraint for MVP; actions remain simulated/drafted.
- **Multi-Agent Swarm / Vector DB / RAG** — Unnecessary architectural bloat for 7-day MVP delivery.
- **User Authentication / Multi-Tenancy** — Single-operator workstation app for demo and evaluation clarity.
- **Distributed Queues (Celery/Redis/Kafka)** — SQLite + asyncio provides sufficient throughput and zero deployment friction.

## Context

- **Team**: 3–4 developers on a 7-day delivery sprint.
- **Demo Scenario**: "Plan a technical workshop for 100 students with a ₹20,000 budget. Generate a budget breakdown, create preparation tasks, and draft an invitation email."
- **Host Environment**: Windows 11 workstation with Python 3.14 (`py`), Node.js v24, Ollama 0.40.3.

## Constraints

- **Local LLM**: Ollama using `qwen2.5:3b` default (configurable via `OLLAMA_MODEL` env var) with offline fallback.
- **Tech Stack**: FastAPI + Pydantic + SQLAlchemy + SQLite (Backend); React + Vite + TypeScript + Tailwind CSS (Frontend).
- **Zero Hallucination Arithmetic**: Mathematical assertions must be evaluated by Python code, not LLM generations.
- **Testing**: Automated coverage using Pytest and FastAPI TestClient before completing integrations.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SQLite + SQLAlchemy | Zero-configuration single-file database ideal for 7-day delivery and demo portability | 🟢 Good |
| In-Process Async Orchestrator | Avoids Redis/Celery dependency while providing full state-machine control | 🟢 Good |
| Local Ollama + Mock Fallback | Guarantees demos and automated tests succeed even when Ollama is offline | 🟢 Good |
| Strict Pydantic Schemas | Prevents malformed LLM outputs from corrupting workflow execution | 🟢 Good |

---
*Last updated: 2026-10-14 after project initialization*
