# Roadmap: AutoPilot AI (InnoTech)

## Overview

A phased 7-day delivery roadmap to build AutoPilot AI from initial architecture to a polished, demonstrable MVP. Each phase delivers a functional, verifiable vertical layer accompanied by automated tests.

## Phases

- [ ] **Phase 1: Foundations, Schemas & API Contracts (Day 1)** - Python virtual environment, FastAPI skeleton, Pydantic schemas, and typed API endpoints.
- [ ] **Phase 2: AI Planner & Ollama Integration (Day 2)** - Local Ollama connectivity (`qwen2.5:3b`), JSON prompt engineering, Pydantic validation, and graceful mock fallback.
- [ ] **Phase 3: Deterministic Tools & Unit Tests (Day 3)** - Implement `calculate_budget`, `create_tasks`, and `draft_email` with pytest test suites.
- [ ] **Phase 4: Workflow Orchestration & Persistence (Day 4)** - Dependency order execution engine, SQLite persistence with SQLAlchemy, state machine, and log streaming.
- [ ] **Phase 5: React Dashboard Integration (Day 5)** - React + Vite + Tailwind CSS dashboard with request inputs, execution timeline, and inspection panels.
- [ ] **Phase 6: Safety, Failure Handling & End-to-End Tests (Day 6)** - Approval checkpoints, cascade failure blocking, error states, and full workshop scenario tests.
- [ ] **Phase 7: Demo Scenarios, Documentation & Presentation Readiness (Day 7)** - Seeded workshop demo button, automated run scripts, README guide, and demo rehearsal.

## Phase Details

### Phase 1: Foundations, Schemas & API Contracts (Day 1)
**Goal**: Establish project directory structure, dependencies, database setup, Pydantic schemas, and FastAPI endpoints.
**Depends on**: Nothing
**Requirements**: API-01, API-02, API-03, API-04, API-05
**Success Criteria**:
  1. FastAPI server starts cleanly and `GET /api/health` returns status `200 OK` with JSON metadata.
  2. Pydantic request and response schemas for workflows, tasks, and reports are defined and validated.
  3. Skeleton endpoints (`/api/workflows`, `/api/workflows/{id}`, `/api/workflows/{id}/report`) respond with typed mock data.
  4. CORS is configured for `localhost:5173` (Vite frontend).
  5. Initial test suite verifies all base endpoints via FastAPI `TestClient`.
**Plans**: 1 plan
- [ ] 01-01: FastAPI skeleton, Pydantic data models, SQLite connection, and baseline API test suite.

---

### Phase 2: AI Planner & Ollama Integration (Day 2)
**Goal**: Build the planning module that queries local Ollama (`qwen2.5:3b`) to produce structured JSON plans, with deterministic mock fallback when offline.
**Depends on**: Phase 1
**Requirements**: PLAN-01, PLAN-02, PLAN-03, PLAN-04, PLAN-05
**Success Criteria**:
  1. Planner accepts natural-language workshop prompts and produces a structured `TaskPlan`.
  2. Every task specifies an id, tool name, parameters, dependencies, and validation requirements.
  3. Pydantic parses and strictly validates LLM output before passing to execution.
  4. Malformed JSON or connection refusal triggers a clean fallback or retry without application crash.
  5. Unit tests pass for both live LLM responses and mock fallback plans.
**Plans**: 1 plan
- [ ] 02-01: Ollama client wrapper, prompt template, Pydantic parser, error handling, and test fixtures.

---

### Phase 3: Deterministic Tools & Unit Tests (Day 3)
**Goal**: Implement the three required tools with pure Python execution and strict SQLite persistence.
**Depends on**: Phase 2
**Requirements**: TOOL-01, TOOL-02, TOOL-03
**Success Criteria**:
  1. `calculate_budget` computes line-item sums in Python, checks limits, and flags overruns deterministically.
  2. `create_tasks` persists preparation checklist records with deadlines and assignee tags into SQLite.
  3. `draft_email` generates a professional invitation email draft containing event details and schedule.
  4. 100% unit test coverage for tool arithmetic, edge cases (over budget, negative costs), and database records.
