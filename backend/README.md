# AutoPilot AI — Backend API & Integration Guide

AutoPilot AI is an account-based Agentic AI Workflow Automation Backend. It translates natural-language operational requests into schema-validated DAG execution plans, executes allowlisted deterministic tools in dependency order, verifies mathematical computations using pure Python `Decimal` logic, enforces per-user multi-tenant isolation via Supabase Auth, persists all execution records in PostgreSQL via SQLAlchemy 2.x and Alembic, and provides real-time polling REST endpoints for frontend dashboards.

---

## 1. Technology Stack

- **Runtime:** Python 3.11+
- **API Framework:** FastAPI 0.110+
- **Data Validation:** Pydantic v2
- **Authentication:** Supabase Auth (Asymmetric JWKS JWT verification)
- **Primary Database:** PostgreSQL via Supabase (or local PostgreSQL)
- **ORM:** SQLAlchemy 2.x
- **Schema Migrations:** Alembic
- **AI Inference:** Cloud-hosted GPT-OSS 120B (configurable API endpoint, credentials, and model name)
- **HTTP Client:** HTTPX
- **Testing:** Pytest & FastAPI TestClient (with SQLite support for isolated tests)

---

## 2. Directory Layout

```text
backend/
├── .planning/               # Backend GSD planning artifacts & specifications
│   ├── PROJECT.md
│   ├── REQUIREMENTS.md
│   ├── ROADMAP.md
│   └── STATE.md
├── alembic/                 # Alembic database migration scripts
│   ├── env.py
│   └── versions/
│       └── 8f9eacd44526_initial_schema.py
├── app/
│   ├── main.py              # FastAPI app initialization, CORS, exception handlers
│   ├── core/
│   │   ├── config.py        # Pydantic BaseSettings environment configuration
│   │   ├── security.py      # Supabase JWKS JWT validation & user UUID extraction
│   │   └── exceptions.py    # Standardized application exception hierarchy
│   ├── api/
│   │   ├── dependencies.py  # Auth (get_current_user) & DB session dependencies
│   │   └── routes/
│   │       ├── health.py    # Public health check endpoint
│   │       ├── workflows.py # Workflow lifecycle CRUD & report endpoints
│   │       └── tasks.py     # User-owned task listing endpoint
│   ├── schemas/
│   │   ├── auth.py          # Authenticated user schema
│   │   ├── workflow.py      # Workflow request/response Pydantic models
│   │   ├── plan.py          # DAG plan schema with cycle detection & tool verification
│   │   └── tools.py         # Tool input/output Pydantic schemas
│   ├── services/
│   │   ├── planner.py       # CloudPlannerService (GPT-OSS 120B integration)
│   │   ├── orchestrator.py  # Topological DAG execution engine & state machine
│   │   ├── verifier.py      # ResultVerifier (zero-hallucination math audit)
│   │   └── report_service.py# Final verified report synthesis
│   ├── tools/
│   │   ├── registry.py      # Central allowlisted tool registry
│   │   ├── budget.py        # calculate_budget (Python Decimal arithmetic)
│   │   ├── tasks.py         # create_tasks (DB persistence under user ownership)
│   │   └── email_drafter.py # draft_email (draft-only template preview)
│   └── db/
│       ├── database.py      # Engine, SessionLocal, Base
│       ├── models.py        # Workflow, WorkflowTask, ToolExecution SQLAlchemy models
│       └── repositories.py  # User-isolated repositories (Workflow, Task, Execution)
├── tests/                   # 40 automated pytest unit & integration tests
│   ├── test_api_routes.py
│   ├── test_auth.py
│   ├── test_config.py
│   ├── test_db_repositories.py
│   ├── test_orchestrator.py
│   ├── test_planner.py
│   └── test_tools.py
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

---

## 3. Quick Start & Setup

### 3.1 Prerequisites
- Python 3.11+
- Virtual environment tool (`uv` recommended, or standard `python -m venv`)

### 3.2 Installation

```bash
# Navigate to backend directory
cd backend

# Create virtual environment with Python 3.11
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3.3 Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure your parameters in `.env`:

```env
APP_ENV=development
APP_NAME=AutoPilot AI
API_PREFIX=/api

# Database: PostgreSQL (Supabase) or SQLite for local dev
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/autopilot

# Supabase Auth
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWKS_URL=https://your-project.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_JWT_ISSUER=https://your-project.supabase.co/auth/v1
SUPABASE_JWT_AUDIENCE=authenticated
SUPABASE_JWT_SECRET=

# Cloud LLM: GPT-OSS 120B
LLM_PROVIDER=cloud
LLM_API_BASE_URL=https://api.cloud-provider.com/v1
LLM_API_KEY=your_cloud_api_key_here
LLM_MODEL=gpt-oss-120b
LLM_TIMEOUT_SECONDS=60
MAX_PLANNER_RETRIES=2

# Frontend Origin for CORS
FRONTEND_ORIGIN=http://localhost:5173
```

*(Note: If `LLM_API_KEY` is omitted or set to test mode, the system automatically uses a deterministic workshop fallback plan, enabling full offline development and demos.)*

### 3.4 Database Migrations

Run Alembic migrations to create tables in PostgreSQL:

```bash
alembic upgrade head
```

### 3.5 Running the Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive Swagger UI documentation is available at `http://localhost:8000/docs`.

---

## 4. Frontend Integration Guide

The frontend communicates with the backend via standard REST calls using the Bearer token issued by Supabase Auth upon user login.

### Authentication Header Requirement

Include the Supabase access token in all protected requests:

