"""Schema Registry — with type-aware and semantic validation."""

from __future__ import annotations

# ── 中文小说类型 ──────────────────────────────────────────
KNOWN_GENRES = [
    "奇幻", "科幻", "武侠", "仙侠", "都市", "历史", "悬疑",
    "推理", "言情", "恐怖", "轻小说", "现实", "史诗", "冒险",
    "末世", "游戏", "穿越", "重生", "军事", "竞技",
]

# ── Schema 定义 ───────────────────────────────────────────
BUILTIN_SCHEMAS: dict[str, dict] = {
    "story_premise": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "小说标题"},
            "genre": {"type": "string", "description": "题材"},
            "theme": {"type": "string", "description": "主题"},
            "logline": {"type": "string", "description": "一句话梗概"},
        },
        "required": ["title", "genre"],
    },
    "character": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "角色名称"},
            "role": {"type": "string", "enum": [
                "protagonist", "antagonist", "supporting", "sidekick", "mentor",
                "主角", "反派", "配角", "盟友", "导师",
            ], "description": "角色定位"},
            "goal": {"type": "string", "description": "角色目标"},
            "need": {"type": "string", "description": "内在需求"},
            "backstory": {"type": "string", "description": "背景故事"},
            "description": {"type": "string", "description": "角色描述"},
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

    # ── 字段类型校验 ─────────────────────────────────────
    @staticmethod
    def _validate_field_type(key: str, value, prop: dict, errors: list[str]) -> None:
        typ = prop.get("type")
        if typ == "string" and not isinstance(value, str):
            errors.append(f"「{key}」应为文本类型")
        elif typ == "integer" and not isinstance(value, int):
            errors.append(f"「{key}」应为整数类型")
        elif typ == "array" and not isinstance(value, list):
            errors.append(f"「{key}」应为数组类型")
        elif typ == "array" and isinstance(value, list):
            items_schema = prop.get("items", {})
            if items_schema.get("type") == "object":
                item_props = items_schema.get("properties", {})
                for idx, item in enumerate(value):
                    if not isinstance(item, dict):
                        errors.append(f"「{key}」第 {idx+1} 项应为对象")
                        continue
                    for fname, fprop in item_props.items():
                        if fname in item and item[fname] is not None:
                            SchemaRegistry._validate_field_type(
                                f"{key}[{idx}].{fname}", item[fname], fprop, errors
                            )

    # ── 语义校验器 ────────────────────────────────────────
    @staticmethod
    def _validate_genre(data: dict) -> list[str]:
        """校验题材是否有效。"""
        genre = data.get("genre", "")
        if not genre:
            return []
        if genre not in KNOWN_GENRES:
            return [f"题材「{genre}」不在推荐列表中（{'、'.join(KNOWN_GENRES[:8])}……）"]
        return []

    @staticmethod
    def _validate_logline(data: dict) -> list[str]:
        """校验一句话梗概质量。"""
        logline = data.get("logline", "")
        if not logline:
            return ["建议填写一句话梗概，帮助锁定故事核心"]
        errs = []
        if len(logline) < 10:
            errs.append(f"梗概仅 {len(logline)} 字，建议至少 10 字以清晰表达故事核心")
        if not any(c in logline for c in "发现遇到卷入被迫意外"):
            errs.append("梗概中建议包含「发现/遇到/卷入」等词，体现故事冲突或转折")
        return errs

    @staticmethod
    def _validate_title(data: dict) -> list[str]:
        """校验标题。"""
        title = data.get("title", "")
        if not title:
            return []
        errs = []
        if len(title) < 2:
            errs.append("标题至少 2 个字")
        if title in ("未命名", "untitled", "无标题"):
            errs.append("标题为占位符，请修改")
        return errs

    @staticmethod
    def _validate_character_completeness(data: dict) -> list[str]:
        """校验角色完整度。"""
        errs = []
        if not data.get("goal"):
            errs.append("建议填写角色目标（goal）")
        if not data.get("need"):
            errs.append("建议填写内在需求（need）")
        if not data.get("backstory"):
            errs.append("建议填写背景故事（backstory）")
        return errs

    # ── 主验证方法 ────────────────────────────────────────
    def validate(self, name: str, data: dict) -> tuple[bool, list[str]]:
        """验证数据是否符合 schema。返回 (是否通过, 错误列表)。"""
        schema = self._schemas.get(name)
        if not schema:
            return True, []
        errors: list[str] = []
        props = schema.get("properties", {})

        # Phase 1: 必填字段
        for field in schema.get("required", []):
            if field not in data or data[field] is None or data[field] == "":
                label = props.get(field, {}).get("description", field)
                errors.append(f"缺少{label}（{field}）")

        # Phase 2: 类型校验
        for k, v in data.items():
            p = props.get(k)
            if p and v is not None:
                self._validate_field_type(k, v, p, errors)

        # Phase 3: 枚举校验
        for k, v in data.items():
            p = props.get(k)
            if p and "enum" in p and v and v not in p["enum"]:
                errors.append(f"「{k}」的值「{v}」不在有效选项中")

        # Phase 4: 语义校验
        semantic_map = {
            "story_premise": [self._validate_genre, self._validate_logline, self._validate_title],
            "character": [self._validate_character_completeness],
        }
        for vfn in semantic_map.get(name, []):
            errors.extend(vfn(data))

        return len(errors) == 0, errors

    def validate_scored(self, name: str, data: dict) -> tuple[bool, list[str], float]:
        """验证并返回 0-1 分数。"""
        _, errors = self.validate(name, data)
        score = 1.0
        for e in errors:
            if e.startswith("缺少"):
                score -= 0.25
            elif e.startswith("建议"):
                score -= 0.1
            elif e.startswith("梗概") or e.startswith("题材"):
                score -= 0.15
            else:
                score -= 0.1
        score = max(0.0, min(1.0, score))
        passed = score >= 0.5
        return passed, errors, score


registry = SchemaRegistry()