**Plans**: 1 plan
- [ ] 03-01: Tool interface, budget calculator, task creator, email draft generator, and pytest suites.

---

### Phase 4: Workflow Orchestration & Persistence (Day 4)
**Goal**: Build the workflow execution state machine with dependency resolution and persistent audit logs.
**Depends on**: Phase 3
**Requirements**: ORCH-01, ORCH-02, ORCH-03, ORCH-04, ORCH-05
**Success Criteria**:
  1. Orchestrator executes tasks in correct topological order based on declared dependencies.
  2. State transitions follow: `queued` -> `planning` -> `running` -> `completed` / `failed`.
  3. Upstream task failure halts dependent tasks without executing them.
  4. Workflow state, task status, outputs, and log entries are saved to SQLite at every transition step.
  5. Automated integration tests verify multi-step task execution and state persistence.
**Plans**: 1 plan
- [ ] 04-01: Orchestration engine, topological dependency runner, database repositories, and execution tests.

---

### Phase 5: React Dashboard Integration (Day 5)
**Goal**: Build the user-facing web dashboard using React, Vite, TypeScript, and Tailwind CSS.
**Depends on**: Phase 4
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04
**Success Criteria**:
  1. User can submit a workshop request with customized budget limit and attendee count.
  2. Live status polling updates the workflow progress timeline in real time.
  3. Interactive UI displays individual task cards, status badges, and execution logs.
  4. Dedicated visual panels show budget breakdown, generated preparation tasks, and email draft preview.
  5. Final report panel renders when workflow reaches terminal state.
**Plans**: 1 plan
- [ ] 05-01: Vite + React setup, Tailwind theme, form inputs, timeline component, output panels, and API hook.

---

### Phase 6: Safety, Approvals & Verification (Day 6)
**Goal**: Enforce deterministic safety gates, human-in-the-loop approval, and edge case resilience.
**Depends on**: Phase 5
**Requirements**: SAFE-01, SAFE-02, SAFE-03, SAFE-04
**Success Criteria**:
  1. Tasks marked as requiring approval pause workflow in `awaiting_approval` state.
  2. User can approve or reject the action directly via API and Frontend button.
  3. Arithmetic from LLM is strictly ignored in favor of verified Python calculations.
  4. End-to-end integration tests pass for the full workshop scenario (100 students, ₹20,000 budget).
  5. Edge cases (budget overrun, model timeout, cancelled workflow) render gracefully without crashing.
**Plans**: 1 plan
- [ ] 06-01: Approval gate mechanism, arithmetic safety validator, and comprehensive end-to-end test suite.

---

### Phase 7: Demo Scenarios, Documentation & Presentation Readiness (Day 7)
**Goal**: Prepare the project for final demo, review, and team handover.
**Depends on**: Phase 6
**Requirements**: All validated
**Success Criteria**:
  1. Single-command startup scripts (`run.ps1` and `run.sh`) launch both backend and frontend.
  2. One-click "Load InnoTech Workshop Demo" button pre-fills the ₹20,000 / 100 students scenario.
  3. Clear documentation in `README.md` covering prerequisites, architecture, API reference, and testing.
  4. Verification checklist completed and ready for presentation.
**Plans**: 1 plan
- [ ] 07-01: One-click demo fixtures, startup scripts, README documentation, and final audit.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundations, Schemas & API Contracts | 0/1 | Not started | - |
| 2. AI Planner & Ollama Integration | 0/1 | Not started | - |
| 3. Deterministic Tools & Unit Tests | 0/1 | Not started | - |
| 4. Workflow Orchestration & Persistence | 0/1 | Not started | - |
| 5. React Dashboard Integration | 0/1 | Not started | - |
| 6. Safety, Approvals & Verification | 0/1 | Not started | - |
| 7. Demo Scenarios & Readiness | 0/1 | Not started | - |
