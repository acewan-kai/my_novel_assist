"""Streamlit UI — single-file web interface for all features."""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="My Novel Assist", layout="wide")

# ── Import all modules ──────────────────────────────────────────────
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
st.caption("AI-powered novel writing assistant")

tab_names = ["📐 Story", "🔍 Audit", "🤖 De-AI", "✅ Validate",
             "📊 Quality", "📈 Narrative", "🔤 DSL", "🏪 Providers", "📝 State"]
tabs = st.tabs(tab_names)


# ── Tab 1: Story Setup ──────────────────────────────────────────────
with tabs[0]:
    st.subheader("Story Premise Validation")

    col1, col2, col3 = st.columns(3)
    with col1:
        title = st.text_input("Title", "星穹之下")
    with col2:
        genre = st.text_input("Genre", "奇幻")
    with col3:
        logline = st.text_input("Logline", "一个在天文台工作的青年发现星空是巨大生物的外壳")

    if st.button("Validate Premise", use_container_width=True):
        sr = SchemaRegistry()
        ok, errors = sr.validate("story_premise", {
            "title": title, "genre": genre, "logline": logline
        })
        if ok:
            st.success("✓ Story premise is valid")
        else:
            for e in errors:
                st.error(e)

    st.divider()
    st.subheader("Character Schema")
    c1, c2 = st.columns(2)
    with c1:
        char_name = st.text_input("Character name", "林夜")
    with c2:
        char_role = st.text_input("Role", "protagonist")
    if st.button("Validate Character", use_container_width=True):
        sr = SchemaRegistry()
        ok, errors = sr.validate("character", {"name": char_name, "role": char_role})
        if ok:
            st.success("✓ Character valid")
        else:
            for e in errors:
                st.error(e)


# ── Tab 2: 33-Dimension Audit ──────────────────────────────────────
with tabs[1]:
    st.subheader("33-Dimension Quality Audit")

    sample_audit = "突然间，全场震惊。然而，他不由得感到一阵寒意。仿佛世界在旋转。"
    audit_text = st.text_area("Text to audit", sample_audit, height=150)

    if st.button("Run Audit", use_container_width=True, type="primary"):
        auditor = Audit33Validator()
        result = auditor.audit(audit_text)

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Overall", f"{result.overall:.2f}")
        col_b.metric("Passed", "✅ Yes" if result.passed else "❌ No")
        col_c.metric("Issues", len(result.issues))

        if result.issues:
            st.subheader("Issues")
            for i in result.issues:
                sev = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
                st.write(f"{sev.get(i.severity, '⚪')} **{i.dimension}** ({i.severity}): {i.message}")

        st.subheader("Dimension Scores")
        for dim, score in result.scores.items():
            st.progress(min(score, 1.0), text=f"{dim}: {score:.2f}")


# ── Tab 3: De-AI ────────────────────────────────────────────────────
with tabs[2]:
    st.subheader("De-AI-fication — AI Writing Detection")

    sample_deai = "首先，让我们探讨这个问题。其次，我们需要分析数据。最后，值得注意的是结论。"
    deai_text = st.text_area("Text to analyze", sample_deai, height=150)

    if st.button("Analyze", use_container_width=True, type="primary"):
        deai = DeAIFilter()
        result = deai.analyze(deai_text)

        score = result.ai_score
        if score < 0.3:
            st.success(f"AI Score: {score:.2f} — Looks human-written")
        elif score < 0.6:
            st.warning(f"AI Score: {score:.2f} — Some AI patterns detected")
        else:
            st.error(f"AI Score: {score:.2f} — Heavy AI痕迹 detected")

        st.metric("Passes threshold", "✅ Yes" if result.passes else "❌ No")

        if result.issues:
            st.subheader("Patterns Found")
            for i in result.issues:
                st.write(f"- **{i.pattern}** ({i.severity}): {i.suggestion}")


# ── Tab 4: Post-Write Validation ───────────────────────────────────
with tabs[3]:
    st.subheader("Post-Write Validation")

    sample_v = "林夜猛然抬头，星空在头顶旋转。不，不是旋转——它们在移动，像是有生命的。"
    val_text = st.text_area("Text to validate", sample_v, height=150)
    min_words = st.slider("Minimum word count", 10, 1000, 50)

    if st.button("Validate", use_container_width=True, type="primary"):
        v = PostWriteValidator(min_words=min_words)
        result = v.validate(val_text)

        if result.passed:
            st.success("✓ Validation passed")
        else:
            st.error("✗ Validation failed")

        col1, col2 = st.columns(2)
        col1.metric("Word count", int(result.metrics.get("word_count", 0)))
        col2.metric("Quality score", f"{result.metrics.get('quality_score', 0):.2f}")

        if result.errors:
            st.subheader("Errors")
            for e in result.errors:
                st.error(e)
        if result.warnings:
            st.subheader("Warnings")
            for w in result.warnings:
                st.warning(w)


