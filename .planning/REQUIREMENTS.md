# Requirements: AutoPilot AI (InnoTech)

**Defined:** 2026-10-14  
**Core Value:** Deterministic reliability in agentic execution: natural-language planning coupled with zero-hallucination arithmetic, verified tool execution, strict dependency gating, and persistent auditability.

## v1 Requirements

### 1. API & Application Foundation (API)

- [ ] **API-01**: Server exposes `GET /api/health` returning system and Ollama status.
- [ ] **API-02**: Server exposes `POST /api/workflows` to accept natural language prompts with budget and attendee limits.
- [ ] **API-03**: Server exposes `GET /api/workflows/{workflow_id}` returning current state, plan, and task details.
- [ ] **API-04**: Server exposes `GET /api/workflows/{workflow_id}/report` returning compiled summary and outputs.
- [ ] **API-05**: CORS configuration restricts access to the development frontend.

### 2. AI Planning Engine (PLAN)

- [ ] **PLAN-01**: Converts natural language requests into structured JSON execution plans.
- [ ] **PLAN-02**: Identifies required tools, input arguments, dependencies between tasks, and constraints.
- [ ] **PLAN-03**: Validates generated plan against strict Pydantic schemas (`TaskPlan`, `PlannedTask`).
- [ ] **PLAN-04**: Handles malformed LLM responses via retry prompts or deterministic fallback.
- [ ] **PLAN-05**: Gracefully handles Ollama unavailability with clear error reporting and mock demonstration mode.

### 3. Deterministic Tools (TOOL)

- [ ] **TOOL-01**: `calculate_budget` calculates line-item totals and detects budget overrun against configured ceilings.
- [ ] **TOOL-02**: `create_tasks` stores preparation checklist items, deadlines, and roles in SQLite.
- [ ] **TOOL-03**: `draft_email` produces a structured invitation email draft with recipient and schedule context.

### 4. Workflow Orchestration & Persistence (ORCH)

- [ ] **ORCH-01**: Executes workflow tasks in correct topological dependency order.
- [ ] **ORCH-02**: Tracks lifecycle states: `queued`, `planning`, `running`, `awaiting_approval`, `completed`, `failed`, `cancelled`.
- [ ] **ORCH-03**: Persists workflow runs, task records, and execution log events in SQLite database via SQLAlchemy.
- [ ] **ORCH-04**: Blocks execution of downstream tasks when an upstream prerequisite task fails.
- [ ] **ORCH-05**: Provides safe error capture and execution logs for each task step.

### 5. Verification & Safety Guards (SAFE)

- [ ] **SAFE-01**: Enforces deterministic Python verification for arithmetic (zero trust for LLM math).
- [ ] **SAFE-02**: Enforces task result verification before updating task status to `completed`.
- [ ] **SAFE-03**: Implements approval checkpoint before external or irreversible actions (`awaiting_approval`).
- [ ] **SAFE-04**: Zero external side effects in MVP (emails drafted, never sent; no real financial charges).

### 6. Frontend Dashboard (DASH)

- [ ] **DASH-01**: Input form with natural-language prompt textarea, attendee count, and budget limit fields.
- [ ] **DASH-02**: Workflow execution timeline displaying task states and status badges in real-time.
- [ ] **DASH-03**: Interactive panels for budget verification breakdown, task list table, and email draft preview.
- [ ] **DASH-04**: Final report modal/view and comprehensive error diagnostic alerts.

## v2 Requirements (Deferred)

- **V2-01**: Multi-model routing (switch between local Ollama, cloud models, or specialized fine-tunes).
- **V2-02**: Real SMTP email delivery with authenticated credentials.
- **V2-03**: Interactive plan editing in UI before execution starts.
- **V2-04**: Multi-user authentication, workspaces, and team role-based permissions.
- **V2-05**: External tool plugins (Google Calendar, Notion, Slack notifications).

## Out of Scope

| Feature | Reason |
|---------|--------|
| Paid Cloud LLM APIs | Strict InnoTech MVP requirement to use local/free stack |
| Real Financial Transactions | Dangerous for demo/testing; budget calculation is simulated |
| Live Email Dispatch | Avoid accidental spam; draft generation satisfies workflow verification |
| Vector DB / RAG Pipeline | Unnecessary complexity for structured planning & tool execution |
| Distributed Celery/Redis Workers | Single workstation deployment using SQLite + async is zero-friction |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| API-01 | Phase 1: Foundations & API Contracts | Pending |
| API-02 | Phase 1: Foundations & API Contracts | Pending |
| API-03 | Phase 1: Foundations & API Contracts | Pending |
| API-04 | Phase 1: Foundations & API Contracts | Pending |
| API-05 | Phase 1: Foundations & API Contracts | Pending |
| PLAN-01 | Phase 2: AI Planner & Ollama Integration | Pending |
| PLAN-02 | Phase 2: AI Planner & Ollama Integration | Pending |
| PLAN-03 | Phase 2: AI Planner & Ollama Integration | Pending |
| PLAN-04 | Phase 2: AI Planner & Ollama Integration | Pending |
| PLAN-05 | Phase 2: AI Planner & Ollama Integration | Pending |
| TOOL-01 | Phase 3: Deterministic Tools & Unit Tests | Pending |
| TOOL-02 | Phase 3: Deterministic Tools & Unit Tests | Pending |
| TOOL-03 | Phase 3: Deterministic Tools & Unit Tests | Pending |
| ORCH-01 | Phase 4: Workflow Orchestration & Persistence | Pending |
| ORCH-02 | Phase 4: Workflow Orchestration & Persistence | Pending |
| ORCH-03 | Phase 4: Workflow Orchestration & Persistence | Pending |
| ORCH-04 | Phase 4: Workflow Orchestration & Persistence | Pending |
| ORCH-05 | Phase 4: Workflow Orchestration & Persistence | Pending |
| DASH-01 | Phase 5: React Frontend Dashboard | Pending |
| DASH-02 | Phase 5: React Frontend Dashboard | Pending |
| DASH-03 | Phase 5: React Frontend Dashboard | Pending |
| DASH-04 | Phase 5: React Frontend Dashboard | Pending |
| SAFE-01 | Phase 6: Safety, Approvals & Verification | Pending |
| SAFE-02 | Phase 6: Safety, Approvals & Verification | Pending |
| SAFE-03 | Phase 6: Safety, Approvals & Verification | Pending |
| SAFE-04 | Phase 6: Safety, Approvals & Verification | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0 🎯

---
*Requirements defined: 2026-10-14*
