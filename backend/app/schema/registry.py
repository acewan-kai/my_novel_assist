"""Schema Registry — NovelForge-inspired card type system."""

from __future__ import annotations

BUILTIN_SCHEMAS: dict[str, dict] = {
    "story_premise": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "故事标题"},
            "genre": {"type": "string", "description": "题材"},
            "theme": {"type": "string", "description": "主题"},
        },
        "required": ["title", "genre"],
    },
    "character": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "role": {"type": "string", "enum": ["protagonist", "antagonist", "supporting", "sidekick", "mentor"]},
            "goal": {"type": "string", "description": "外部目标"},
            "need": {"type": "string", "description": "内在需求"},
            "backstory": {"type": "string"},
            "traits": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["name", "role"],
    },
    "chapter": {
        "type": "object",
        "properties": {
            "number": {"type": "integer"},
            "title": {"type": "string"},
            "pov": {"type": "string"},
            "scenes": {"type": "array", "items": {"type": "object", "properties": {
                "summary": {"type": "string"}, "location": {"type": "string"},
                "participants": {"type": "array", "items": {"type": "string"}},
            }}},
            "word_target": {"type": "integer"},
        },
        "required": ["number", "title"],
    },
}


class SchemaRegistry:
    def __init__(self):
        self._schemas = dict(BUILTIN_SCHEMAS)

    def register(self, name: str, schema: dict) -> bool:
        self._schemas[name] = schema
        return True

    def get(self, name: str) -> dict | None:
        return self._schemas.get(name)

    def list_types(self) -> list[str]:
        return list(self._schemas.keys())

    def validate(self, name: str, data: dict) -> tuple[bool, list[str]]:
        schema = self._schemas.get(name)
        if not schema:
            return True, []
        errors = []
        for field in schema.get("required", []):
            if field not in data or data[field] is None:
                errors.append(f"Missing: {field}")
        props = schema.get("properties", {})
        for k, v in data.items():
            p = props.get(k)
            if p and "enum" in p and v not in p["enum"]:
                errors.append(f"Invalid {k}: '{v}'")
        return len(errors) == 0, errors


registry = SchemaRegistry()