# ── Tab 5: Quality Metrics ─────────────────────────────────────────
with tabs[4]:
    st.subheader("Quality Metrics Calculator")

    c1, c2, c3 = st.columns(3)
    with c1:
        coherence = st.slider("Coherence", 0.0, 1.0, 0.85, 0.05)
    with c2:
        integration = st.slider("Integration", 0.0, 1.0, 0.72, 0.05)
    with c3:
        polish = st.slider("Polish", 0.0, 1.0, 0.68, 0.05)

    qm = QualityMetrics(coherence=coherence, integration=integration, polish=polish)

    st.metric("Overall", f"{qm.overall:.2f}",
              delta="Passed" if qm.passed else "Failed",
              delta_color="normal" if qm.passed else "off")

    st.progress(qm.overall, text="Overall quality")

    st.json(qm.to_dict())


# ── Tab 6: Narrative Engine ────────────────────────────────────────
with tabs[5]:
    st.subheader("Narrative Engine — 16 Dramatica Stages")

    ne = NarrativeEngine()

    # Stage table
    stage_data = []
    for i, stage in enumerate(NARRATIVE_STAGES):
        prompt = ne.get_stage_prompt(stage)
        stage_data.append({"#": i + 1, "Stage": stage, "Prompt": prompt[:80] + "..."})

    st.dataframe(stage_data, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Chapter Beat Planner")

    ch = st.number_input("Chapter number", 1, 100, 5)
    total = st.number_input("Total chapters", 1, 100, 20)

    beats = ne.get_required_beats(ch, total)
    for b in beats:
        st.info(f"**{b}**: {ne.get_stage_prompt(b)}")

    # Simulation
    st.divider()
    st.subheader("Progression Simulation")
    sim_cols = st.columns(4)
    for i in range(8):
        with sim_cols[i % 4]:
            b = ne.get_required_beats(i + 1, 20)
            st.caption(f"Ch.{i+1}")
            st.write(", ".join(b))


# ── Tab 7: DSL Parser ──────────────────────────────────────────────
with tabs[6]:
    st.subheader("@DSL Template Parser")

    dsl_input = st.text_input("DSL template", "@title met @type:character at @self")
    if dsl_input:
        parser = DSLParser()
        matches = parser.parse(dsl_input)
        if matches:
            st.dataframe([{"Type": m.qtype, "Target": m.target,
                          "Field": m.field, "Valid": m.valid} for m in matches],
                        use_container_width=True, hide_index=True)
        else:
            st.info("No @DSL patterns found")

    st.divider()
    st.subheader("Template Injection Demo")
    template = st.text_input("Injection template", "In @type:location, @title is...")
    if template:
        parser = DSLParser()
        found = parser.parse(template)
        st.write(f"**Found {len(found)} injection points**")
        for m in found:
            st.write(f"- `{m.raw}` → resolve via {m.qtype}")


# ── Tab 8: Providers ───────────────────────────────────────────────
with tabs[7]:
    st.subheader("LLM Provider Bank")

    pdata = []
    for name, info in PROVIDER_BANK.items():
        pdata.append({
            "Provider": info.name,
            "Default Model": info.default_model,
            "API URL": info.base_url or "(local)",
            "API Key Env": info.api_key_env or "-",
            "Models": ", ".join(info.models[:4]),
            "Local": "✅" if info.local else "",
        })

    st.dataframe(pdata, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Configuration")
    st.code("LLM_PROVIDER=openai|deepseek|anthropic|google|ollama|custom\n"
            "OPENAI_API_KEY=sk-...\n"
            "ANTHROPIC_API_KEY=sk-ant-...\n"
            "DEEPSEEK_API_KEY=sk-...", language="bash")


# ── Tab 9: State Delta ─────────────────────────────────────────────
with tabs[8]:
    st.subheader("State Delta Tracking")

    if "delta_store" not in st.session_state:
        st.session_state.delta_store = DeltaStore()
    ds = st.session_state.delta_store

    col1, col2, col3 = st.columns(3)
    with col1:
        field = st.text_input("Field", "chapter_1_status")
    with col2:
        old_v = st.text_input("Old value", "")
    with col3:
        new_v = st.text_input("New value", "")

    bcol1, bcol2, bcol3 = st.columns(3)
    with bcol1:
        if st.button("Record", use_container_width=True):
            ds.record(field, old_v, new_v, "user")
            st.rerun()
    with bcol2:
        if st.button("Checkpoint", use_container_width=True):
            ds.checkpoint(f"cp_{len(ds.history)}")
            st.success("Checkpoint saved")
    with bcol3:
        if st.button("Rollback", use_container_width=True):
            cp = [k for k in ds._checkpoints.keys()]
            if cp:
                ds.rollback(cp[-1])
                st.warning(f"Rolled back to last checkpoint")
                st.rerun()

    if ds.history:
        st.subheader("History")
        st.dataframe(
            [{"Agent": d.agent, "Field": d.field,
              "Old": str(d.old_value)[:20], "New": str(d.new_value)[:20],
              "Time": d.timestamp.split("T")[1][:8]} for d in ds.history],
            use_container_width=True, hide_index=True
        )

    if st.button("Clear History"):
        ds.clear()
        st.rerun()


st.caption("---\nMy Novel Assist v0.2.0 — built with Streamlit")
