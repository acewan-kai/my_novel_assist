"""Streamlit UI — 全中文界面，闭环工作流：设定 → 规划 → 写作 → 审核。"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="My Novel Assist", layout="wide")

# ── 导入 ──────────────────────────────────────────────────
from app.validators.metrics import QualityMetrics
from app.validators.audit_33 import Audit33Validator
from app.validators.de_ai import DeAIFilter
from app.validators.post_write import PostWriteValidator
from app.narrative.engine import NarrativeEngine, NARRATIVE_STAGES
from app.schema.registry import SchemaRegistry
from app.context.dsl_parser import DSLParser
from app.state.delta import DeltaStore
from app.llm.provider_bank import PROVIDER_BANK


# ═══════════════════════════════════════════════════════════
# 会话状态 — 跨 Tab 数据流通
# ═══════════════════════════════════════════════════════════
def _init_session_state():
    """初始化所有会话状态键，确保 Tab 间数据流通。"""
    if "premise" not in st.session_state:
        st.session_state.premise = {"title": "", "genre": "", "logline": ""}
    if "characters" not in st.session_state:
        st.session_state.characters = []
    if "narrative_beats" not in st.session_state:
        st.session_state.narrative_beats = {}       # {chapter: [beat_names]}
    if "total_chapters" not in st.session_state:
        st.session_state.total_chapters = 20
    if "generated_chapters" not in st.session_state:
        st.session_state.generated_chapters = {}    # {ch_num: {content, ...}}
    if "current_generation" not in st.session_state:
        st.session_state.current_generation = None
    if "delta_store" not in st.session_state:
        st.session_state.delta_store = DeltaStore()

_init_session_state()

st.title("📖 My Novel Assist")
st.caption("AI 辅助小说写作工具 —— 从灵感到成稿的全流程支持")

tab_names = [
    "📐 故事设定",
    "📈 叙事规划",
    "✍️ 生成章节",
    "🔍 质量审核",
    "🤖 去 AI 检测",
    "✅ 后写作校验",
    "📊 质量指标",
    "🔤 DSL 解析",
    "🏪 LLM 提供商",
    "📝 状态追踪",
]
tabs = st.tabs(tab_names)


# ═══════════════════════════════════════════════════════════
# Tab 1：故事设定
# ═══════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("故事前提验证")

    col1, col2, col3 = st.columns(3)
    with col1:
        title = st.text_input("小说标题", st.session_state.premise.get("title", ""))
    with col2:
        genre = st.text_input("类型", st.session_state.premise.get("genre", ""))
    with col3:
        logline = st.text_input("一句话梗概", st.session_state.premise.get("logline", ""))

    if st.button("验证并保存故事前提", use_container_width=True, type="primary"):
        sr = SchemaRegistry()
        ok, errors, score = sr.validate_scored("story_premise", {
            "title": title, "genre": genre, "logline": logline
        })
        # 保存到会话状态
        st.session_state.premise = {"title": title, "genre": genre, "logline": logline}
        # 自动记录到 DeltaStore
        ds = st.session_state.delta_store
        ds.record("premise.title", "", title, "user")
        ds.record("premise.genre", "", genre, "user")

        st.progress(score, text=f"完整度评分：{score:.0%}")
        if ok:
            st.success("✓ 故事前提验证通过，已保存")
        else:
            st.warning(f"前提可改进（评分 {score:.0%}）")
            for e in errors:
                st.error(e)

    st.divider()
    st.subheader("角色管理")

    if st.button("从前提导入主角"):
        premise = st.session_state.premise
        existing = [c["name"] for c in st.session_state.characters]
        # 尝试从 logline 提取第一个角色名（"..."之前的部分）
        logline_text = premise.get("logline", "")
        if logline_text:
            # 简单启发：logline 开头的人名
            name_hint = logline_text.split("发现")[0].split("的")[-1].strip()[:4] if "发现" in logline_text else ""
        else:
            name_hint = ""
        if name_hint and name_hint not in existing and len(name_hint) >= 2:
            st.session_state.characters.append({
                "name": name_hint, "role": "主角",
                "description": f"来自《{premise.get('title','')}》的主角"
            })
            st.success(f"已自动添加主角：{name_hint}")
            st.rerun()
        else:
            st.info("未能自动提取角色名，请手动添加")

    with st.container(border=True):
        st.caption("添加新角色")
        c1, c2 = st.columns(2)
        with c1:
            new_name = st.text_input("角色名称", key="char_name")
        with c2:
            new_role = st.text_input("角色定位", key="char_role",
                                     placeholder="主角 / 反派 / 盟友 / 导师")
        c3, c4 = st.columns(2)
        with c3:
            new_goal = st.text_input("角色目标 (goal)", key="char_goal",
                                     placeholder="角色想要什么")
        with c4:
            new_need = st.text_input("内在需求 (need)", key="char_need",
                                     placeholder="角色真正需要什么")
        new_backstory = st.text_area("背景故事 (backstory)", key="char_backstory",
                                      placeholder="角色的过去经历、动机来源……",
                                      height=80)
        new_desc = st.text_input("角色描述", key="char_desc",
                                 placeholder="外貌、性格等")

        if st.button("添加角色", use_container_width=True):
            if new_name.strip():
                st.session_state.characters.append({
                    "name": new_name.strip(),
                    "role": new_role.strip() or "未指定",
                    "goal": new_goal.strip(),
                    "need": new_need.strip(),
                    "backstory": new_backstory.strip(),
                    "description": new_desc.strip() or "暂无描述",
                })
                st.session_state.delta_store.record("characters", "", new_name.strip(), "user")
                st.success(f"已添加角色：{new_name.strip()}")
                st.rerun()
            else:
                st.error("角色名称不能为空")

    if st.session_state.characters:
        st.caption(f"已添加 {len(st.session_state.characters)} 个角色")
        sr = SchemaRegistry()
        char_data = []
        for i, c in enumerate(st.session_state.characters):
            _ok, _errs, _score = sr.validate_scored("character", c)
            char_data.append({
                "序号": i + 1,
                "名称": c["name"],
                "定位": c["role"],
                "描述": c["description"][:25] + "…" if len(c["description"]) > 25 else c["description"],
                "完整度": f"{_score:.0%}",
            })
        st.dataframe(char_data, use_container_width=True, hide_index=True)

        with st.expander("角色完整度详情"):
            for c in st.session_state.characters:
                _ok, _errs, _score = sr.validate_scored("character", c)
                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.metric(c["name"], f"{_score:.0%}")
                with col_b:
                    if _errs:
                        for e in _errs:
                            st.caption(f"⚠ {e}")
                    else:
                        st.caption("✓ 角色信息完整")

        if st.button("批量验证角色", use_container_width=True):
            sr = SchemaRegistry()
            all_ok = True
            for c in st.session_state.characters:
                ok, errors = sr.validate("character", {"name": c["name"], "role": c["role"]})
                if ok:
                    st.success(f"✓ {c['name']} Schema 验证通过")
                else:
                    all_ok = False
                    for e in errors:
                        st.error(f"{c['name']}: {e}")
            if all_ok:
                st.success("全部角色 Schema 验证通过")

        with st.expander("删除角色"):
            del_names = [c["name"] for c in st.session_state.characters]
            to_del = st.multiselect("选择要删除的角色", del_names)
            if st.button("删除选中角色"):
                st.session_state.characters = [
                    c for c in st.session_state.characters if c["name"] not in to_del
                ]
                st.rerun()
    else:
        st.info("尚未添加任何角色，请在上方表单中添加")


# ═══════════════════════════════════════════════════════════
# Tab 2：叙事规划
# ═══════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("叙事引擎 — 16 阶段 Dramatica 结构")

    # 从 Tab 1 读取故事设定
    premise = st.session_state.get("premise", {})
    characters = st.session_state.get("characters", [])

    if premise.get("title"):
        st.info(f"📖 当前故事：**{premise['title']}**（{premise.get('genre', '未设定类型')}）")
    if characters:
        st.caption(f"👥 已注册角色：{'、'.join(c['name'] for c in characters)}")

    ne = NarrativeEngine()

    stage_data = []
    for i, stage in enumerate(NARRATIVE_STAGES):
        prompt = ne.get_stage_prompt_cn(stage)
        stage_data.append({"序号": i + 1, "阶段名称": ne.get_stage_name_cn(stage), "写作提示": prompt[:80] + "…"})
    st.dataframe(stage_data, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("章节节奏规划")

    total = st.number_input("总章节数", 1, 100,
                            value=st.session_state.total_chapters,
                            key="total_ch_input")

    # 展示全部章节的节奏预览
    st.caption(f"全书 {total} 章的叙事节奏分配：")
    beat_preview = []
    for ch_num in range(1, total + 1):
        cn_beats = ne.get_required_beats_cn(ch_num, total)
        beat_preview.append({
            "章节": f"第 {ch_num} 章",
            "叙事阶段": " → ".join(cn_beats),
        })
    st.dataframe(beat_preview, use_container_width=True, hide_index=True)

    if st.button("确认节奏规划", use_container_width=True, type="primary"):
        beats_map = {}
        for ch_num in range(1, total + 1):
            beats_map[ch_num] = ne.get_required_beats(ch_num, total)
        st.session_state.narrative_beats = beats_map
        st.session_state.total_chapters = total
        st.session_state.delta_store.record("total_chapters", "", total, "user")
        st.success(f"✓ 已保存 {total} 章的节奏规划，可前往「生成章节」Tab 开始写作")

    # 显示已保存的规划状态
    if st.session_state.narrative_beats:
        st.divider()
        st.caption("✅ 节奏规划已确认")

    st.divider()
    st.subheader("前 8 章进度模拟")
    sim_cols = st.columns(4)
    for i in range(8):
        with sim_cols[i % 4]:
            cn_b = ne.get_required_beats_cn(i + 1, 20)
            st.caption(f"第 {i+1} 章")
            st.write("、".join(cn_b))


# ═══════════════════════════════════════════════════════════
# Tab 3：生成章节
# ═══════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("✍️ 生成章节 — 7 Agent 管线")

    characters = st.session_state.get("characters", [])
    premise = st.session_state.get("premise", {})
    narrative_beats = st.session_state.get("narrative_beats", {})

    # 显示当前故事上下文
    if premise.get("title"):
        st.info(f"📖 {premise['title']}（{premise.get('genre', '')}）")
    with st.container(border=True):
        st.caption("章节参数")
        col1, col2 = st.columns(2)
        with col1:
            gen_chapter = st.number_input("章节号", 1, 100, 1)
        with col2:
            gen_title = st.text_input("章节标题（可选）", "第一章 星空异象")

        gen_pov = st.selectbox(
            "叙事视角（POV 角色）",
            [c["name"] for c in characters] if characters else ["林夜"],
            help="选择此章节的视角角色。可在「故事设定」Tab 中添加更多角色。"
        )

        # 显示叙事阶段提示
        chapter_beats = narrative_beats.get(gen_chapter, [])
        ne = NarrativeEngine()
        cn_beats = [ne.get_stage_name_cn(b) for b in chapter_beats]
        if chapter_beats:
            beat_info = " → ".join(cn_beats)
            st.success(f"📈 本章叙事阶段：{beat_info}")
            for b in chapter_beats:
                cn = ne.get_stage_name_cn(b)
                prompt = ne.get_stage_prompt_cn(b)
                st.caption(f"  • {cn}：{prompt}")

        gen_outline = st.text_area(
            "章节大纲",
            value=f"本章叙事阶段：{' → '.join(cn_beats)}\n\n" if cn_beats else "",
            height=120,
            help="描述本章要发生的情节"
        )

        gen_context = st.text_area(
            "世界观上下文（可选）",
            value=f"故事类型：{premise.get('genre', '未设定')}\n" if premise.get("genre") else "",
            height=80,
        )

    # 检查 API 服务器
    import httpx

    server_ok = False
    server_url = "http://localhost:8000"
    try:
        r = httpx.get(f"{server_url}/api/health", timeout=2)
        server_ok = r.status_code == 200
    except Exception:
        server_ok = False

    if not server_ok:
        st.warning(
            "⚠️ API 服务器未运行。生成章节需要先启动后端服务器并配置 LLM API Key。\n\n"
            "**启动方法：**\n"
            "```\n"
            "cd backend\n"
            "python -m app.cli server\n"
            "```\n\n"
            "**配置 API Key：**\n"
            "在项目根目录创建 `.env` 文件：\n"
            "```\n"
            "LLM_PROVIDER=openai|deepseek|anthropic|ollama\n"
            "OPENAI_API_KEY=sk-xxx\n"
            "```\n\n"
            "也可先手动撰写章节内容，然后使用「质量审核」等 Tab 进行校验。"
        )

    gen_disabled = not server_ok
    if st.button("开始生成", use_container_width=True, type="primary", disabled=gen_disabled):
        if not server_ok:
            st.error("API 服务器不可用")
        else:
            with st.spinner("7 Agent 管线运行中：规划 → 架构 → 写作 → 审核 → 修订 → 观察 → 总结……"):
                try:
                    resp = httpx.post(
                        f"{server_url}/api/generate/chapter",
                        json={
                            "project_id": "streamlit_ui",
                            "chapter_number": gen_chapter,
                            "outline": gen_outline or f"第 {gen_chapter} 章",
                            "world_context": gen_context,
                            "pov_character": gen_pov,
                            "prior_summary": "",
                        },
                        timeout=300,
                    )
                    data = resp.json()
                except httpx.TimeoutException:
                    st.error("生成超时")
                    data = None
                except Exception as e:
                    st.error(f"请求失败：{e}")
                    data = None

            if data and data.get("success"):
                ch_num = data["chapter_number"]
                content = data.get("content", "")

                # 保存到会话状态
                st.session_state.generated_chapters[ch_num] = {
                    "content": content,
                    "passed_audit": data.get("passed_audit", False),
                    "phases": data.get("phases", []),
                    "audit_report": data.get("audit_report", ""),
                    "observer_notes": data.get("observer_notes", ""),
                    "summary": data.get("summary", ""),
                }
                st.session_state.current_generation = st.session_state.generated_chapters[ch_num]
                st.session_state.delta_store.record(
                    f"chapter_{ch_num}_generated", "", "done", "system"
                )

                st.success(f"✓ 第 {ch_num} 章生成成功！")
                with st.container(border=True):
                    st.markdown(content)

                phases = data.get("phases", [])
                if phases:
                    st.subheader("管线阶段状态")
                    phase_data = []
                    for p in phases:
                        phase_data.append({
                            "阶段": p.get("name", ""),
                            "状态": "✅" if p.get("success") else "❌",
                            "耗时(秒)": round(p.get("duration_ms", 0) / 1000, 1),
                            "错误": p.get("error", "") or "-",
                        })
                    st.dataframe(phase_data, use_container_width=True, hide_index=True)

                if data.get("passed_audit"):
                    st.success("✓ 章节通过管线内置质量审核")
                else:
                    st.warning("⚠ 章节未通过内置审核，建议切换到「质量审核」Tab 手动检查")

                st.info("💡 生成的文本已保存，可切换到「质量审核」「去 AI 检测」等 Tab 查看（从下拉框选择此章节）")

            elif data:
                st.error(f"生成失败：{data.get('error', '未知错误')}")

    # 显示已保存的章节列表
    gen_chapters = st.session_state.get("generated_chapters", {})
    if gen_chapters:
        st.divider()
        st.caption(f"✅ 已生成 {len(gen_chapters)} 个章节：")
        ch_list = ", ".join(str(k) for k in sorted(gen_chapters.keys()))
        st.write(f"第 {ch_list} 章")
        for ch_num, gen_data in sorted(gen_chapters.items()):
            with st.expander(f"第 {ch_num} 章预览（{'通过' if gen_data.get('passed_audit') else '未审核'}）"):
                st.markdown(gen_data.get("content", "（空）")[:500] + "…")


# ═══════════════════════════════════════════════════════════
# Tab 4：质量审核 — 支持从已生成章节自动填充
# ═══════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("33 维质量审核")

    gen_chapters = st.session_state.get("generated_chapters", {})
    sample_audit = "突然间，全场震惊。然而，他不由得感到一阵寒意。仿佛世界在旋转。"

    # 章节选择器
    if gen_chapters:
        ch_options = sorted(gen_chapters.keys())
        selected_ch = st.selectbox("选择已生成章节（自动填充）", [""] + ch_options,
                                   format_func=lambda x: f"第 {x} 章" if x else "手动输入")
        default_audit = gen_chapters[selected_ch]["content"] if selected_ch else sample_audit
    else:
        default_audit = sample_audit

    audit_text = st.text_area("待审核文本", default_audit, height=150)

    if st.button("运行审核", use_container_width=True, type="primary"):
        auditor = Audit33Validator()
        result = auditor.audit(audit_text)

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("综合评分", f"{result.overall:.2f}")
        col_b.metric("是否通过", "✅ 通过" if result.passed else "❌ 未通过")
        col_c.metric("问题数量", len(result.issues))

        if result.issues:
            st.subheader("发现的问题")
            for i in result.issues:
                sev = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
                st.write(f"{sev.get(i.severity, '⚪')} **{i.dimension}**（{i.severity}）：{i.message}")

        st.subheader("各维度得分")
        for dim, score in result.scores.items():
            st.progress(min(score, 1.0), text=f"{dim}：{score:.2f}")

        if selected_ch:
            st.info("💡 可将修改后的文本粘贴回「生成章节」Tab 覆盖保存")


# ═══════════════════════════════════════════════════════════
# Tab 5：去 AI 检测 — 支持从已生成章节自动填充
# ═══════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("去 AI 化 — AI 写作痕迹检测")

    gen_chapters = st.session_state.get("generated_chapters", {})
    sample_deai = "首先，让我们探讨这个问题。其次，我们需要分析数据。最后，值得注意的是结论。"

    if gen_chapters:
        ch_options = sorted(gen_chapters.keys())
        selected_ch = st.selectbox("选择已生成章节（自动填充）", [""] + ch_options,
                                   format_func=lambda x: f"第 {x} 章" if x else "手动输入",
                                   key="deai_ch_select")
        default_deai = gen_chapters[selected_ch]["content"] if selected_ch else sample_deai
    else:
        default_deai = sample_deai

    deai_text = st.text_area("待分析文本", default_deai, height=150)

    if st.button("分析", use_container_width=True, type="primary"):
        deai = DeAIFilter()
        result = deai.analyze(deai_text)

        score = result.ai_score
        if score < 0.3:
            st.success(f"AI 分数：{score:.2f} — 看起来像人类写作")
        elif score < 0.6:
            st.warning(f"AI 分数：{score:.2f} — 检测到部分 AI 模式")
        else:
            st.error(f"AI 分数：{score:.2f} — 大量 AI 痕迹")

        st.metric("是否通过阈值", "✅ 通过" if result.passes else "❌ 未通过")

        if result.issues:
            st.subheader("检测到的模式")
            for i in result.issues:
                st.write(f"- **{i.pattern}**（{i.severity}）：{i.suggestion}")


# ═══════════════════════════════════════════════════════════
# Tab 6：后写作校验 — 支持从已生成章节自动填充
# ═══════════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("后写作校验")

    gen_chapters = st.session_state.get("generated_chapters", {})
    sample_v = "林夜猛然抬头，星空在头顶旋转。不，不是旋转——它们在移动，像是有生命的。"

    if gen_chapters:
        ch_options = sorted(gen_chapters.keys())
        selected_ch = st.selectbox("选择已生成章节（自动填充）", [""] + ch_options,
                                   format_func=lambda x: f"第 {x} 章" if x else "手动输入",
                                   key="val_ch_select")
        default_val = gen_chapters[selected_ch]["content"] if selected_ch else sample_v
    else:
        default_val = sample_v

    val_text = st.text_area("待校验文本", default_val, height=150)
    min_words = st.slider("最低字数要求", 10, 1000, 50)

    if st.button("开始校验", use_container_width=True, type="primary"):
        v = PostWriteValidator(min_words=min_words)
        result = v.validate(val_text)

        if result.passed:
            st.success("✓ 校验通过")
        else:
            st.error("✗ 校验未通过")

        col1, col2 = st.columns(2)
        col1.metric("字数", int(result.metrics.get("word_count", 0)))
        col2.metric("质量评分", f"{result.metrics.get('quality_score', 0):.2f}")

        if result.errors:
            st.subheader("错误")
            for e in result.errors:
                st.error(e)
        if result.warnings:
            st.subheader("警告")
            for w in result.warnings:
                st.warning(w)


# ═══════════════════════════════════════════════════════════
# Tab 7：质量指标
# ═══════════════════════════════════════════════════════════
with tabs[6]:
    st.subheader("质量指标计算器")

    # 如果已生成章节，尝试从管线数据填充默认值
    gen = st.session_state.get("current_generation")
    default_coherence = 0.85
    default_integration = 0.72
    default_polish = 0.68

    if gen:
        phases = gen.get("phases", [])
        for p in phases:
            if p.get("name", "").startswith("auditor"):
                # 如果有管线审核分数，可尝试解析（目前存为文本）
                pass

    c1, c2, c3 = st.columns(3)
    with c1:
        coherence = st.slider("连贯性", 0.0, 1.0, default_coherence, 0.05)
    with c2:
        integration = st.slider("整合性", 0.0, 1.0, default_integration, 0.05)
    with c3:
        polish = st.slider("润色度", 0.0, 1.0, default_polish, 0.05)

    qm = QualityMetrics(coherence=coherence, integration=integration, polish=polish)

    st.metric("综合评分", f"{qm.overall:.2f}",
              delta="通过" if qm.passed else "未通过",
              delta_color="normal" if qm.passed else "off")

    st.progress(qm.overall, text="整体质量")

    st.json(qm.to_dict())


# ═══════════════════════════════════════════════════════════
# Tab 8：DSL 解析
# ═══════════════════════════════════════════════════════════
with tabs[7]:
    st.subheader("@DSL 模板解析器")

    dsl_input = st.text_input("DSL 模板（支持 @title、@type:类型、@self 等）", "@title 遇到了 @type:character")
    if dsl_input:
        parser = DSLParser()
        matches = parser.parse(dsl_input)
        if matches:
            st.dataframe([{"类型": m.qtype, "目标": m.target,
                          "字段": m.field, "有效": m.valid} for m in matches],
                        use_container_width=True, hide_index=True)
        else:
            st.info("未找到 @DSL 模式")

    st.divider()
    st.subheader("模板注入演示")
    template = st.text_input("注入模板", "在 @type:location，@title 遇到了 @type:character……")
    if template:
        parser = DSLParser()
        found = parser.parse(template)
        st.write(f"**发现 {len(found)} 个注入点**")
        for m in found:
            st.write(f"- `{m.raw}` → 通过 {m.qtype} 解析")


# ═══════════════════════════════════════════════════════════
# Tab 9：LLM 提供商
# ═══════════════════════════════════════════════════════════
with tabs[8]:
    st.subheader("LLM 提供商一览")

    pdata = []
    for name, info in PROVIDER_BANK.items():
        pdata.append({
            "提供商": info.name,
            "默认模型": info.default_model,
            "API 地址": info.base_url or "（本地）",
            "环境变量": info.api_key_env or "-",
            "模型列表": "、".join(info.models[:4]),
            "本地": "✅" if info.local else "",
        })

    st.dataframe(pdata, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("配置说明")
    st.code("LLM_PROVIDER=openai|deepseek|anthropic|google|ollama|custom\n"
            "OPENAI_API_KEY=sk-...\n"
            "ANTHROPIC_API_KEY=sk-ant-...\n"
            "DEEPSEEK_API_KEY=sk-...", language="bash")
    st.info("在项目根目录的 .env 文件中设置以上环境变量即可切换 LLM 提供商。\n"
            "配置完成后启动 API 服务器（python -m app.cli server），即可在「生成章节」Tab 使用 7-Agent 管线。")


# ═══════════════════════════════════════════════════════════
# Tab 10：状态追踪
# ═══════════════════════════════════════════════════════════
with tabs[9]:
    st.subheader("状态变更追踪")

    ds = st.session_state.delta_store

    col1, col2, col3 = st.columns(3)
    with col1:
        field = st.text_input("字段名", "chapter_1_status")
    with col2:
        old_v = st.text_input("旧值", "")
    with col3:
        new_v = st.text_input("新值", "")

    bcol1, bcol2, bcol3 = st.columns(3)
    with bcol1:
        if st.button("记录变更", use_container_width=True):
            ds.record(field, old_v, new_v, "user")
            st.rerun()
    with bcol2:
        if st.button("创建检查点", use_container_width=True):
            ds.checkpoint(f"cp_{len(ds.history)}")
            st.success("检查点已保存")
    with bcol3:
        if st.button("回滚", use_container_width=True):
            cp = [k for k in ds._checkpoints.keys()]
            if cp:
                ds.rollback(cp[-1])
                st.warning("已回滚到上一个检查点")
                st.rerun()

    if ds.history:
        st.subheader("变更历史")
        st.dataframe(
            [{"操作者": d.agent, "字段": d.field,
              "旧值": str(d.old_value)[:20], "新值": str(d.new_value)[:20],
              "时间": d.timestamp.split("T")[1][:8]} for d in ds.history],
            use_container_width=True, hide_index=True
        )

    if st.button("清除历史记录"):
        ds.clear()
        st.rerun()


st.caption("---\nMy Novel Assist v0.3.0 — 闭环工作流：设定 → 规划 → 写作 → 审核 → 发布")
