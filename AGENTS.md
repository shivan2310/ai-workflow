<!-- GSD:project-start source:PROJECT.md -->
## Project

**AutoPilot AI (InnoTech)**

AutoPilot AI is an agentic AI-powered workflow automation system built as a functional, reliable MVP for an InnoTech innovation project. It takes natural-language requests (such as organizing technical workshops), constructs validated multi-step execution plans, runs deterministic tools in dependency order, enforces strict arithmetic and safety verification, tracks execution state in SQLite, and presents live progress and final reports through an intuitive React dashboard.

**Core Value:** Deterministic reliability in agentic execution: natural-language planning coupled with zero-hallucination arithmetic, verified tool execution, strict dependency gating, and persistent auditability.

### Constraints

- **Local LLM**: Ollama using `qwen2.5:3b` default (configurable via `OLLAMA_MODEL` env var) with offline fallback.
- **Tech Stack**: FastAPI + Pydantic + SQLAlchemy + SQLite (Backend); React + Vite + TypeScript + Tailwind CSS (Frontend).
- **Zero Hallucination Arithmetic**: Mathematical assertions must be evaluated by Python code, not LLM generations.
- **Testing**: Automated coverage using Pytest and FastAPI TestClient before completing integrations.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->
## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