```http
Authorization: Bearer <supabase_access_token>
```

---

### Endpoints Overview

#### 1. `GET /api/health` (Public)
Checks backend status, database connectivity, and cloud LLM configuration status.

**Response `200 OK`:**
```json
{
  "status": "healthy",
  "timestamp": "2026-10-18T16:00:00Z",
  "database": {
    "connected": true,
    "dialect": "postgresql"
  },
  "llm": {
    "provider": "cloud",
    "model": "gpt-oss-120b",
    "configured": true
  }
}
```

---

#### 2. `POST /api/workflows` (Protected)
Submits a natural-language operational request (e.g. workshop organization). Initiates background execution.

**Request Body:**
```json
{
  "request": "Organize a technical workshop for 100 students within ₹20,000",
  "budget_limit": 20000.00
}
```

**Response `201 Created`:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "original_request": "Organize a technical workshop for 100 students within ₹20,000",
  "budget_limit": 20000.00,
  "status": "queued",
  "created_at": "2026-10-18T16:01:00Z",
  "completed_at": null
}
```

---

#### 3. `GET /api/workflows` (Protected)
Lists the authenticated user's submitted workflows with pagination, ordered newest first.

**Query Parameters:**
- `skip`: Number of records to skip (default `0`).
- `limit`: Number of records to return (default `20`, max `100`).

**Response `200 OK`:**
```json
{
  "items": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "original_request": "Organize a technical workshop for 100 students within ₹20,000",
      "budget_limit": 20000.00,
      "status": "completed",
      "created_at": "2026-10-18T16:01:00Z",
      "completed_at": "2026-10-18T16:01:45Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

---

#### 4. `GET /api/workflows/{workflow_id}` (Protected)
Retrieves live execution status, generated DAG plan, and task status progression for polling (recommended interval: 1–2 seconds).

**Workflow Status Lifecycle:**
`queued` $\to$ `planning` $\to$ `running` $\to$ `completed` / `failed` / `cancelled`

**Response `200 OK`:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "original_request": "Organize a technical workshop for 100 students within ₹20,000",
  "budget_limit": 20000.00,
  "status": "running",
  "plan": {
    "goal": "Organize Technical Workshop: ...",
    "tasks": [
      {
        "task_key": "task_1",
        "description": "Calculate itemized budget",
        "tool_name": "calculate_budget",
        "arguments": {"items": [...], "budget_limit": 20000},
        "dependencies": []
      }
    ]
  },
  "tasks": [
    {
      "id": "c1f7b822-...",
      "task_key": "task_1",
      "description": "Calculate itemized budget",
      "tool_name": "calculate_budget",
      "status": "completed",
      "result": {
        "total_estimated_cost": 18000.00,
        "budget_limit": 20000.00,
        "remaining_amount": 2000.00,
        "overrun_amount": 0.00,
        "is_within_budget": true
      },
      "error_message": null,
      "started_at": "2026-10-18T16:01:05Z",
      "completed_at": "2026-10-18T16:01:06Z"
    }
  ],
  "error_message": null,
  "created_at": "2026-10-18T16:01:00Z",
  "updated_at": "2026-10-18T16:01:06Z",
  "completed_at": null
}
```

---

#### 5. `GET /api/workflows/{workflow_id}/report` (Protected)
Retrieves the final verified outcome report when the workflow reaches terminal state (`completed` or `failed`).

**Response `200 OK`:**
```json
{
  "workflow_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "completed",
  "original_request": "Organize a technical workshop for 100 students within ₹20,000",
  "budget_limit": 20000.00,
  "summary": {
    "total_tasks": 3,
    "completed_tasks": 3,
    "failed_tasks": 0,
    "blocked_tasks": 0,
    "cancelled_tasks": 0,
    "checklist_items_persisted": 3
  },
  "outcome": "success",
  "budget_verification": {
    "verified_by": "python_deterministic_engine",
    "total_cost": 18000.00,
    "budget_limit": 20000.00,
    "remaining_amount": 2000.00,
    "overrun_amount": 0.00,
    "is_within_budget": true
  },
  "tasks_persisted": 3,
  "email_draft": {
    "subject": "Invitation: Hands-on Workshop: Agentic AI Systems",
    "is_draft_only": true,
    "missing_information": ["Speaker / Facilitator"],
    "status": "draft_created_not_dispatched"
  },
  "executed_tasks": [...],
  "completed_at": "2026-10-18T16:01:45Z"
}
```

*Note: If called while workflow is still `planning` or `running`, returns HTTP `409 Conflict` (`Workflow report is not ready`).*

---

#### 6. `POST /api/workflows/{workflow_id}/cancel` (Protected)
Cancels a queued or running workflow. Unexecuted tasks transition to `cancelled`; completed tasks retain their persisted outputs.

---

#### 7. `GET /api/tasks` (Protected)
Lists all tasks (both plan execution tasks and generated checklist items) owned by the current user across workflows.

---

## 5. Automated Testing

Run the full pytest suite:

```bash
pytest
```

Running tests outputs:
```text
======================== 40 passed in 1.35s ========================
```

The test suite covers:
- JWT asymmetric JWKS and secret key verification.
- User ownership and cross-user resource protection (404 isolation).
- Zero-hallucination `Decimal` arithmetic and budget overrun detection.
- Task persistence in SQLite/PostgreSQL.
- Email template drafting and missing detail flags.
- DAG validation, topological sorting, and cycle detection.
- Bounded cloud LLM retries and mock fallback handling.
- Cascading prerequisite failure blocking.
- Real-time status transitions and final report synthesis.
- REST API endpoint response codes and schemas.
