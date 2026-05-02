"""My Novel Assist CLI — explore all features from the terminal."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="My Novel Assist - AI-powered novel writing assistant")
console = Console()


# ─── Demo: run everything ──────────────────────────────────────────────

@app.command()
def demo():
    """Run a full demonstration of ALL features."""
    console.print(Panel.fit(
        "[bold]My Novel Assist - Feature Demo[/bold]\n"
        "Running all modules to show what this project can do.",
        border_style="green"
    ))

    # 1. Providers
    console.print("\n[yellow]> 1/9  Provider Bank[/yellow]")
    from ..llm.provider_bank import PROVIDER_BANK
    for name, info in PROVIDER_BANK.items():
        console.print(f"   + {info.name}: {info.base_url or '(local)'} ({len(info.models)} models)")

    # 2. Quality Metrics
    console.print("\n[yellow]> 2/9  Quality Metrics[/yellow]")
    from ..validators.metrics import QualityMetrics
    qm = QualityMetrics(coherence=0.85, integration=0.72, polish=0.68)
    console.print(f"   Coherence={qm.coherence}, Integration={qm.integration}, Polish={qm.polish}")
    console.print(f"   Overall={qm.overall:.2f}, Passed={qm.passed}")
    console.print(f"   Dict: {qm.to_dict()}")

    # 3. Audit33
    console.print("\n[yellow]> 3/9  33-Dimension Audit[/yellow]")
    from ..validators.audit_33 import Audit33Validator
    auditor = Audit33Validator()
    sample = "突然间，全场震惊。然而，他不由得感到一阵寒意。仿佛世界在旋转。"
    result = auditor.audit(sample)
    console.print(f"   Input: {sample}")
    console.print(f"   Issues: {len(result.issues)}, Overall: {result.overall:.2f}, Passed: {result.passed}")
    for i in result.issues:
        console.print(f"   ! [{i.severity}] {i.dimension}: {i.message}")

    # 4. De-AI
    console.print("\n[yellow]> 4/9  De-AI-fication[/yellow]")
    from ..validators.de_ai import DeAIFilter
    deai = DeAIFilter()
    ai_text = "首先，让我们探讨这个问题。其次，我们需要分析数据。最后，值得注意的是结论。"
    r = deai.analyze(ai_text)
    console.print(f"   Input: {ai_text}")
    console.print(f"   AI Score: {r.ai_score:.2f}, Passes: {r.passes}")
    for i in r.issues:
        console.print(f"   * {i.pattern}: {i.severity} {i.suggestion}")

    # 5. Post-Write Validation
    console.print("\n[yellow]> 5/9  Post-Write Validation[/yellow]")
    from ..validators.post_write import PostWriteValidator
    pv = PostWriteValidator(min_words=5)
    r = pv.validate("Hello world. This is a test with enough words.")
    console.print(f"   Word count: {r.metrics.get('word_count', 0)}, Passed: {r.passed}")
    r2 = pv.validate("")
    console.print(f"   Empty input: passed={r2.passed}, errors={r2.errors}")

    # 6. Narrative Engine
    console.print("\n[yellow]> 6/9  Narrative Engine (Dramatica 16-stage)[/yellow]")
    from ..narrative.engine import NarrativeEngine, NARRATIVE_STAGES
    ne = NarrativeEngine()
    console.print(f"   Initial stage: {ne.state.current_stage}")
    for i in range(4):
        stage = ne.advance()
        console.print(f"   -> {stage}")
    console.print(f"   Completed: {len(ne.state.completed_stages)} stages, "
                  f"Progress: {ne.state.progress:.0%}")

    # 7. Schema Registry
    console.print("\n[yellow]> 7/9  Schema Registry[/yellow]")
    from ..schema.registry import SchemaRegistry
    sr = SchemaRegistry()
    for name in ["story_premise", "character", "chapter"]:
        ok, errs = sr.validate(name, {})
        console.print(f"   {name}: valid={ok}")
    ok, errs = sr.validate("story_premise", {"title": "A Novel", "genre": "Fantasy"})
    console.print(f"   story_premise (valid data): valid={ok}")

    # 8. DSL Parser
    console.print("\n[yellow]> 8/9  @DSL Parser[/yellow]")
    from ..context.dsl_parser import DSLParser
    parser = DSLParser()
    matches = parser.parse("Hello @title, meet @type:character from @self")
    console.print(f"   Input: Hello @title, meet @type:character from @self")
    for m in matches:
        console.print(f"   -> type={m.qtype}, target={m.target}, field={m.field}")

    # 9. State Delta
    console.print("\n[yellow]> 9/9  State Delta Tracking[/yellow]")
    from ..state.delta import DeltaStore
    ds = DeltaStore()
    ds.record("title", "", "My Novel", "user")
    ds.record("author", "", "Tester", "user")
    ds.checkpoint("v1")
    ds.record("title", "My Novel", "Great Novel", "user")
    rollback = ds.rollback("v1")
    console.print(f"   Records: 2 -> checkpoint -> 2 more -> rollback -> {len(ds.history)} records")
    console.print(f"   Reverted: {[d.field for d in rollback]}")

    console.print(Panel.fit(
        "[bold green]+ All features demonstrated successfully![/bold green]\n"
        "Run with --help to see all available commands.",
        border_style="green"
    ))


# ─── Server ────────────────────────────────────────────────────────────

@app.command()
def server(
    host: str = typer.Option("0.0.0.0", "--host", "-H", help="Bind address"),
    port: int = typer.Option(8000, "--port", "-p", help="Port number"),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Auto-reload on changes"),
):
    """Start the FastAPI server."""
    import uvicorn
    console.print(f"[green]Starting server on {host}:{port}...[/green]")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


# ─── Validate ──────────────────────────────────────────────────────────

@app.command()
def validate(
    text: str = typer.Argument(..., help="Text or file path to validate"),
    min_words: int = typer.Option(200, "--min-words", "-w", help="Minimum word count"),
):
    """Post-write validation -- checks word count, repeats, quality."""
    from ..validators.post_write import PostWriteValidator

    path = Path(text)
    content = path.read_text("utf-8") if path.exists() else text

    v = PostWriteValidator(min_words=min_words)
    result = v.validate(content)

    if result.passed:
        console.print("[green]+ Validation PASSED[/green]")
    else:
        console.print("[red]- Validation FAILED[/red]")

    if result.errors:
        console.print("\n[yellow]Errors:[/yellow]")
        for e in result.errors:
            console.print(f"  * {e}")
    if result.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for w in result.warnings:
            console.print(f"  * {w}")

    console.print(f"\n[bold]Metrics:[/bold]")
    for k, v in result.metrics.items():
        console.print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")


# ─── Audit ─────────────────────────────────────────────────────────────

@app.command()
def audit(text: str = typer.Argument(..., help="Text or file path to audit")):
    """33-dimension quality audit -- detects fatigue, forbidden patterns, etc."""
    from ..validators.audit_33 import Audit33Validator

    path = Path(text)
    content = path.read_text("utf-8") if path.exists() else text

    v = Audit33Validator()
    result = v.audit(content)

    if result.passed:
        console.print("[green]+ Audit PASSED[/green]")
    else:
        console.print("[red]- Audit FAILED[/red]")

    table = Table(title="Audit Results")
    table.add_column("Dimension", style="cyan")
    table.add_column("Severity", style="yellow")
    table.add_column("Message")
    for i in result.issues:
        table.add_row(i.dimension, i.severity, i.message)
    if result.issues:
        console.print(table)

    console.print(f"\n[bold]Overall Score: {result.overall:.2f}[/bold]")
    console.print(f"[bold]Dimension Scores:[/bold]")
    for dim, score in result.scores.items():
        color = "green" if score >= 0.8 else ("yellow" if score >= 0.5 else "red")
        console.print(f"  {dim}: [{color}]{score:.2f}[/{color}]")


# ─── De-AI ─────────────────────────────────────────────────────────────

@app.command(name="de-ai")
def de_ai(text: str = typer.Argument(..., help="Text or file path to analyze")):
    """De-AI-fication -- detect AI writing traces."""
    from ..validators.de_ai import DeAIFilter

    path = Path(text)
    content = path.read_text("utf-8") if path.exists() else text

    f = DeAIFilter()
    result = f.analyze(content)

    score_color = "green" if result.ai_score < 0.3 else ("yellow" if result.ai_score < 0.6 else "red")
    console.print(f"[bold]AI Score: [{score_color}]{result.ai_score:.2f}[/{score_color}] / 1.00[/bold]")

    if result.passes:
        console.print("[green]+ Passes De-AI check[/green]")
    else:
        console.print("[red]- Fails De-AI check (too many LLM patterns)[/red]")

    if result.issues:
        console.print("\n[bold]Issues found:[/bold]")
        for i in result.issues:
            icon = "WARN" if i.severity == "warning" else "INFO"
            console.print(f"  {icon} [{i.severity}] {i.pattern}: {i.suggestion}")


# ─── Quality ───────────────────────────────────────────────────────────

@app.command()
def quality(
    coherence: float = typer.Option(0.5, "--coherence", "-c", help="Coherence score (0-1)"),
    integration: float = typer.Option(0.5, "--integration", "-i", help="Integration score (0-1)"),
    polish: float = typer.Option(0.5, "--polish", "-p", help="Polish score (0-1)"),
):
    """Calculate quality metrics from scores."""
    from ..validators.metrics import QualityMetrics
    qm = QualityMetrics(coherence=coherence, integration=integration, polish=polish)

    console.print(Panel.fit(
        f"[bold]Quality Metrics[/bold]\n\n"
        f"Coherence:    {qm.coherence:.2f}\n"
        f"Integration:  {qm.integration:.2f}\n"
        f"Polish:       {qm.polish:.2f}\n"
        f"---\n"
        f"Overall:      [bold]{qm.overall:.2f}[/bold]\n"
        f"Passed:       {'[green]Yes[/green]' if qm.passed else '[red]No[/red]'}",
        border_style="green"
    ))


# ─── Narrative ─────────────────────────────────────────────────────────

@app.command()
def narrative(
    chapter: int = typer.Option(5, "--chapter", "-c", help="Chapter number for beat preview"),
    total: int = typer.Option(20, "--total", "-t", help="Total chapters"),
):
    """Show narrative stage progression and chapter beats."""
    from ..narrative.engine import NarrativeEngine, NARRATIVE_STAGES

    ne = NarrativeEngine()

    # Show all stages
    table = Table(title="16 Dramatica Stages")
    table.add_column("#", style="dim")
    table.add_column("Stage", style="cyan")
    table.add_column("Prompt", style="white")
    for i, stage in enumerate(NARRATIVE_STAGES):
        prompt = ne.get_stage_prompt(stage)
        table.add_row(str(i + 1), stage, prompt[:60] + "...")
    console.print(table)

    # Show chapter beats
    console.print(f"\n[bold]Beats for Chapter {chapter} of {total}:[/bold]")
    beats = ne.get_required_beats(chapter, total)
    for b in beats:
        console.print(f"  * {b}: {ne.get_stage_prompt(b)}")

    # Simulate progression
    console.print("\n[bold]Simulated Progression (first 8 chapters):[/bold]")
    for ch in range(1, 9):
        b = ne.get_required_beats(ch, 20)
        console.print(f"  Ch.{ch}: {', '.join(b)}")


# ─── Schema ────────────────────────────────────────────────────────────

@app.command()
def schema(
    action: str = typer.Argument("list", help="Action: list or validate"),
    name: str = typer.Option("", "--name", "-n", help="Schema name (for validate)"),
    data: str = typer.Option("{}", "--data", "-d", help="JSON data (for validate)"),
):
    """List or validate schemas."""
    from ..schema.registry import SchemaRegistry
    sr = SchemaRegistry()

    if action == "list":
        table = Table(title="Schema Registry")
        table.add_column("Name", style="cyan")
        table.add_column("Fields", style="white")
        for sname in ["story_premise", "character", "chapter"]:
            table.add_row(sname, "(use 'validate' to check)")
        console.print(table)

    elif action == "validate":
        if not name:
            console.print("[red]Error: --name is required for validate action[/red]")
            raise typer.Exit(1)
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON: {e}[/red]")
            raise typer.Exit(1)

        ok, errors = sr.validate(name, parsed)
        if ok:
            console.print(f"[green]+ Schema '{name}' validation PASSED[/green]")
        else:
            console.print(f"[red]- Schema '{name}' validation FAILED[/red]")
            for e in errors:
                console.print(f"  * {e}")


# ─── DSL Parse ─────────────────────────────────────────────────────────

@app.command()
def dsl(
    template: str = typer.Argument(..., help="@DSL template string to parse"),
):
    """Parse @DSL template syntax."""
    from ..context.dsl_parser import DSLParser
    parser = DSLParser()

    console.print(f"[bold]Input:[/bold] {template}")
    matches = parser.parse(template)

    if not matches:
        console.print("[yellow]No @DSL patterns found.[/yellow]")
        return

    table = Table(title="DSL Matches")
    table.add_column("Type", style="cyan")
    table.add_column("Target", style="green")
    table.add_column("Field", style="yellow")
    table.add_column("Valid", style="white")
    for m in matches:
        table.add_row(m.qtype, m.target or "-", m.field or "-", str(m.valid))
    console.print(table)


# ─── Providers ─────────────────────────────────────────────────────────

@app.command()
def providers():
    """List all available LLM providers and their models."""
    from ..llm.provider_bank import PROVIDER_BANK

    table = Table(title="LLM Provider Bank")
    table.add_column("Provider", style="cyan", no_wrap=True)
    table.add_column("API Base URL", style="white")
    table.add_column("Models", style="green")
    table.add_column("Env Key", style="dim")

    for name, info in PROVIDER_BANK.items():
        models = ", ".join(info.models[:3])
        if len(info.models) > 3:
            models += f"... (+{len(info.models) - 3})"
        table.add_row(info.name, info.base_url or "(local)", models, info.api_key_env or "-")
    console.print(table)

    console.print("\n[bold]Provider IDs for .env:[/bold]")
    console.print("  LLM_PROVIDER=openai | deepseek | anthropic | google | ollama | custom")


# ─── State ─────────────────────────────────────────────────────────────

@app.command()
def state():
    """Demonstrate state delta tracking with checkpoint/rollback."""
    from ..state.delta import DeltaStore
    ds = DeltaStore()

    console.print("[bold]State Delta Tracking Demo[/bold]\n")

    console.print("[dim]1. Record 'title' = 'My Novel'[/dim]")
    ds.record("title", "", "My Novel", "user")

    console.print("[dim]2. Record 'author' = 'Tester'[/dim]")
    ds.record("author", "", "Tester", "user")

    console.print(f"[dim]3. History: {len(ds.history)} entries[/dim]")
    for d in ds.history:
        console.print(f"   [{d.agent}] {d.field}: '{d.old_value}' -> '{d.new_value}'")

    console.print("\n[dim]4. Checkpoint 'v1'[/dim]")
    ds.checkpoint("v1")
    console.print("[green]   + Checkpoint saved[/green]")

    console.print("\n[dim]5. Record 'title' = 'Great Novel'[/dim]")
    ds.record("title", "My Novel", "Great Novel", "user")

    console.print("\n[dim]6. Record 'word_count' = 5000[/dim]")
    ds.record("word_count", 0, 5000, "system")

    console.print(f"[dim]7. History: {len(ds.history)} entries[/dim]")

    console.print("\n[dim]8. Rollback to 'v1'[/dim]")
    reverted = ds.rollback("v1")
    console.print(f"[yellow]   Reverted {len(reverted)} changes: {[d.field for d in reverted]}[/yellow]")
    console.print(f"[dim]9. History after rollback: {len(ds.history)} entries[/dim]")

    console.print("[green]\n+ State delta tracking works correctly[/green]")


# ─── API ───────────────────────────────────────────────────────────────

@app.command()
def api(
    action: str = typer.Argument("health", help="API action: health, projects, create-project, chapters, generate"),
    project_id: str = typer.Option("", "--project", "-p", help="Project ID"),
    title: str = typer.Option("", "--title", "-t", help="Project title"),
    chapter_number: int = typer.Option(1, "--chapter", "-c", help="Chapter number"),
    base_url: str = typer.Option("http://localhost:8000", "--url", "-u", help="API base URL"),
):
    """Quick API calls against a running server."""
    import httpx

    client = httpx.Client(base_url=base_url)
    base = "/api"

    try:
        if action == "health":
            r = client.get(f"{base}/health")
            console.print_json(r.text)

        elif action == "projects":
            r = client.get(f"{base}/projects")
            console.print_json(r.text)

        elif action == "create-project":
            if not title:
                console.print("[red]Error: --title is required[/red]")
                raise typer.Exit(1)
            r = client.post(f"{base}/projects", json={"title": title})
            console.print_json(r.text)

        elif action == "chapters":
            if not project_id:
                console.print("[red]Error: --project is required[/red]")
                raise typer.Exit(1)
            r = client.get(f"{base}/projects/{project_id}/chapters")
            console.print_json(r.text)

        elif action == "generate":
            if not project_id:
                console.print("[red]Error: --project is required[/red]")
                raise typer.Exit(1)
            r = client.post(f"{base}/generate/chapter", json={
                "project_id": project_id,
                "chapter_number": chapter_number,
            })
            console.print_json(r.text)

        else:
            console.print(f"[red]Unknown action: {action}[/red]")
            console.print("Available: health, projects, create-project, chapters, generate")
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to server. Start it first with:[/red]")
        console.print("  python -m app.cli server")


# ─── Entry point ───────────────────────────────────────────────────────

def entry():
    """Entry point for `python -m app.cli`."""
    app()

if __name__ == "__main__":
    entry()
