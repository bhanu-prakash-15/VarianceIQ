import json
from typing import Tuple

import altair as alt
import pandas as pd
import streamlit as st

from analysis_agent import AnalysisAgent, AnalysisConfig
from explanation_agent import ExplanationAgent, ExplanationConfig


# -------- HELPERS --------

@st.cache_data(show_spinner=False)
def run_analysis(csv_bytes: bytes) -> Tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Run AnalysisAgent (and serialize to dict/dataframes) for caching."""
    df = pd.read_csv(csv_bytes)

    # Mapping for the NYC “Expense_Budget_20251119.csv” file
    analysis_cfg = AnalysisConfig(
        department_col="Agency Name",
        account_col="Object Code",
        budget_col="Adopted Budget Amount",
        actual_col="Current Modified Budget Amount",
        materiality_threshold_abs=1_000_000.0,
        materiality_threshold_pct=0.05,
    )

    analysis_agent = AnalysisAgent(config=analysis_cfg)
    summary = analysis_agent.run(df)

    summary_dict = summary.to_dict()
    agg_df = pd.DataFrame(summary_dict["aggregate"])
    li_df = pd.DataFrame(summary_dict["line_items"])

    return summary_dict, agg_df, li_df


@st.cache_data(show_spinner=False)
def run_explanation(summary_dict: dict, use_llm: bool = True) -> Tuple[str, list, str]:
    """Run ExplanationAgent and cache narrative output."""
    expl_cfg = ExplanationConfig(use_llm=use_llm)
    expl_agent = ExplanationAgent(config=expl_cfg)
    result = expl_agent.run(summary_dict)
    mode = result.mode
    return result.narrative, result.bullet_points, mode


# -------- STREAMLIT UI --------

st.set_page_config(
    page_title="VarianceIQ – FP&A Variance Copilot",
    layout="wide",
)

st.title("📊 VarianceIQ – FP&A Variance Copilot")
st.caption(
    "Upload a Budget vs Actual CSV, compute structured variances, and generate LLM-powered explanations."
)

with st.sidebar:
    st.header("Upload")
    uploaded_file = st.file_uploader(
        "Budget vs Actual CSV",
        type=["csv"],
        help="For now, the file should have columns: Agency Name, Object Code, Adopted Budget Amount, Current Modified Budget Amount.",
    )
    use_llm = st.checkbox("Use Azure GPT-4o-mini for explanation", value=True)
    st.markdown("---")
    st.markdown("Made for **COT6930 – Final Project (VarianceIQ)**")

if uploaded_file is None:
    st.info("👈 Upload the csv file to begin.")
    st.stop()

# 1) Run analysis
with st.spinner("Running AnalysisAgent..."):
    summary_dict, agg_df, li_df = run_analysis(uploaded_file)

meta = summary_dict["metadata"]

# 2) KPI ROW
st.subheader("1. Overview")

kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.metric(
        "Total rows analysed",
        f"{meta['row_count']:,}",
    )

with kpi2:
    material_count = li_df["material"].sum() if "material" in li_df.columns else 0
    st.metric(
        "Material line items",
        f"{material_count:,}",
        help=f"Using materiality: abs ≥ {meta['materiality_abs']:,.0f} or ≥ {meta['materiality_pct']*100:.1f}%",
    )

with kpi3:
    dept_count = agg_df["department"].nunique() if not agg_df.empty else 0
    st.metric("Departments", f"{dept_count:,}")

st.markdown("---")

# 3) CHARTS SECTION
st.subheader("2. Department variance profile")

if agg_df.empty:
    st.warning("No aggregate variance data available.")
else:
    chart_df = agg_df.copy()
    chart_df["variance_m"] = chart_df["variance_total"] / 1_000_000
    chart_df["direction"] = chart_df["variance_total"].apply(
        lambda v: "Unfavorable" if v > 0 else "Favorable"
    )

    # Focus on top 15 by absolute variance
    chart_df = chart_df.sort_values("variance_total", key=lambda s: s.abs(), ascending=False).head(15)

    base = alt.Chart(chart_df).encode(
        x=alt.X("variance_m:Q", title="Variance (Millions)"),
        y=alt.Y("department:N", sort="-x", title="Department"),
        color=alt.Color(
            "direction:N",
            scale=alt.Scale(range=["#ff6b6b", "#4caf50"]),  # red = unfav, green = fav
            legend=alt.Legend(title="Direction"),
        ),
        tooltip=[
            "department",
            alt.Tooltip("variance_total:Q", title="Variance"),
            alt.Tooltip("budget_total:Q", title="Budget total"),
            alt.Tooltip("actual_total:Q", title="Actual total"),
        ],
    )

    st.altair_chart(base.mark_bar(), use_container_width=True)

# 4) TOP MATERIAL LINE ITEMS TABLE
st.subheader("3. Top material variances (line-item view)")

if li_df.empty:
    st.warning("No line item details available.")
else:
    material_df = li_df[li_df["material"]].copy()
    if material_df.empty:
        st.info("No line items exceeded the configured materiality threshold.")
    else:
        material_df = material_df.sort_values(
            "variance", key=lambda s: s.abs(), ascending=False
        ).head(25)

        display_cols = [
            "department",
            "account",
            "budget",
            "actual",
            "variance",
            "variance_pct",
            "direction",
            "drivers",
        ]
        st.dataframe(material_df[display_cols], use_container_width=True)

# 5) EXPLANATION AGENT
st.markdown("---")
st.subheader("4. Variance explanation")

with st.spinner("Generating explanation..."):
    narrative, bullets, mode = run_explanation(summary_dict, use_llm=use_llm)

st.markdown(f"**Explanation mode:** `{mode}`")

st.markdown("##### Narrative")
st.write(narrative)

st.markdown("##### Key points")
for b in bullets:
    st.markdown(f"- {b}")
