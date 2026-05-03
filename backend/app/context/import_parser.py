"""Import parser — extract premise and character info using LLM, with regex fallback."""

from __future__ import annotations

import json
import re
from typing import Any

from ..llm import LLMConfig, LLMMessage, BaseProvider

# ── 常量（正则 fallback 用） ────────────────────────────

SURNAMES: set[str] = set(
    "王李张刘陈杨赵黄周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐"
    "冯于董萧程曹袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘"
    "杜戴夏钟汪田任姜范方石姚谭廖邹熊金陆郝孔白崔康毛邱秦"
    "江史顾侯邵孟龙万段漕钱汤尹黎易常武乔贺赖龚文"
)

ROLE_KEYWORDS: list[str] = [
    "主角", "反派", "配角", "盟友", "导师", "恋人", "对手",
    "女主角", "男主角", "主人公",
]

GENRE_KEYWORDS: list[str] = [
    "奇幻", "科幻", "武侠", "仙侠", "都市", "历史", "悬疑",
    "推理", "言情", "恐怖", "轻小说", "现实", "史诗", "冒险",
    "末世", "游戏", "穿越", "重生", "军事", "竞技",
]

NAME_VERBS: list[str] = [
    "说", "道", "问", "答", "走", "看", "听", "想",
    "发现", "觉得", "感到", "知道", "看见", "听见",
    "是", "有", "去", "来", "坐", "站", "笑", "哭",
]

PREMISE_SYSTEM_PROMPT = """你是一个小说设定分析专家。从用户提供的文本中提取小说的核心设定信息。

请以严格的 JSON 格式返回（不要加 markdown 代码块标记），包含以下字段：
- title: 小说标题（字符串）
- genre: 小说类型，从以下列表中选择最匹配的一个：奇幻、科幻、武侠、仙侠、都市、历史、悬疑、推理、言情、恐怖、轻小说、现实、史诗、冒险、末世、游戏、穿越、重生、军事、竞技。如果都不匹配则返回"未分类"
- logline: 一句话梗概（字符串，不超过 200 字）

示例输入：
《星穹之下》奇幻小说。林夜发现星空是巨大的生物外壳。

示例输出：
{"title": "星穹之下", "genre": "奇幻", "logline": "林夜发现星空是巨大的生物外壳"}

请只输出 JSON，不要任何额外说明。"""

CHARACTER_SYSTEM_PROMPT = """你是一个小说角色分析专家。从用户提供的文本中提取所有出现的角色信息。

请以严格的 JSON 数组格式返回（不要加 markdown 代码块标记），每个角色包含以下字段：
- name: 角色名称（字符串，必填）
- role: 角色定位（字符串，从以下选择：主角、反派、配角、盟友、导师、恋人、对手、未指定）
- goal: 角色目标（字符串，角色想要什么，没有则填""）
- need: 内在需求（字符串，角色真正需要什么，没有则填""）
- backstory: 背景故事（字符串，角色的过去经历，没有则填""）
- description: 外貌描述和性格特征（字符串，没有则填""）

要求：
1. 严格根据文本内容提取，不要编造信息
2. 不确定的字段留空字符串，不要猜测
3. 文本中的定位/目标/内在需求/背景故事/外貌描述等字段标签对应的内容，填入对应字段
4. 角色名称格式：中文名即可，不需要带括号内的英文或拼音
5. 如果文本中有多个角色，全部提取出来

请只输出 JSON 数组，不要任何额外说明。"""


def _parse_json_response(raw: str) -> Any | None:
    """尝试从 LLM 回复中解析 JSON，支持容错。"""
    raw = raw.strip()
    # 去掉可能的 markdown 代码块
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    raw = raw.strip()

    # 尝试直接解析
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 尝试提取JSON数组
    m = re.search(r'\[[\s\S]*\]', raw)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    # 尝试提取JSON对象
    m = re.search(r'\{[\s\S]*\}', raw)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    return None


