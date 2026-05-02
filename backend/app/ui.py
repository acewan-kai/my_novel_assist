"""Streamlit UI — 全中文界面，覆盖所有功能。"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="My Novel Assist", layout="wide")

# ── 导入所有模块 ─────────────────────────────────────────────
from app.validators.metrics import QualityMetrics
from app.validators.audit_33 import Audit33Validator
from app.validators.de_ai import DeAIFilter
from app.validators.post_write import PostWriteValidator
from app.narrative.engine import NarrativeEngine, NARRATIVE_STAGES
from app.schema.registry import SchemaRegistry
from app.context.dsl_parser import DSLParser
from app.state.delta import DeltaStore
from app.llm.provider_bank import PROVIDER_BANK


st.title("📖 My Novel Assist")
st.caption("AI 辅助小说写作工具 —— 从灵感到成稿的全流程支持")

# 工作流顺序：设定 → 规划 → 写作 → 审核 → 修改 → 发布
tab_names = [
    "📐 故事设定",     # 0: premise + characters
    "📈 叙事规划",     # 1: narrative engine (was tab 6)
    "✍️ 生成章节",     # 2: NEW — call API to generate
    "🔍 质量审核",     # 3: 33-dim audit (was tab 2)
    "🤖 去 AI 检测",   # 4: de-ai (was tab 3)
    "✅ 后写作校验",   # 5: validate (was tab 4)
    "📊 质量指标",     # 6: quality (was tab 5)
    "🔤 DSL 解析",     # 7: dsl (was tab 7)
    "🏪 LLM 提供商",   # 8: providers (was tab 8)
    "📝 状态追踪",     # 9: state (was tab 9)
]
tabs = st.tabs(tab_names)


# ═══════════════════════════════════════════════════════════
# Tab 1：故事设定 — 前提验证 + 角色管理
# ═══════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("故事前提验证")

    col1, col2, col3 = st.columns(3)
    with col1:
        title = st.text_input("小说标题", "星穹之下")
    with col2:
        genre = st.text_input("类型", "奇幻")
    with col3:
        logline = st.text_input("一句话梗概", "一个在天文台工作的青年发现星空是巨大生物的外壳")

    if st.button("验证故事前提", use_container_width=True):
        sr = SchemaRegistry()
        ok, errors = sr.validate("story_premise", {
            "title": title, "genre": genre, "logline": logline
        })
        if ok:
            st.success("✓ 故事前提验证通过")
        else:
            for e in errors:
                st.error(e)

    st.divider()
    st.subheader("角色管理")

    if "characters" not in st.session_state:
        st.session_state.characters = []

    with st.container(border=True):
        st.caption("添加新角色")
        c1, c2, c3 = st.columns(3)
        with c1:
            new_name = st.text_input("角色名称", key="char_name")
        with c2:
            new_role = st.text_input("角色定位", key="char_role",
                                     placeholder="protagonist / antagonist / ally / mentor")
        with c3:
            new_desc = st.text_input("角色描述", key="char_desc",
                                     placeholder="外貌、性格、背景等")

        if st.button("添加角色", use_container_width=True, type="primary"):
            if new_name.strip():
                st.session_state.characters.append({
                    "name": new_name.strip(),
                    "role": new_role.strip() or "未指定",
                    "description": new_desc.strip() or "暂无描述"
                })
                st.success(f"已添加角色：{new_name.strip()}")
            else:
                st.error("角色名称不能为空")

    if st.session_state.characters:
        st.caption(f"已添加 {len(st.session_state.characters)} 个角色")
        char_data = []
        for i, c in enumerate(st.session_state.characters):
            char_data.append({
                "序号": i + 1,
                "名称": c["name"],
                "定位": c["role"],
                "描述": c["description"][:30] + "..." if len(c["description"]) > 30 else c["description"],
            })
        st.dataframe(char_data, use_container_width=True, hide_index=True)

        if st.button("验证所有角色 Schema", use_container_width=True):
            sr = SchemaRegistry()
            all_ok = True
            for c in st.session_state.characters:
                ok, errors = sr.validate("character", {"name": c["name"], "role": c["role"]})
                if ok:
                    st.success(f"✓ {c['name']} 验证通过")
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
# Tab 2：叙事规划 — Dramatica 16 阶段 + 章节节奏
# ═══════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("叙事引擎 — 16 阶段 Dramatica 结构")

    ne = NarrativeEngine()

    stage_data = []
    for i, stage in enumerate(NARRATIVE_STAGES):
        prompt = ne.get_stage_prompt(stage)
        stage_data.append({"序号": i + 1, "阶段名称": stage, "写作提示": prompt[:80] + "..."})

    st.dataframe(stage_data, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("章节节奏规划")

    ch = st.number_input("当前章节号", 1, 100, 5)
    total = st.number_input("总章节数", 1, 100, 20)

    beats = ne.get_required_beats(ch, total)
    for b in beats:
        st.info(f"**{b}**：{ne.get_stage_prompt(b)}")

    st.divider()
    st.subheader("前 8 章进度模拟")
    sim_cols = st.columns(4)
    for i in range(8):
        with sim_cols[i % 4]:
            b = ne.get_required_beats(i + 1, 20)
            st.caption(f"第 {i+1} 章")
            st.write("、".join(b))


# ═══════════════════════════════════════════════════════════
# Tab 3：生成章节 — 调用 7-agent 管线 API
# ═══════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("✍️ 生成章节 — 7 Agent 管线")

    # 从故事设定 Tab 获取角色列表
    char_names = [c["name"] for c in st.session_state.get("characters", [])]

    with st.container(border=True):
        st.caption("章节参数")
        col1, col2 = st.columns(2)
        with col1:
            gen_chapter = st.number_input("章节号", 1, 100, 1)
        with col2:
            gen_title = st.text_input("章节标题（可选）", "第一章 星空异象")

        gen_pov = st.selectbox("叙事视角（POV 角色）", char_names if char_names else ["林夜"],
                               help="选择此章节的视角角色。可在「故事设定」Tab 中添加更多角色。")
        gen_outline = st.text_area("章节大纲",
                                   "林夜在天文台值夜班时发现星空异常，星星像呼吸一样明灭。",
                                   height=100)
        gen_context = st.text_area("世界观上下文（可选）",
                                   "现代都市背景，天文台位于城郊山上。主角林夜是天文台观测员。",
                                   height=80)

    # 检查 API 服务器是否可用
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
            "在项目根目录创建 `.env` 文件，填入：\n"
            "```\n"
            "LLM_PROVIDER=openai|deepseek|anthropic\n"
            "OPENAI_API_KEY=sk-xxx\n"
            "```\n\n"
            "配置完成后刷新此页面即可启用生成功能。"
        )

    if st.button("开始生成", use_container_width=True, type="primary", disabled=not server_ok):
        if not server_ok:
            st.error("API 服务器不可用，请先启动服务器。")
        else:
            with st.spinner("7 Agent 管线运行中：规划 → 架构 → 写作 → 审核 → 修订 → 观察 → 总结..."):
                try:
                    resp = httpx.post(
                        f"{server_url}/api/generate/chapter",
                        json={
                            "project_id": "streamlit_ui",
                            "chapter_number": gen_chapter,
                            "outline": gen_outline,
                            "world_context": gen_context,
                            "pov_character": gen_pov,
                            "prior_summary": "",
                        },
                        timeout=300,
                    )
                    data = resp.json()
                except httpx.TimeoutException:
                    st.error("生成超时（5 分钟），管线可能仍在运行，请检查服务器日志。")
                    data = None
                except Exception as e:
                    st.error(f"请求失败：{e}")
                    data = None

            if data and data.get("success"):
                st.success(f"✓ 第 {data['chapter_number']} 章生成成功！")

                # 显示生成内容
                with st.container(border=True):
                    st.markdown(data.get("content", "（内容为空）"))

                # 显示各阶段状态
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
                    st.success("✓ 章节通过质量审核")
                else:
                    st.warning("⚠ 章节未通过质量审核，请在「质量审核」Tab 中手动审核")

            elif data:
                st.error(f"生成失败：{data.get('error', '未知错误')}")
    elif not server_ok:
        st.info("请先启动 API 服务器后再点击生成。")


# ═══════════════════════════════════════════════════════════
# Tab 4：33 维质量审核
# ═══════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("33 维质量审核")

    sample_audit = "突然间，全场震惊。然而，他不由得感到一阵寒意。仿佛世界在旋转。"
    audit_text = st.text_area("待审核文本", sample_audit, height=150)

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


# ═══════════════════════════════════════════════════════════
# Tab 5：去 AI 检测
# ═══════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("去 AI 化 — AI 写作痕迹检测")

    sample_deai = "首先，让我们探讨这个问题。其次，我们需要分析数据。最后，值得注意的是结论。"
    deai_text = st.text_area("待分析文本", sample_deai, height=150)

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
# Tab 6：后写作校验
# ═══════════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("后写作校验")

    sample_v = "林夜猛然抬头，星空在头顶旋转。不，不是旋转——它们在移动，像是有生命的。"
    val_text = st.text_area("待校验文本", sample_v, height=150)
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

    c1, c2, c3 = st.columns(3)
    with c1:
        coherence = st.slider("连贯性", 0.0, 1.0, 0.85, 0.05)
    with c2:
        integration = st.slider("整合性", 0.0, 1.0, 0.72, 0.05)
    with c3:
        polish = st.slider("润色度", 0.0, 1.0, 0.68, 0.05)

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

    dsl_input = st.text_input("DSL 模板", "@title met @type:character at @self")
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
            "配置完成后启动 API 服务器，即可在「生成章节」Tab 中使用 7-Agent 管线。")


# ═══════════════════════════════════════════════════════════
# Tab 10：状态追踪
# ═══════════════════════════════════════════════════════════
with tabs[9]:
    st.subheader("状态变更追踪")

    if "delta_store" not in st.session_state:
        st.session_state.delta_store = DeltaStore()
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
                st.warning(f"已回滚到上一个检查点")
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


st.caption("---\nMy Novel Assist v0.2.0 — 工作流：设定 → 规划 → 写作 → 审核 → 发布")
