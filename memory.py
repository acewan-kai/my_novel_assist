"""
Memory operations:
  - add_episode()          — append a witnessed event
  - compress_to_longterm() — compress old episodes → summary via Claude
  - assemble_system_blocks() — build prompt blocks with prompt caching
"""
from __future__ import annotations
import datetime
import anthropic

from config import MODEL, MAX_TOKENS_COMPRESS, EPISODE_WINDOW, LONGTERM_WINDOW
from character import Character

_client = anthropic.Anthropic()


# ── Core operations ───────────────────────────────────────────────────────────

def add_episode(character: Character, scene_id: str, content: str) -> None:
    """Append a witnessed event to the character's episodic memory."""
    character.episodes.append({
        "scene_id": scene_id,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "content": content,
    })


def compress_to_longterm(character: Character) -> None:
    """
    If episodes exceed EPISODE_WINDOW, compress the overflow into a
    long-term summary via Claude and trim the episode list.
    """
    if len(character.episodes) <= EPISODE_WINDOW:
        return

    overflow = character.episodes[:-EPISODE_WINDOW]
    character.episodes = character.episodes[-EPISODE_WINDOW:]

    episodes_text = "\n".join(
        f"[Scene {e['scene_id']}] {e['content']}" for e in overflow
    )

    response = _client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS_COMPRESS,
        system=(
            f"You are summarizing memories for the character {character.name}. "
            "Write a concise 2-3 sentence summary in third person. "
            "Preserve key emotional events, relationship changes, and important facts."
        ),
        messages=[{
            "role": "user",
            "content": f"Summarize these events for {character.name}'s long-term memory:\n\n{episodes_text}",
        }],
    )
    summary = response.content[0].text.strip()
    character.long_term_summaries.append(summary)


# ── Context assembly with prompt caching ─────────────────────────────────────

def assemble_system_blocks(
    character: Character,
    scene_working_memory: list[str],
) -> list[dict]:
    """
    Build the `system` blocks for a Claude API call.

    Structure (cache-friendly: stable first, volatile last):
      Block 1 [STABLE — cache_control] : core persona (traits, background, values…)
      Block 2 [VOLATILE]               : relationships + memories + current scene
    """
    # ── Block 1: stable persona (cached) ──────────────────────────────────────
    persona_parts = [
        f"You are roleplaying as {character.name}. Stay in character at all times.",
        "Respond as this character would — naturally, consistently with their personality.",
        "Keep responses concise (1-4 sentences) unless the scene demands more.",
        "",
    ]
    if character.background:
        persona_parts.append(f"Background: {character.background}")
    if character.traits:
        persona_parts.append(f"Personality traits: {', '.join(character.traits)}")
    if character.values:
        persona_parts.append(f"Core values: {', '.join(character.values)}")
    if character.goals:
        persona_parts.append(f"Goals: {', '.join(character.goals)}")

    persona_text = "\n".join(persona_parts).strip()

    blocks: list[dict] = [
        {
            "type": "text",
            "text": persona_text,
            "cache_control": {"type": "ephemeral"},   # ← cache stable persona
        }
    ]

    # ── Block 2: volatile context (not cached) ────────────────────────────────
    volatile_parts: list[str] = []

    volatile_parts.append(f"Current emotional state: {character.emotional_state}")

    if character.relationships:
        rel_lines = [
            f"  {name}: feeling {data.get('emotion', 'neutral')}, "
            f"trust {data.get('trust', 5)}/10"
            for name, data in character.relationships.items()
        ]
        volatile_parts.append("Your relationships:\n" + "\n".join(rel_lines))

    if character.long_term_summaries:
        recent_lt = character.long_term_summaries[-LONGTERM_WINDOW:]
        volatile_parts.append(
            "What you remember from the past:\n" +
            "\n".join(f"- {s}" for s in recent_lt)
        )

    if character.episodes:
        recent_eps = character.episodes[-EPISODE_WINDOW:]
        volatile_parts.append(
            "Recent events you witnessed:\n" +
            "\n".join(f"- {e['content']}" for e in recent_eps)
        )

    if scene_working_memory:
        volatile_parts.append(
            "Current scene (most recent exchanges):\n" +
            "\n".join(scene_working_memory[-20:])
        )

    if volatile_parts:
        blocks.append({
            "type": "text",
            "text": "\n\n".join(volatile_parts),
        })

    return blocks