class ImportParser:
    """从原始文本中提取结构化信息。支持 LLM 提取 + 正则 fallback。"""

    def __init__(self, provider: BaseProvider | None = None):
        self.llm = provider

    # ── LLM 调用 ──────────────────────────────────────────

    def _call_llm(self, system: str, user: str) -> str | None:
        """调用 LLM 并返回文本回复。失败返回 None。"""
        if not self.llm:
            return None
        try:
            resp = self.llm.complete([
                LLMMessage(role="system", content=system),
                LLMMessage(role="user", content=user),
            ])
            if resp.finished and resp.content.strip():
                return resp.content.strip()
        except Exception:
            pass
        return None

    # ── 故事前提提取 ──────────────────────────────────────

    def extract_premise(self, text: str) -> dict:
        """从文本中提取标题、类型、一句话梗概。优先使用 LLM。"""
        text = text.strip()
        if not text:
            return {"title": "", "genre": "", "logline": ""}

        # LLM 提取
        if self.llm:
            raw = self._call_llm(PREMISE_SYSTEM_PROMPT, text)
            if raw:
                parsed = _parse_json_response(raw)
                if isinstance(parsed, dict):
                    result = {
                        "title": str(parsed.get("title", "")),
                        "genre": str(parsed.get("genre", "")),
                        "logline": str(parsed.get("logline", "")),
                    }
                    result["_ai"] = True
                    return result

        # 正则 fallback
        result = self._extract_premise_regex(text)
        result["_ai"] = False
        return result

    # ── 角色提取 ──────────────────────────────────────────

    def extract_characters(self, text: str) -> list[dict]:
        """从文本中提取角色列表。优先使用 LLM。"""
        text = text.strip()
        if not text:
            return []

        # LLM 提取
        if self.llm:
            raw = self._call_llm(CHARACTER_SYSTEM_PROMPT, text)
            if raw:
                parsed = _parse_json_response(raw)
                if isinstance(parsed, list):
                    seen: set[str] = set()
                    result: list[dict] = []
                    for item in parsed:
                        name = str(item.get("name", "")).strip()
                        if not name or name in seen:
                            continue
                        seen.add(name)
                        result.append({
                            "name": name,
                            "role": str(item.get("role", "未指定")),
                            "goal": str(item.get("goal", "")),
                            "need": str(item.get("need", "")),
                            "backstory": str(item.get("backstory", "")),
                            "description": str(item.get("description", "")),
                        })
                    if result:
                        return result

        # 正则 fallback
        return self._extract_characters_regex(text)

    # ══════════════════════════════════════════════════════
    # 正则 fallback 方法（保持向后兼容）
    # ══════════════════════════════════════════════════════

    @staticmethod
    def _extract_premise_regex(text: str) -> dict:
        """正则方式提取前提（原 extract_premise 逻辑）。"""
        title = ""
        genre = ""
        body = text

        m = re.search(r'《([^》]+)》', text)
        if m:
            title = m.group(1).strip()
            body = text.replace(m.group(0), "").strip()

        if not title:
            m = re.search(r'(?:^|\n)\s*标题[：:]\s*([^\s:：]+)', text)
            if m:
                title = m.group(1).strip()

        if not title:
            first_line = text.split("\n")[0].strip()
            first_word = re.split(r'[\s，。、, ]', first_line)[0]
            if first_word and len(first_word) <= 6 and first_word not in GENRE_KEYWORDS:
                title = first_word
                body = text[len(first_word):].strip()
            elif first_line and len(first_line) <= 20:
                title = first_line
                body = "\n".join(text.split("\n")[1:]).strip()

        m = re.search(r'(?:类型|题材)[：:]\s*(\S+)', text)
        if m:
            genre = m.group(1).strip()
        else:
            for kw in GENRE_KEYWORDS:
                if kw in text:
                    genre = kw
                    break

        logline = body.strip()
        logline = re.sub(r'\s+', ' ', logline)
        logline = logline[:200]

        return {"title": title, "genre": genre, "logline": logline}

    @staticmethod
    def _is_likely_name(word: str) -> bool:
        if len(word) < 2 or len(word) > 4:
            return False
        return word[0] in SURNAMES

    @staticmethod
    def _extract_characters_regex(text: str) -> list[dict]:
        """正则方式提取角色（原 extract_characters 逻辑）。"""
        text = text.strip()
        if not text:
            return []

        found: list[dict] = []
        seen: set[str] = set()
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            m = re.match(r'^([一-鿿]{2,4})[：:]\s*(.+)', line)
            if m:
                candidate_name = m.group(1)
                if candidate_name not in ROLE_KEYWORDS and not any(
                    candidate_name.startswith(rk) for rk in ROLE_KEYWORDS
                ):
                    name = candidate_name
                    rest = m.group(2)
                else:
                    name = ""
                    rest = line
            else:
                name = ""
                rest = line

            prefix_role = ""
            if not name:
                for rk in ROLE_KEYWORDS:
                    if line.startswith(rk):
                        after = line[len(rk):].strip()
                        after = re.sub(r'^[：:，,\s]+', '', after)
                        after_name = re.split(r'[：:，,\s]', after)[0]
                        if after_name and ImportParser._is_likely_name(after_name):
                            name = after_name
                            prefix_role = rk
                            rest = line
                            break

            if not name:
                pat = re.compile(r'([一-鿿]{2,4})[（(](' + "|".join(ROLE_KEYWORDS) + r')[）)]')
                pos = 0
                while pos < len(line):
                    m = pat.search(line, pos)
                    if not m:
                        break
                    candidate = m.group(1)
                    if ImportParser._is_likely_name(candidate):
                        name = candidate
                        break
                    pos = m.start() + 1

            if not name:
                m = re.search(r'名(?:字|叫|为)[：:：\s]*([一-鿿]{2,3}?)', line)
                if m:
                    name = m.group(1)

            if not name or name in seen:
                continue

            char_info: dict = {
                "name": name,
                "role": "未指定",
                "goal": "",
                "need": "",
                "backstory": "",
                "description": "",
            }

            role_map = {
                "主角": "主角", "女主角": "主角", "男主角": "主角", "主人公": "主角",
                "反派": "反派", "配角": "配角", "盟友": "盟友",
                "导师": "导师", "恋人": "恋人", "对手": "对手",
            }
            if prefix_role:
                char_info["role"] = role_map.get(prefix_role, prefix_role)
            else:
                for rk in ROLE_KEYWORDS:
                    if rk in rest:
                        char_info["role"] = role_map.get(rk, rk)
                        break

            goal_m = re.search(r'(?:目标|想要|希望|试图)[：:]\s*([^。\n]+)', rest)
            if not goal_m:
                goal_m = re.search(r'(?:为了|渴望)[：:]\s*([^。\n]+)', rest)
            if goal_m:
                char_info["goal"] = goal_m.group(1).strip()
            else:
                rest_clean = re.sub("|".join(ROLE_KEYWORDS), "", rest).strip()
                if rest_clean and len(rest_clean) > 4:
                    char_info["description"] = rest_clean[:100]

            need_m = re.search(r'(?:需要|真正需要|渴望|缺乏)[：:]\s*([^。\n]+)', rest)
            if need_m:
                char_info["need"] = need_m.group(1).strip()

            seen.add(name)
            found.append(char_info)

        if not found:
            for verb in NAME_VERBS:
                pattern = rf'([一-鿿]{{2,3}}){verb}'
                for m in re.finditer(pattern, text):
                    candidate = m.group(1)
                    if ImportParser._is_likely_name(candidate) and candidate not in seen:
                        seen.add(candidate)
                        sentence_pattern = rf'[^。\n]*{re.escape(candidate)}[^。\n]*'
                        sent_m = re.search(sentence_pattern, text)
                        desc = sent_m.group(0).strip() if sent_m else ""
                        found.append({
                            "name": candidate,
                            "role": "未指定",
                            "goal": "",
                            "need": "",
                            "backstory": "",
                            "description": desc[:100],
                        })

        return found
