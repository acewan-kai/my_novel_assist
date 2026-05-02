"""33-dimension audit — InkOS-inspired quality checks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class AuditIssue:
    dimension: str = ""
    severity: str = ""
    message: str = ""


@dataclass
class AuditReport:
    passed: bool = True
    issues: list[AuditIssue] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    overall: float = 1.0


FATIGUE_WORDS = {"然而": 0.8, "突然": 0.5, "仿佛": 0.5, "竟然": 0.3, "不由得": 0.3,
                 "忽然": 0.3, "猛地": 0.3, "霎时": 0.2, "顿时": 0.5, "不禁": 0.3}

META_PATTERNS = [r"核心动机", r"信息落差", r"叙事节奏", r"情节推进", r"人物弧线", r"显然"]

COLLECTIVE_PATTERNS = [r"(?:在场|全场)(?:之人|人|众人)(?:皆|都|全)", r"众人齐声"]

FORBIDDEN = [r"不是[……—]{2,}而是", r"全场震惊", r"众人哗然", r"所有人都", r"不言而喻"]


class Audit33Validator:
    def audit(self, text: str) -> AuditReport:
        issues = []
        scores = {}

        # Fatigue words
        c = 0
        for w, t in FATIGUE_WORDS.items():
            n = text.count(w)
            if n / max(len(text) / 1000, 1) > t:
                c += 1
                if n > 3:
                    issues.append(AuditIssue("fatigue", "warning", f"'{w}' x{n}"))
        scores["fatigue"] = max(0, 1 - c * 0.1)

        # Forbidden patterns
        c = 0
        for p in FORBIDDEN:
            for m in re.findall(p, text):
                c += 1
                issues.append(AuditIssue("forbidden", "critical", f"match: {m[:30]}"))
        scores["forbidden"] = max(0, 1 - c * 0.2)

        # Meta-narrative
        c = sum(len(re.findall(p, text)) for p in META_PATTERNS)
        if c:
            issues.append(AuditIssue("meta", "warning", f"x{c}"))
        scores["meta"] = max(0, 1 - c * 0.15)

        # Collective reactions
        c = sum(len(re.findall(p, text)) for p in COLLECTIVE_PATTERNS)
        if c:
            issues.append(AuditIssue("collective", "critical", f"x{c}"))
        scores["collective"] = max(0, 1 - c * 0.25)

        # Consecutive 了 sentences
        sentences = re.split(r'[。！？\n]', text)
        cons = max((sum(1 for _ in iter(lambda: next(iter([])), None)) for _ in [1]), default=0)  # placeholder
        max_cons = 0
        current = 0
        for s in sentences:
            if s.strip().endswith('了'):
                current += 1
                max_cons = max(max_cons, current)
            else:
                current = 0
        if max_cons >= 5:
            issues.append(AuditIssue("consecutive_le", "warning", f"x{max_cons}"))
        scores["consecutive_le"] = max(0, 1 - (max_cons - 4) * 0.1)

        overall = sum(scores.values()) / len(scores) if scores else 1.0
        return AuditReport(passed=overall >= 0.6 and not any(i.severity == "critical" for i in issues),
                          issues=issues, scores=scores, overall=overall)
