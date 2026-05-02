# My Novel Assist

AI-powered novel writing assistant with a Dramatica-inspired 7-agent pipeline.

## Architecture

**7-Agent Pipeline:** Planner → Architect → Writer → Auditor → Reviser → Observer → Summary

### Backend (FastAPI)

| Layer | Description |
|---|---|
| `pipeline/` | 7 agent modules + PipelineOrchestrator coordinator |
| `llm/` | 6-provider bank (OpenAI, DeepSeek, Anthropic, Google, Ollama, Custom) |
| `governance/` | ControlPlane (author_intent.md + current_focus.md), WordBudget |
| `schema/` | SchemaRegistry with typed validation cards |
| `context/` | @DSL parser for template injection |
| `memory/` | ChromaDB vector semantic retrieval |
| `validators/` | 33-dim audit, De-AI-fication, PostWrite, QualityMetrics |
| `narrative/` | 16-stage Dramatica story progression engine |
| `state/` | Delta state tracking with checkpoint/rollback |
| `api/` | REST endpoints for projects, chapters, generation |

### Frontend (Vite + React + Tailwind CSS)

Minimal project management UI with chapter generation trigger.

## Getting Started

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # configure API keys
python -m app.run

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Configuration

Set provider API keys in `.env`:

| Key | Provider |
|---|---|
| `OPENAI_API_KEY` | OpenAI / DeepSeek |
| `ANTHROPIC_API_KEY` | Anthropic Claude |
| `GOOGLE_API_KEY` | Google Gemini |

Default provider is `openai`; set `LLM_PROVIDER` to switch.

## License

MIT
