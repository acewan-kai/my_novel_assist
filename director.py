"""
Director — routes CLI commands to story actions.
"""
from __future__ import annotations
import anthropic
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

from character import Character
from scene import Scene
from story import StoryRecorder
import memory as mem
from config import MODEL, MAX_TOKENS_SPEECH

_client = anthropic.Anthropic()
console = Console()


# ─────────────────────────────────────────────────────────────────────────────

class Director:
    def __init__(self) -> None:
        self.scene: Scene | None = Scene.load()
        self.story = StoryRecorder()

    # ── Public entry point ────────────────────────────────────────────────────

    def handle(self, raw: str) -> bool:
        """
        Process one line of CLI input.
        Returns False when the user wants to quit.
        """
        raw = raw.strip()
        if not raw:
            return True

        # Split into command and the rest
        if " " in raw:
            cmd, rest = raw.split(None, 1)
        else:
            cmd, rest = raw, ""

        cmd = cmd.lower()

        dispatch = {
            "/scene":   self._cmd_scene,
            "/add":     self._cmd_add,
            "/remove":  self._cmd_remove,
            "/speak":   self._cmd_speak,
            "/narrate": self._cmd_narrate,
            "/story":   self._cmd_story,
            "/status":  self._cmd_status,
            "/help":    self._cmd_help,
            "/quit":    None,
            "/q":       None,
            "/exit":    None,
        }

        if cmd in ("/quit", "/q", "/exit"):
            self._end_session()
            return False

        handler = dispatch.get(cmd)
        if handler is None:
            console.print(f"[red]Unknown command:[/red] {cmd}   (type [cyan]/help[/cyan])")
        else:
            handler(rest)

        return True

    # ── Commands ──────────────────────────────────────────────────────────────

    def _cmd_scene(self, args: str) -> None:
        """
        /scene <name>
        /scene <name> | <description>
        """
        if not args:
            console.print("[yellow]Usage: /scene <name>  or  /scene <name> | <description>[/yellow]")
            return

        if "|" in args:
            name, description = args.split("|", 1)
            name = name.strip()
            description = description.strip()
        else:
            name = args.strip()
            description = ""

        self.scene = Scene(name=name, description=description)
        self.scene.save()
        console.print(f"\n[bold green]Scene:[/bold green] {name}")
        if description:
            console.print(f"[dim]{description}[/dim]")
        console.print()

    def _cmd_add(self, args: str) -> None:
        """/add <character_name>"""
        if not self.scene:
            console.print("[red]Set a scene first:  /scene <name>[/red]")
            return
        name = args.strip()
        if not name:
            console.print("[yellow]Usage: /add <character_name>[/yellow]")
            return

        # Create if new
        if not Character.exists(name):
            console.print(f"[yellow]'{name}' doesn't exist yet. Let's create them.[/yellow]")
            char = self._create_character_interactive(name)
        else:
            char = Character.load(name)

        self.scene.add_character(char.name)
        entry = f"{char.name} enters the scene."
        self.scene.add_to_working_memory(entry)
        self.story.append_entry("STAGE", entry, entry_type="narration")
        mem.add_episode(char, self.scene.scene_id, entry)
        char.save()
        console.print(f"[dim italic]{entry}[/dim italic]\n")

    def _cmd_remove(self, args: str) -> None:
        """/remove <character_name>"""
        if not self.scene:
            console.print("[red]No active scene.[/red]")
            return
        name = args.strip()
        if not name:
            console.print("[yellow]Usage: /remove <character_name>[/yellow]")
            return
        self.scene.remove_character(name)
        entry = f"{name} leaves the scene."
        self.scene.add_to_working_memory(entry)
        self.story.append_entry("STAGE", entry, entry_type="narration")
        console.print(f"[dim italic]{entry}[/dim italic]\n")

    def _cmd_speak(self, args: str) -> None:
        """
        /speak <character>
        /speak <character> | <prompt to the character>
        """
        if not self.scene:
            console.print("[red]No active scene.[/red]")
            return

        if "|" in args:
            char_name, prompt_text = args.split("|", 1)
            char_name = char_name.strip()
            prompt_text = prompt_text.strip()
        else:
            char_name = args.strip()
            prompt_text = "React naturally to the current situation. What do you say or do?"

        if not char_name:
            console.print("[yellow]Usage: /speak <character>  or  /speak <character> | <prompt>[/yellow]")
            return

        if char_name not in self.scene.present_characters:
            console.print(
                f"[red]{char_name} is not in the scene.[/red]  "
                f"Use [cyan]/add {char_name}[/cyan] first."
            )
            return

        char = Character.load(char_name)

        # Build prompt blocks — persona cached, rest volatile
        system_blocks = mem.assemble_system_blocks(char, self.scene.working_memory)

        with console.status(f"[dim]{char_name} is thinking…[/dim]"):
            response = _client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS_SPEECH,
                system=system_blocks,
                messages=[{"role": "user", "content": prompt_text}],
            )

        speech = response.content[0].text.strip()

        # Display
        console.print(
            Panel(
                Text(speech),
                title=f"[bold cyan]{char_name}[/bold cyan]",
                border_style="cyan",
                expand=False,
            )
        )
        console.print()

        # Log to story
        self.story.append_entry(char_name, speech)

        # Update memories for ALL present characters
        memory_entry = f'{char_name} said: "{speech}"'
        self.scene.add_to_working_memory(f"{char_name}: {speech}")

        for c_name in self.scene.present_characters:
            c = Character.load(c_name)
            mem.add_episode(c, self.scene.scene_id, memory_entry)
            c.save()

    def _cmd_narrate(self, args: str) -> None:
        """/narrate <description of what happens>"""
        if not self.scene:
            console.print("[red]No active scene.[/red]")
            return
        text = args.strip()
        if not text:
            console.print("[yellow]Usage: /narrate <what happens>[/yellow]")
            return

        console.print(f"\n[italic dim]{text}[/italic dim]\n")
        self.story.append_entry("NARRATOR", text, entry_type="narration")

        self.scene.add_to_working_memory(f"[Event] {text}")

        for c_name in self.scene.present_characters:
            c = Character.load(c_name)
            mem.add_episode(c, self.scene.scene_id, f"[Event] {text}")
            c.save()

    def _cmd_story(self, args: str = "") -> None:
        """/story"""
        text = self.story.print_story()
        console.print(Panel(text, title="[bold]Story So Far[/bold]", border_style="dim"))

    def _cmd_status(self, args: str = "") -> None:
        """/status"""
        if not self.scene:
            console.print("[yellow]No active scene.[/yellow]")
            return
        chars = ", ".join(self.scene.present_characters) or "[dim]none[/dim]"
        console.print(f"\n[bold]Scene:[/bold] {self.scene.name}")
        if self.scene.description:
            console.print(f"[dim]{self.scene.description}[/dim]")
        console.print(f"[bold]Characters:[/bold] {chars}")
        console.print(f"[bold]Working memory entries:[/bold] {len(self.scene.working_memory)}")
        console.print(f"[bold]Story file:[/bold] {self.story.path}\n")

    def _cmd_help(self, args: str = "") -> None:
        """/help"""
        console.print(Panel(
            "\n".join([
                "[bold]Commands[/bold]",
                "",
                "  [cyan]/scene <name>[/cyan]                  — Create / enter a scene",
                "  [cyan]/scene <name> | <description>[/cyan]  — Scene with description",
                "  [cyan]/add <character>[/cyan]               — Add character (creates if new)",
                "  [cyan]/remove <character>[/cyan]            — Remove character from scene",
                "  [cyan]/speak <character>[/cyan]             — Character speaks naturally",
                "  [cyan]/speak <character> | <prompt>[/cyan]  — Character responds to prompt",
                "  [cyan]/narrate <text>[/cyan]                — Director narrates an event",
                "  [cyan]/story[/cyan]                         — Print story log",
                "  [cyan]/status[/cyan]                        — Show scene info",
                "  [cyan]/help[/cyan]                          — Show this help",
                "  [cyan]/quit[/cyan]                          — Save & exit",
            ]),
            border_style="dim",
            expand=False,
        ))

    # ── Character creation wizard ─────────────────────────────────────────────

    def _create_character_interactive(self, name: str) -> Character:
        console.print(f"\n[bold]Creating character: {name}[/bold]")
        background = Prompt.ask("  Background", default="")
        traits_raw = Prompt.ask("  Personality traits (comma-separated)", default="curious, thoughtful")
        values_raw = Prompt.ask("  Core values (comma-separated)", default="loyalty")
        goals_raw = Prompt.ask("  Goals (comma-separated, optional)", default="")
        secrets_raw = Prompt.ask("  Secrets (comma-separated, optional)", default="")
        emotional_state = Prompt.ask("  Current emotional state", default="neutral")

        char = Character(
            name=name,
            background=background,
            traits=[t.strip() for t in traits_raw.split(",") if t.strip()],
            values=[v.strip() for v in values_raw.split(",") if v.strip()],
            goals=[g.strip() for g in goals_raw.split(",") if g.strip()],
            secrets=[s.strip() for s in secrets_raw.split(",") if s.strip()],
            emotional_state=emotional_state,
        )
        char.save()
        console.print(f"[green]✓ {name} created.[/green]\n")
        return char

    # ── Session end ───────────────────────────────────────────────────────────

    def _end_session(self) -> None:
        if self.scene and self.scene.present_characters:
            with console.status("[dim]Compressing memories before exit…[/dim]"):
                for c_name in self.scene.present_characters:
                    char = Character.load(c_name)
                    mem.compress_to_longterm(char)
                    char.save()
        console.print("\n[green]Session saved. See you next time![/green]\n")
