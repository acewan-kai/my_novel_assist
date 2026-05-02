"""Import parser — extract premise and character info from raw Chinese text."""

from __future__ import annotations

import re

# 常见中文姓氏（前 100）
SURNAMES: set[str] = set(
    "王李张刘陈杨赵黄周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐"
    "冯于董萧程曹袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘"
    "杜戴夏钟汪田任姜范方石姚谭廖邹熊金陆郝孔白崔康毛邱秦"
    "江史顾侯邵孟龙万段漕钱汤尹黎易常武乔贺赖龚文"
)

# 角色定位关键词
ROLE_KEYWORDS: list[str] = [
    "主角", "反派", "配角", "盟友", "导师", "恋人", "对手",
    "女主角", "男主角", "主人公",
]

# 小说类型关键词
GENRE_KEYWORDS: list[str] = [
    "奇幻", "科幻", "武侠", "仙侠", "都市", "历史", "悬疑",
    "推理", "言情", "恐怖", "轻小说", "现实", "史诗", "冒险",
    "末世", "游戏", "穿越", "重生", "军事", "竞技",
]

# 常见动词（用于姓名后置判断）
NAME_VERBS: list[str] = [
    "说", "道", "问", "答", "走", "看", "听", "想",
    "发现", "觉得", "感到", "知道", "看见", "听见",
    "是", "有", "去", "来", "坐", "站", "笑", "哭",
]


class ImportParser:
    """从原始文本中提取结构化信息。"""

    # ── 故事前提提取 ──────────────────────────────────────

    @staticmethod
    def extract_premise(text: str) -> dict:
        """从文本中提取标题、类型、一句话梗概。

        支持格式:
        - 《标题》类型：type。正文……
        - 标题：xxx  类型：xxx  正文
        - 纯文本：首行或《》为标题，匹配类型词，其余为梗概
        """
        text = text.strip()
        if not text:
            return {"title": "", "genre": "", "logline": ""}

        title = ""
        genre = ""
        body = text

        # 1. 提取《标题》
        m = re.search(r'《([^》]+)》', text)
        if m:
            title = m.group(1).strip()
            body = text.replace(m.group(0), "").strip()

        # 2. 尝试从 "标题：xxx" 格式提取
        if not title:
            m = re.search(r'(?:^|\n)\s*标题[：:]\s*([^\s:：]+)', text)
            if m:
                title = m.group(1).strip()

        # 3. 尝试从首行提取（没有《》时）
        if not title:
            first_line = text.split("\n")[0].strip()
            # 首行第一个词（空格/标点分隔）可能是标题
            first_word = re.split(r'[\s，。、, ]', first_line)[0]
            if first_word and len(first_word) <= 6 and first_word not in GENRE_KEYWORDS:
                title = first_word
                body = text[len(first_word):].strip()
            elif first_line and len(first_line) <= 20:
                title = first_line
                body = "\n".join(text.split("\n")[1:]).strip()

        # 4. 提取类型
        #    尝试 "类型：xxx" 模式
        m = re.search(r'(?:类型|题材)[：:]\s*(\S+)', text)
        if m:
            genre = m.group(1).strip()
        else:
            # 遍历类型关键词
            for kw in GENRE_KEYWORDS:
                if kw in text:
                    genre = kw
                    break

        # 5. 剩余内容作为梗概
        logline = body.strip()
        logline = re.sub(r'\s+', ' ', logline)  # 合并空白
        logline = logline[:200]  # 截断过长文本

        return {"title": title, "genre": genre, "logline": logline}

    # ── 角色提取 ──────────────────────────────────────────

    @staticmethod
    def _is_likely_name(word: str) -> bool:
        """判断是否像中文姓名（2-4 字，首字为姓氏）。"""
        if len(word) < 2 or len(word) > 4:
            return False
        return word[0] in SURNAMES

    @staticmethod
    def extract_characters(text: str) -> list[dict]:
        """从文本中提取角色列表。

        支持的格式:
        - 角色名：描述（role标识）
        - 主角/反派 XXX
        - XXX（主角/反派）
        - 天然段落包含角色信息
        """
        text = text.strip()
        if not text:
            return []

        found: list[dict] = []
        seen: set[str] = set()

        lines = text.split("\n")

        # Phase 1: 逐行扫描
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 模式: "角色名：描述"（排除角色关键词本身）
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

            # 如果没有匹配到"角色名：", 尝试找"主角/反派 XXX"
            prefix_role = ""
            if not name:
                for rk in ROLE_KEYWORDS:
                    if line.startswith(rk):
                        after = line[len(rk):].strip()
                        after = re.sub(r'^[：:，,\s]+', '', after)
                        # 取 : 或 前的内容作为可能的姓名
                        after_name = re.split(r'[：:，,\s]', after)[0]
                        if after_name and ImportParser._is_likely_name(after_name):
                            name = after_name
                            prefix_role = rk
                            rest = line
                            break
                            rest = after
                            break

            # 如果还没有 name, 尝试找 XXX（角色），逐位置扫描避免重叠漏匹配
            if not name:
                pat = re.compile(r'([一-鿿]{2,4})[（(](' + '|'.join(ROLE_KEYWORDS) + r')[）)]')
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

            # 如果还没有 name, 尝试找"名叫XXX" / "名为XXX"
            if not name:
                m = re.search(r'名(?:字|叫|为)[：:：\s]*([一-鿿]{2,3}?)', line)
                if m:
                    name = m.group(1)

            if not name or name in seen:
                continue

            # 提取角色信息
            char_info: dict = {
                "name": name,
                "role": "未指定",
                "goal": "",
                "need": "",
                "backstory": "",
                "description": "",
            }

            # 提取角色定位
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

            # 提取目标（想要/希望/试图/目标：）
            goal_m = re.search(r'(?:目标|想要|希望|试图)[：:]\s*([^。\n]+)', rest)
            if not goal_m:
                goal_m = re.search(r'(?:为了|渴望)[：:]\s*([^。\n]+)', rest)
            if goal_m:
                char_info["goal"] = goal_m.group(1).strip()
            else:
                # 从 role 行后的内容推断
                rest_clean = re.sub(r'|'.join(ROLE_KEYWORDS), '', rest).strip()
                if rest_clean and len(rest_clean) > 4:
                    char_info["description"] = rest_clean[:100]

            # 提取内在需求（需要/真正需要/渴望）
            need_m = re.search(r'(?:需要|真正需要|渴望|缺乏)[：:]\s*([^。\n]+)', rest)
            if need_m:
                char_info["need"] = need_m.group(1).strip()

            seen.add(name)
            found.append(char_info)

        # Phase 2: 如果 Phase 1 没找到，尝试用姓氏 + 动词模式
        if not found:
            # 找 "XXX说" "XXX发现" 等模式
            for verb in NAME_VERBS:
                pattern = rf'([一-鿿]{{2,3}}){verb}'
                for m in re.finditer(pattern, text):
                    candidate = m.group(1)
                    if ImportParser._is_likely_name(candidate) and candidate not in seen:
                        seen.add(candidate)
                        # 获取包含该角色的句子作为描述
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


parser = ImportParser()
