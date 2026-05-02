# My Novel Assist

AI-powered novel writing assistant with a Dramatica-inspired 7-agent pipeline.

## Quick Start

```bash
cd backend
pip install -r requirements.txt

# Run the full feature demo (no API key needed):
python -m app.cli demo

# Start the API server:
python -m app.cli server
```

## CLI Usage

The CLI is the primary way to interact with all features. Run from `backend/`:

| Command | What it does |
|---|---|
| `demo` | Run full demo of ALL features |
| `server` | Start FastAPI server |
| `audit <text>` | 33-dimension quality audit |
| `de-ai <text>` | Detect AI writing patterns |
| `validate <text>` | Post-write validation |
| `quality -c 0.8 -i 0.7 -p 0.6` | Calculate quality metrics |
| `narrative` | Show 16-stage story progression |
| `providers` | List 6 LLM providers |
| `schema validate <name> -d '{}'` | Validate data against schema |
| `dsl <template>` | Parse @DSL syntax |
| `state` | State delta tracking demo |
| `api health` | Quick API call to running server |

Examples:

```bash
# Audit text for quality issues
python -m app.cli audit "突然间，全场震惊。然而..."

# Check AI writing score
python -m app.cli de-ai "首先，让我们探讨这个问题..."

# Validate story schema
python -m app.cli schema validate --name story_premise --data '{"title":"My Story","genre":"Fantasy"}'

# Calculate quality
python -m app.cli quality --coherence 0.85 --integration 0.72 --polish 0.68

# Parse @DSL template
python -m app.cli dsl "@title and @type:character"
```

## Architecture

**7-Agent Pipeline:** Planner → Architect → Writer → Auditor → Reviser → Observer → Summary

| Module | Description |
|---|---|
| `pipeline/` | 7-agent pipeline + coordinator |
| `llm/` | 6-provider bank (OpenAI, DeepSeek, Anthropic, Google, Ollama, Custom) |
| `validators/` | 33-dim audit, De-AI-fication, PostWrite, QualityMetrics |
| `narrative/` | 16-stage Dramatica story engine |
| `schema/` | Schema validation cards |
| `context/` | @DSL parser for template injection |
| `memory/` | ChromaDB vector retrieval |
| `state/` | Delta tracking with checkpoint/rollback |
| `governance/` | ControlPlane + WordBudget |
| `api/` | FastAPI REST endpoints |

## Web UI (Streamlit — No Build Needed)

```bash
cd backend
pip install streamlit
streamlit run app/ui.py
```

9-tab dashboard at **http://localhost:8501** — Story Setup, Audit, De-AI, Validate, Quality, Narrative, DSL, Providers, State.

No API server, no frontend build, no separate process needed.

## React Frontend

```bash
cd frontend
npm install
npm run dev
```

Minimal React UI at http://localhost:5173.

## Configuration

```bash
cp .env.example .env
```

| Key | Provider |
|---|---|
| `OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic Claude |
| `DEEPSEEK_API_KEY` | DeepSeek |
| `GOOGLE_API_KEY` | Google Gemini |
| `LLM_PROVIDER` | Set to: openai, deepseek, anthropic, google, ollama, custom |

## Usage Guide

For a complete walkthrough with a real case study (from idea to novel), see:

➡ **[docs/usage-guide.md](docs/usage-guide.md)**

## License

MIT
