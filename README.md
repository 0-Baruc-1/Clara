# Clara

Clara is a multi-agent teaching copilot for teachers in Latin America, starting with the Chilean national curriculum. A teacher describes a class in plain language and Clara will produce an editable, coherent teaching pack: a lesson plan, activity guide, and assessment with rubric.

## Agent architecture

All agents are designed to use GPT-5.6 through the configurable `gpt-5.6-terra` model ID. They will share a stable, cached system-context prefix containing common pedagogy instructions and verified curriculum context.

1. **Planner** maps a lesson request to curriculum objectives and a structured plan.
2. **Designer** creates activities from that plan.
3. **Assessment** creates an aligned assessment and rubric.
4. **Reviewer** checks the three artifacts for consistency before returning them.

The current `/generate` endpoint returns typed placeholder data. Agent classes and the OpenAI client seam are scaffolded and intentionally marked `TODO` for the next feature iteration.

## Run locally

Prerequisites: Python 3.11+ and Node.js 20+.

```powershell
# Terminal 1 — API
cd backend
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```powershell
# Terminal 2 — web app
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open the URL Vite prints (normally `http://localhost:5173`). The API is available at `http://localhost:8000`; interactive API docs are at `/docs`.

## Environment variables

`backend/.env` (not committed):

```dotenv
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.6-terra
FRONTEND_ORIGIN=http://localhost:5173
```

`frontend/.env` (optional):

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

## How Codex built this

_To be completed as Clara evolves._

