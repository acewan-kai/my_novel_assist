"""
ThatMyDream — CLI Novel Director
Entry point: starts the director loop.
"""
from __future__ import annotations
import os
import sys

from rich.console import Console
from rich.panel import Panel

from director import Director
from scene import Scene
from config import CHARACTERS_DIR, WORLD_DIR, STORIES_DIR

console = Console()


def _ensure_dirs() -> None:
    for d in (CHARACTERS_DIR, WORLD_DIR, STORIES_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _check_api_key() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print(
            "[bold red]Warning:[/bold red] ANTHROPIC_API_KEY is not set.\n"
            "Set it with:  [cyan]export ANTHROPIC_API_KEY=sk-...[/cyan]\n"
        )


def _welcome_banner() -> None:
    console.print(
        Panel(
            "[bold]ThatMyDream[/bold] — AI Novel Director\n\n"
            "You are the [bold cyan]Director[/bold cyan]. Set the stage, summon characters, let the story unfold.\n"
            "Type [cyan]/help[/cyan] for commands.  Type [cyan]/quit[/cyan] to save and exit.",
            border_style="green",
            expand=False,
        )
    )
    console.print()


def _resume_prompt(scene: Scene) -> bool:
    """Return True if user wants to continue the existing scene."""
    console.print(
        f"[yellow]Found a previous scene:[/yellow] [bold]{scene.name}[/bold]  "
        f"({len(scene.present_characters)} character(s) present)"
    )
    answer = console.input("  Continue this scene? [[green]Y[/green]/n] ").strip().lower()
    return answer in ("", "y", "yes")


def main() -> None:
    _ensure_dirs()
    _check_api_key()
    _welcome_banner()

    director = Director()

    # Offer to continue or discard previous scene
    if director.scene:
        if not _resume_prompt(director.scene):
            director.scene = None
            console.print("[dim]Previous scene cleared. Start with /scene <name>.[/dim]\n")
        else:
            console.print(
                f"[dim]Resuming scene: {director.scene.name}  "
                f"— {len(director.scene.present_characters)} character(s) present.[/dim]\n"
            )

    # Main command loop
    try:
        while True:
            try:
                raw = console.input("[bold green]>[/bold green] ")
            except EOFError:
                break

            if not director.handle(raw):
                break

    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted — saving session…[/dim]")
        director._end_session()
        console.print()


if __name__ == "__main__":
    main()
