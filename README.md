# Agent Factory OS

A React + FastAPI + Groq MVP implementing the supplied five-member AI Software Factory architecture.

## Important UI decision
The supplied team brief originally specified Streamlit (`ui/dashboard.py`, `ui/input_form.py`, `ui/output_view.py`).
The requested final UI choice was React, so the UI is in `frontend/`. The Python agent architecture is at the
repository root in the exact shared-module locations: `agents/`, `orchestrator/`, `tools/`, `templates/`,
`integration/`, `tests/`, and `outputs/`. `ui/README.md` documents the mapping.

## Stack
- React + Vite frontend with Tailwind CSS utilities and SCSS component styling
- FastAPI Python entry point (`app.py`)
- Groq SDK for AI-assisted requirements and planning
- Deterministic fallback if `GROQ_API_KEY` is absent or Groq output is unavailable
- Reusable template-based starter project generation
- pytest structural workflow tests

> Honest MVP scope: this creates a reusable starter scaffold and validates its structure. It does not claim
> autonomous production software development and does not execute generated code.

## Run locally

### Backend (Python 3.10+)
From the repository root:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your Groq key:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
CORS_ORIGINS=http://localhost:5173
```

Start backend from the repository root:

```bash
uvicorn app:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend
In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### Tests
From repository root:

```bash
pytest -q
```

## Function contracts
- `agents/requirement_agent.py`: `analyze_requirement(user_prompt) -> dict`
- `agents/planner_agent.py`: `create_plan(requirements) -> dict`
- `agents/builder_agent.py`: `generate_project(plan) -> dict`
- `agents/tester_agent.py`: `test_project(build_result) -> dict`
- `orchestrator/workflow.py`: `run_factory(user_prompt) -> dict` with `requirements`, `plan`, `build`, `tests`

Tester returns `passed` only when all required generated-file checks pass.

## Five-member task division

| Member | Ownership | Files |
|---|---|---|
| 1 — UI/UX | React dashboard | `frontend/src/`, design handoff in `docs/figma_design_spec.md` |
| 2 — Requirements + Planner | Agent logic | `agents/requirement_agent.py`, `agents/planner_agent.py` |
| 3 — Orchestration | Workflow | `orchestrator/workflow.py` |
| 4 — Builder + templates | Generation | `agents/builder_agent.py`, `tools/`, `templates/` |
| 5 — Integration + QA + docs | Integration and delivery | `integration/`, `tests/`, `docs/`, `README.md` |

## GitHub
```bash
git init
git add .
git commit -m "Initial Agent Factory OS MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/agent-factory-os.git
git push -u origin main
```

Do not commit `.env`; it is excluded by `.gitignore`.

## Docs
- `docs/architecture.md` — architecture and module contracts
- `docs/presentation.md` — demo presentation outline
- `docs/figma_design_spec.md` — Figma / Google Stitch-ready design brief
- `docs/ui_preview.html` — static visual preview (if present)
- `docs/architecture.svg` — architecture diagram (if present)
