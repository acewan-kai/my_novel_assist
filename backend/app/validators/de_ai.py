"""De-AI-fication — detect and reduce AI writing traces."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class DeAIIssue:
    pattern: str = ""
    severity: str = "info"
    suggestion: str = ""


@dataclass
class DeAIReport:
    issues: list[DeAIIssue] = field(default_factory=list)
    ai_score: float = 0.0
    passes: bool = True


LLM_PATTERNS = [
    (r"让我们(?:一起)?(?:看看|探讨|思考)", "作者介入"),
    (r"首先[,，].*其次[,，].*最后[,，]", "结构化列举"),
    (r"值得注意的[是]", "评论插入"),
    (r"从[^。]{0,30}角度[^。]{0,10}(?:看|分析)", "分析视角"),
    (r"总的来说[,，]|综上所述[,，]", "总结句式"),
    (r"[他她]深吸一口气[,，]", "LLM常用动作"),
    (r"仿佛[^。]{0,20}一般", "比喻句式"),
]

TRANSITION_PATTERNS = [(r"与此同时", 0.8), (r"就在这时", 0.6), (r"突然间", 0.5)]


class DeAIFilter:
    def analyze(self, text: str) -> DeAIReport:
        issues = []
        penalty = 0.0

        for pattern, name in LLM_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                issues.append(DeAIIssue(name, "warning", f"x{len(matches)}"))
                penalty += 0.08 * len(matches)

        per_k = max(len(text) / 1000, 1)
        for pattern, threshold in TRANSITION_PATTERNS:
            n = len(re.findall(pattern, text))
            if n / per_k > threshold:
                issues.append(DeAIIssue(f"过渡:{pattern}", "info"))
                penalty += 0.05

        sensory = {"视觉": ["看见", "映入", "呈现"], "听觉": ["听见", "声音", "回荡"],
                   "触觉": ["感觉", "触感", "冰冷"], "嗅觉": ["闻到", "气息"]}
        total_sensory = sum(sum(text.count(w) for w in words) for words in sensory.values())
        if total_sensory / per_k < 2:
            issues.append(DeAIIssue("sensory", "info", f"密度{total_sensory/per_k:.1f}/千字"))

        ai_score = min(1.0, penalty)
        return DeAIReport(issues=issues, ai_score=ai_score, passes=ai_score < 0.4)
