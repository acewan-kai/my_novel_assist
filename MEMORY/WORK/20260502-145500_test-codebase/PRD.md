---
task: Test if codebase runs correctly
slug: 20260502-145500_test-codebase
effort: Advanced
phase: learn
progress: 30/30
mode: algorithm
started: 2026-05-02T14:55:00+08:00
updated: 2026-05-02T15:30:00+08:00
---

## Context

The user asks "代码能运行起来吗？你测试一下" — verify the 63-file codebase actually runs.

**Fixes applied during testing:**
- `run.py`: `settings.host` → `settings.app_host`, `settings.port` → `settings.app_port` (field name mismatch)
- `generation.py`: `PipelineOrchestrator.__init__()` doesn't take `provider` — rebuilt endpoint with proper agent registration pattern. Also fixed `result.success` → `result.passed` 
- `narrative/engine.py`: `advance()` recorded stage after incrementing, skipping "setup". Fixed by recording before advancing.

## Criteria

### Installation
- [x] ISC-1: Backend pip install completes without errors
- [x] ISC-2: Frontend npm install completes without errors

### Import Check
- [x] ISC-3: LLM module (base, provider_bank, openai_compat) imports correctly
- [x] ISC-4: Pipeline module (all 11 submodules) imports correctly
- [x] ISC-5: Governance/schema/context/memory modules import correctly
- [x] ISC-6: Validator modules (all 4) import correctly
- [x] ISC-7: Types/state/narrative modules import correctly
- [x] ISC-8: API modules and main.py import correctly

### Server Startup
- [x] ISC-9: FastAPI server starts on port 8000 without error
- [x] ISC-10: Health endpoint returns 200 with {"status": "ok"}

### Projects API
- [x] ISC-11: POST /api/projects creates a project
- [x] ISC-12: GET /api/projects lists projects
- [x] ISC-13: GET /api/projects/{id} returns project by id
- [x] ISC-14: DELETE /api/projects/{id} removes project

### Chapters API
- [x] ISC-15: POST .../chapters creates a chapter
- [x] ISC-16: GET .../chapters lists chapters
- [x] ISC-17: GET .../chapters/{n} returns chapter by number
- [x] ISC-18: PUT .../chapters/{n}/content updates chapter content

### Generation API
- [x] ISC-19: POST /api/generate/chapter returns proper error without LLM configured

### Validators
- [x] ISC-20: QualityMetrics computation correct (coherence/integration/polish/overall)
- [x] ISC-21: Audit33Validator detects fatigue words and forbidden patterns
- [x] ISC-22: DeAIFilter detects LLM patterns and reports score
- [x] ISC-23: PostWriteValidator validates word count and content quality

### Core Modules
- [x] ISC-24: PipelineOrchestrator instantiates without error
- [x] ISC-25: NarrativeEngine produces correct 16-stage progression
- [x] ISC-26: StateDelta record/checkpoint/rollback work correctly
- [x] ISC-27: Config loads default values without .env file
- [x] ISC-28: DSLParser correctly parses @title @type @special syntax
- [x] ISC-29: SchemaRegistry validates known schemas (story_premise, character, chapter)

### Frontend Build
- [x] ISC-30: Frontend `npm run build` completes without TypeScript or bundler errors

## Decisions

1. **run.py field names**: Settings uses `app_host`/`app_port` not `host`/`port` — fixed to match.
2. **generation.py architecture**: PipelineOrchestrator uses `register()` pattern, not constructor injection. Generation endpoint now builds all 7 agents, registers them, runs with AgentContext.
3. **NarrativeEngine semantics**: `advance()` records current stage, increments, returns new stage. Test corrected for this semantic.

## Verification

- ISC-1: pip install completed, all 15 packages resolved (chromadb 1.5.8 etc.)
- ISC-2: npm install added 201 packages in 9s
- ISC-3 through ISC-8: All import tests passed sequentially
- ISC-9: uvicorn started on 0.0.0.0:8000
- ISC-10: curl GET /api/health → {"status":"ok","version":"0.2.0"}
- ISC-11: POST → {"id":"5867edfa","title":"Test Novel",...}
- ISC-12 through ISC-14: All CRUD operations returned 200
- ISC-15 through ISC-18: Chapter CRUD all returned correct data, including word_count update
- ISC-19: Pipeline ran 6 phases, each returned OpenAI 401 error (no API key) — correct graceful failure
- ISC-20 through ISC-23: All validators produced correct results with test data
- ISC-24: PipelineOrchestrator instantiated and register() worked
- ISC-25: All 16 stages advanced correctly, get_required_beats returns correct stages per chapter ratio
- ISC-26: DeltaStore record/checkpoint/rollback/clear all verified
- ISC-27: Settings loaded with defaults, host="0.0.0.0", port=8000, api_key empty
- ISC-28: DSLParser produced 3 matches with correct types; ContextInjector replaced @title
- ISC-29: SchemaRegistry correctly validated/invalidated schemas based on required fields
- ISC-30: `npm run build` → tsc passed, vite built 81 modules in 1.19s
