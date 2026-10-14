# AutoPilot AI (InnoTech)

> **A dependable, tool-using AI workflow automation system powered by local LLMs, deterministic verification, and persistent state tracking.**

Built as an MVP for the InnoTech 7-Day Innovation Sprint by a team of 3–4 developers.

---

## 🎯 Project Overview

AutoPilot AI accepts natural-language operational requests, converts them into schema-validated task plans, executes deterministic Python tools in dependency order, enforces strict arithmetic verification, and presents live progress and final reports through an interactive React dashboard.

### 🎪 Primary Demo Scenario
> *"Plan a technical workshop for 100 students with a budget of ₹20,000. Create a budget breakdown, preparation tasks, and an invitation email."*

### 💡 Core Value: Deterministic Reliability
- **Zero-Hallucination Arithmetic:** LLMs propose task plans, but **all calculations, cost summations, and budget limit checks are performed strictly in pure Python**.
- **Allowlisted Deterministic Tools:** Only predefined, schema-validated Python functions can execute. No arbitrary code generation or dynamic execution.
- **Cascading Dependency Safety:** If an upstream prerequisite fails (e.g., budget overrun), dependent tasks are blocked immediately.
- **Auditability & Persistence:** Every state transition, task result, and execution log is stored in SQLite and survives backend restarts.
- **Simulated Side Effects:** Emails are generated as draft previews for user inspection; no external side effects or live dispatch in the MVP.

---

## 🏗️ Architecture & Tech Stack

```
[ React + Vite + Tailwind ] (Port 5173)
            │  REST Polling (every 1-2s)
            ▼
[ FastAPI Backend ] (Port 8000)
    ├── AI Planner (Ollama qwen2.5:3b + Mock Fallback)
    ├── Pydantic Schemas & Validators
    ├── Workflow Orchestrator (State Machine & Dependency Resolver)
    ├── Deterministic Tools (Budget, Tasks, Email Draft)
    └── SQLite Database (SQLAlchemy)
```

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide React |
| **Backend** | Python 3.12+ (FastAPI, Uvicorn, Pydantic v2) |
| **Local LLM** | Ollama running `qwen2.5:3b` (configurable via `OLLAMA_MODEL`) |
| **Storage** | SQLite + SQLAlchemy ORM (`autopilot.db`) |
| **Testing** | Pytest, FastAPI TestClient, HTTPX |

---

## 📂 Repository Structure

```
autopilot-ai/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── RequestForm.tsx         # Natural-language prompt & parameters form
│   │   │   ├── ExecutionTimeline.tsx   # Live stage progress & status indicators
│   │   │   ├── TaskList.tsx            # Task execution grid & status badges
│   │   │   ├── BudgetPanel.tsx         # Verified line-item calculation panel
│   │   │   └── ResultPanel.tsx         # Email draft preview & final report
│   │   ├── api/client.ts               # Typed REST API client
│   │   ├── types/workflow.ts           # Frontend TypeScript interfaces
│   │   ├── App.tsx                     # Main layout & dashboard view
│   │   └── index.css                   # Tailwind styling
│   ├── .env.example
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entrypoint & CORS middleware
│   │   ├── config.py                   # Pydantic BaseSettings environment config
│   │   ├── schemas.py                  # Shared Pydantic data contracts
│   │   ├── api/routes.py               # REST API route handlers
│   │   ├── agent/planner.py            # Ollama client & prompt structuring
│   │   ├── agent/orchestrator.py       # State machine & topological runner
│   │   ├── agent/verifier.py           # Arithmetic & tool result verification
│   │   ├── tools/budget.py             # calculate_budget tool (pure Python math)
│   │   ├── tools/tasks.py              # create_tasks tool (SQLite persistence)
│   │   ├── tools/email.py              # draft_email tool (invitation template)
│   │   └── db/
│   │       ├── database.py             # SQLAlchemy session & engine setup
│   │       └── models.py               # Workflow, Task, and Log models
│   ├── tests/                          # Automated Pytest suite
│   ├── requirements.txt                # Python backend dependencies
│   └── .env.example
├── docs/
│   ├── api-contracts.md                # Frozen REST API schemas
│   └── demo-script.md                  # 3-4 minute presentation walkthrough
├── .planning/                          # GSD development roadmap & specs
├── .gitignore
└── README.md
```

---

## ⚙️ Quickstart & Local Setup

### Prerequisites
- **Git**
- **Python 3.12+** (`py` or `python`)
- **Node.js v20+ & npm**
- **Ollama** installed and running locally

---

### 1. Local LLM Setup (Ollama)
In a dedicated terminal:
```bash
ollama pull qwen2.5:3b
ollama run qwen2.5:3b
```
> *Note: If Ollama is running as a background service, keep it running on `http://localhost:11434`.*

---

### 2. Backend Setup
In a terminal, navigate to the `backend/` directory:
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Start the FastAPI server:
```powershell
uvicorn app.main:app --reload --port 8000
```
- Interactive API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

---

### 3. Frontend Setup
In a separate terminal, navigate to the `frontend/` directory:
```powershell
cd frontend
npm install
npm run dev
```
Open the dashboard in your browser: **`http://localhost:5173`**

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check & Ollama model availability status |
| `POST` | `/api/workflows` | Submits NL request, validates parameters, and enqueues workflow |
| `GET` | `/api/workflows/{id}` | Returns real-time workflow state, tasks, and outputs |
| `GET` | `/api/workflows/{id}/report` | Returns compiled summary report and verified audit data |

### Workflow Status Lifecycle
```
queued ──► planning ──► running ──► completed
                          │
                          ├──► awaiting_approval (pause gate)
                          ├──► failed (explicit error)
                          └──► cancelled
```

---

## 🛠️ The Three Executable Tools

1. **`calculate_budget(items, budget_limit)`**
   - Pure Python arithmetic summing proposed expenses.
   - Validates that line items are non-negative and total is strictly $\le$ `budget_limit`.
   - Returns `{total_calculated, remaining_budget, within_limit: bool}`.
2. **`create_tasks(tasks)`**
   - Validates checklist titles, deadlines, and assigned roles.
   - Persists tasks to SQLite and returns assigned database IDs.
3. **`draft_email(event_details)`**
   - Formats a personalized workshop invitation draft.
   - Saves output as reviewable draft (never transmitted externally).

---

## 📅 Seven-Day Build Plan

- **Day 1: Foundations & API Contracts** — Repo setup, Pydantic schemas, FastAPI skeleton, and initial tests.
- **Day 2: AI Planner & Ollama Integration** — Local inference, structured JSON output, and validation.
- **Day 3: Deterministic Tools & Unit Tests** — Budget calculator, task persister, and email draft generator.
- **Day 4: Workflow Orchestration & Persistence** — Dependency ordering, state machine, and SQLite persistence.
- **Day 5: React Dashboard Integration** — Visual timeline, input form, and result panels. *(Feature Freeze)*
- **Day 6: Reliability & Edge Cases** — Over-budget rejection, timeout guards, and failure testing.
- **Day 7: Rehearsal & Documentation** — Clean startup validation, demo rehearsal, and final presentation.

---

## 🧪 Testing

Run the automated test suite from the `backend/` directory:
```powershell
pytest -v
```

---

## 📜 License & Acknowledgments

Developed as an open-source technical prototype for the **InnoTech** Innovation Challenge.
