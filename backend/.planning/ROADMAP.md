# AutoPilot AI — Backend Roadmap

## Phases

- [ ] **Phase 1: Project Setup, Dependencies & Configuration** — Virtual environment, `requirements.txt`, `.env.example`, `.gitignore`, `config.py`, exceptions.
- [ ] **Phase 2: Database Models, Repositories & Alembic Migrations** — SQLAlchemy 2.x models, repositories, and Alembic setup.
- [ ] **Phase 3: Supabase Authentication & Multi-Tenant Isolation** — JWT verification (JWKS / HMAC), dependencies, and ownership tests.
- [ ] **Phase 4: Tool Registry & Deterministic Tools** — `calculate_budget`, `create_tasks`, `draft_email`, and unit tests.
- [ ] **Phase 5: Cloud LLM Planner Service (GPT-OSS 120B)** — DAG plan schemas, prompt engineering, JSON validation, retry handling, and mocks.
- [ ] **Phase 6: Workflow Orchestrator, Verifier & State Machine** — Topological execution, cascading failure blocks, result verification, and report synthesis.
- [ ] **Phase 7: REST API Endpoints & Request Lifecycles** — FastAPI routers for health, workflows, tasks, reports, and error handling.
- [ ] **Phase 8: Comprehensive Verification & Integration Guide** — Full pytest test suite, `backend/README.md` frontend integration guide.
