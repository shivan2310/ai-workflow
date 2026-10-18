# AutoPilot AI — Backend Requirements

## Requirements Matrix

### Authentication & Authorization (AUTH)
- [ ] **AUTH-01**: Backend accepts Supabase Bearer access tokens via HTTP `Authorization` header.
- [ ] **AUTH-02**: Backend independently validates JWT signatures (JWKS asymmetric key verification) with issuer, audience, and expiry checks.
- [ ] **AUTH-03**: Backend extracts stable authenticated Supabase user UUID (`sub`).
- [ ] **AUTH-04**: Backend enforces strict per-user ownership on workflows, tasks, and reports; cross-user requests return 404 Not Found.
- [ ] **AUTH-05**: Frontend-supplied user IDs are never trusted as identity.

### Database & Persistence (DB)
- [ ] **DB-01**: PostgreSQL primary database via SQLAlchemy 2.x ORM models with SQLite test compatibility.
- [ ] **DB-02**: Models defined for `Workflow`, `WorkflowTask`, and `ToolExecution` with UUID PKs and JSON columns.
- [ ] **DB-03**: Alembic migrations track schema versioning cleanly.
- [ ] **DB-04**: Database transactions ensure atomicity for related writes.

### AI Planner (PLAN)
- [ ] **PLAN-01**: Planner connects to cloud-hosted GPT-OSS 120B with configurable base URL, model name, and API key.
- [ ] **PLAN-02**: Planner generates structured DAG plans with task IDs, descriptions, tool names, arguments, and dependencies.
- [ ] **PLAN-03**: Pydantic strictly validates model output, rejecting cycles, missing dependencies, unknown tools, and malformed schemas.
- [ ] **PLAN-04**: Bounded retries handle malformed JSON responses; mocked in tests.

### Deterministic Tools (TOOL)
- [ ] **TOOL-01**: `calculate_budget` computes totals in pure Python `Decimal` arithmetic; reports overruns honestly.
- [ ] **TOOL-02**: `create_tasks` persists task items with user ownership and verifies persistence before returning success.
- [ ] **TOOL-03**: `draft_email` generates structured email draft preview only; never sends email.
- [ ] **TOOL-04**: Tool registry restricts execution strictly to registered tools.

### Orchestration & Verification (ORCH)
- [ ] **ORCH-01**: Orchestrator runs tasks in topological dependency order.
- [ ] **ORCH-02**: State transitions tracked (`queued`, `planning`, `running`, `awaiting_approval`, `completed`, `failed`, `cancelled`).
- [ ] **ORCH-03**: Upstream task failure halts and cascades block to downstream dependent tasks.
- [ ] **ORCH-04**: Verifier audits actual execution outputs before final report generation.

### REST API (API)
- [ ] **API-01**: `GET /api/health` reports status for backend, database, and cloud LLM service.
- [ ] **API-02**: `POST /api/workflows` creates and triggers workflow execution for authenticated user.
- [ ] **API-03**: `GET /api/workflows` lists current user's workflows with pagination.
- [ ] **API-04**: `GET /api/workflows/{id}` returns details of user's workflow; returns 404 for missing/foreign workflows.
- [ ] **API-05**: `GET /api/workflows/{id}/report` returns verified final report.
- [ ] **API-06**: `POST /api/workflows/{id}/cancel` safely cancels queued or running workflow.
- [ ] **API-07**: `GET /api/tasks` returns current user's tasks.
