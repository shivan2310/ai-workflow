# AutoPilot AI — Backend

## Project Overview

AutoPilot AI is an account-based Agentic AI Workflow Automation Platform. It accepts natural-language operational requests (such as organizing technical workshops), uses a cloud-hosted LLM (GPT-OSS 120B) to construct validated multi-step execution plans, executes deterministic allowlisted Python tools in dependency order, enforces strict arithmetic verification, isolates data per authenticated user via Supabase Auth, persists state in PostgreSQL/Supabase via SQLAlchemy 2.x and Alembic, and exposes typed REST endpoints to a React + TypeScript frontend.

## Core Value

Deterministic reliability in agentic execution: natural-language planning coupled with zero-hallucination arithmetic, verified tool execution, strict dependency gating, per-user data isolation, and persistent auditability.

## Technology Stack

- **Language:** Python 3.11+
- **API Framework:** FastAPI
- **Data Validation:** Pydantic v2
- **Authentication:** Supabase Auth (JWT bearer verification via JWKS)
- **Primary Database:** PostgreSQL via Supabase (SQLAlchemy 2.x ORM)
- **Migrations:** Alembic
- **AI Inference:** Cloud-hosted GPT-OSS 120B (configurable API endpoint, model name, and credentials)
- **HTTP Client:** HTTPX
- **Testing:** Pytest & FastAPI TestClient (with isolated SQLite support for tests)
- **Server:** Uvicorn
