"""@DSL parser — NovelForge-inspired context injection.

Syntax: @title, @type:type_name, @self, @parent
Filters: [previous:n], [filter:expr]
Fields: .field_name
"""

from __future__ import annotations

import re
from typing import Any


class DSLQuery:
    raw: str = ""
    qtype: str = ""
    target: str = ""
    field: str = ""
    valid: bool = False


class DSLParser:
    P_BY_TITLE = re.compile(r"@(?P<t>[^@\s{.\[(]+)")
    P_BY_TYPE = re.compile(r"@type:(?P<t>[^\s{.\[(]+)")
    P_SPECIAL = re.compile(r"@(?P<s>self|parent|prev)")

    def parse(self, template: str) -> list[DSLQuery]:
        queries = []
        for m in self.P_BY_TYPE.finditer(template):
            q = DSLQuery(); q.raw = m.group(0); q.qtype = "type"; q.target = m.group("t"); q.valid = True
            queries.append(q)
        for m in self.P_SPECIAL.finditer(template):
            q = DSLQuery(); q.raw = m.group(0); q.qtype = "special"; q.target = m.group("s"); q.valid = True
            queries.append(q)
        for m in self.P_BY_TITLE.finditer(template):
            if m.group(0).startswith("@type:") or m.group(0) in ("@self", "@parent", "@prev"):
                continue
            q = DSLQuery(); q.raw = m.group(0); q.qtype = "title"; q.target = m.group("t"); q.valid = True
            queries.append(q)
        return queries


class ContextInjector:
    def __init__(self):
        self.parser = DSLParser()

    def inject(self, template: str, resolver: Any) -> str:
        for q in self.parser.parse(template):
            if q.qtype == "type":
                resolved = resolver.resolve_type(q.target) if hasattr(resolver, "resolve_type") else f"[@{q.target}]"
            elif q.qtype == "special":
                resolved = resolver.resolve_special(q.target) if hasattr(resolver, "resolve_special") else ""
            else:
                resolved = resolver.resolve_title(q.target) if hasattr(resolver, "resolve_title") else f"[@{q.target}]"
            if resolved:
                template = template.replace(q.raw, str(resolved), 1)
        return template
