import os
import json
import hashlib
from typing import Dict, Any, List

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from analysis_agent import AnalysisAgent, AnalysisConfig
from explanation_agent import ExplanationAgent, ExplanationConfig

USERS_FILE = "users.csv"
HISTORY_DIR = "user_history"
UPLOAD_DIR = "uploaded_files"


# ======================================================
#  GLOBAL STYLE – POWERBI LOOK
# ======================================================
def inject_css():
    st.markdown(
        """
        <style>
        /* Light grey page background */
        .stApp {
            background-color: #e5e7eb;
        }

        .main {
            background-color: #f3f4f6;
        }

        /* Generic dashboard card */
        .dashboard-card {
            background-color: #ffffff;
            padding: 1rem 1.25rem;
            border-radius: 0.9rem;
            box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08);
            border: 1px solid #e5e7eb;
        }

        .card-title {
            font-size: 0.8rem;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: .06em;
            margin-bottom: 0.25rem;
        }

        .card-value {
            font-size: 1.7rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 0.25rem;
        }

        .card-sub {
            font-size: 0.8rem;
            color: #9ca3af;
        }

        .section-title {
            font-size: 1.05rem;
            font-weight: 600;
            color: #111827;
            margin: 0.4rem 0 0.5rem 0;
        }

        .page-title {
            font-size: 2rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 0.25rem;
        }

        .page-subtitle {
            font-size: 0.85rem;
            color: #6b7280;
            margin-bottom: 0.75rem;
        }

        .explanation-text {
            font-size: 0.95rem;
            line-height: 1.6;
            color: #111827;
        }

        /* Table container slightly card-like */
        .stDataFrame {
            border-radius: 0.9rem;
        }

        /* Make all headings black & bold globally */
        h1, h2, h3, h4, h5, h6,
        .block-container h1,
        .block-container h2,
        .block-container h3,
        .block-container h4,
        .block-container h5,
        .block-container h6 {
            color: #111827 !important;
            font-weight: 700 !important;
        }

        /* Control labels darker in Settings etc. */
        .stSlider > label,
        .stSelectbox > label,
        .stNumberInput > label,
        .stCheckbox > label {
            color: #111827 !important;
            font-weight: 600 !important;
        }

        /* Force ALL text inside expanders to be black */
        [data-testid="stExpander"] * {
            color: #111827 !important;
        }

        [data-testid="stExpander"] h1,
        [data-testid="stExpander"] h2,
        [data-testid="stExpander"] h3,
        [data-testid="stExpander"] h4 {
            color: #111827 !important;
            font-weight: 700 !important;
        }

        /* ================= SIDEBAR STYLING ================= */

        /* Dark slate sidebar background */
        [data-testid="stSidebar"] {
            background-color: #111827;
        }

        /* Make ALL sidebar text bright and readable */
        [data-testid="stSidebar"] * {
            color: #f9fafb !important;
        }

        /* Sidebar title (👤 Bhanu) */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] h5 {
            color: #ffffff !important;
            font-weight: 700 !important;
        }

        /* Navigation radio labels */
        [data-testid="stSidebar"] label {
            color: #f9fafb !important;
            font-size: 1.05rem;
            font-weight: 500;
        }

        /* Upload widget text in sidebar */
        [data-testid="stSidebar"] [data-testid="stFileUploader"] * {
            color: #f9fafb !important;
        }

        /* Uploaded file name (e.g., Expense_Budget_DEMO.csv) */
        [data-testid="stSidebar"] .uploadedFileName {
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ======================================================
#  USER AUTH STORAGE HELPERS
# ======================================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_users() -> pd.DataFrame:
    if not os.path.exists(USERS_FILE):
        return pd.DataFrame(columns=["email", "name", "password_hash"])
    return pd.read_csv(USERS_FILE)


def save_users(df: pd.DataFrame) -> None:
    df.to_csv(USERS_FILE, index=False)


# ======================================================
#  PER-USER HISTORY STORAGE
# ======================================================
def _history_file_for_email(email: str) -> str:
    os.makedirs(HISTORY_DIR, exist_ok=True)
    safe_id = hashlib.sha256(email.encode("utf-8")).hexdigest()[:16]
    return os.path.join(HISTORY_DIR, f"history_{safe_id}.json")


def load_user_history(email: str) -> List[Dict[str, Any]]:
    path = _history_file_for_email(email)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_user_history(email: str, history: List[Dict[str, Any]]) -> None:
    if not email:
        return
    path = _history_file_for_email(email)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


# ======================================================
#  LOGIN / SIGNUP PAGE (FULL SCREEN, CENTERED CARD)
# ======================================================
def show_login_page():
    inject_css()

    # ---- Extra CSS: label color + layout for login card ----
    st.markdown(
        """
        <style>
        /* Make input labels black in login form */
        .stTextInput label, .stPasswordInput label {
            color: #111 !important;
            font-weight: 600 !important;
        }

        /* Make subheaders (e.g. "Login to your account") black */
        [data-testid="stAppViewContainer"] h3 {
            color: #111827 !important;
            font-weight: 700 !important;
        }

        /* Hide sidebar on login page */
        [data-testid="stSidebar"] {
            display: none;
        }

        /* Turn the main block-container into a centered card */
        [data-testid="stAppViewContainer"] > .main > div {
            max-width: 480px;
            margin: 5rem auto;
            padding: 2.5rem 2.25rem 2rem 2.25rem;
            background: #ffffff;
            border-radius: 1rem;
            box-shadow: 0 10px 30px rgba(15,23,42,0.12);
            border: 1px solid #e5e7eb;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ----- Title + subtitle -----
    st.markdown(
        "<h1 style='text-align:center; color:black; font-size:1.9rem; "
        "margin-bottom:0.3rem;'>🔐 VarianceIQ Login</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#6b7280; margin-bottom:1.5rem;'>"
        "Sign in to access your variance analysis dashboard.</p>",
        unsafe_allow_html=True,
    )

    users_df = load_users()
    tab_login, tab_signup = st.tabs(["Login", "Create Account"])

    # ---------------- LOGIN ----------------
    with tab_login:
        st.subheader("Login to your account")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            if not email or not password:
                st.error("Please enter email and password.")
            elif email in users_df["email"].values:
                stored_hash = users_df.loc[
                    users_df["email"] == email, "password_hash"
                ].iloc[0]
                if stored_hash == hash_password(password):
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.session_state.user_name = users_df.loc[
                        users_df["email"] == email, "name"
                    ].iloc[0]

                    # Load this user's history into session
                    st.session_state.history = load_user_history(email)

                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            else:
                st.error("Account does not exist. Please create one.")

    # ---------------- SIGN UP ----------------
    with tab_signup:
        st.subheader("Create a new account")
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            create = st.form_submit_button("Create Account")

        if create:
            if not name or not new_email or not new_password:
                st.error("Please fill all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif new_email in users_df["email"].values:
                st.error("User already exists.")
            else:
                new_user = {
                    "email": new_email,
                    "name": name,
                    "password_hash": hash_password(new_password),
                }
                users_df = pd.concat(
                    [users_df, pd.DataFrame([new_user])], ignore_index=True
                )
                save_users(users_df)
                st.success("Account created! Please login.")


# ======================================================
#  SAMPLE DATA (USED WHEN NO CSV IS UPLOADED)
# ======================================================
def load_sample_data():
    data = {
        "Category": ["Dining", "Entertainment", "Groceries", "Rent", "Utilities"],
        "Budget": [1300, 1200, 1100, 1400, 1450],
        "Spent": [1219, 1093, 1050, 1218, 1307],
    }
    df = pd.DataFrame(data)
    df["Variance"] = df["Budget"] - df["Spent"]
    df["% Used"] = (df["Spent"] / df["Budget"] * 100).round(1)
    months = (
        pd.date_range("2025-01-01", periods=5, freq="MS")
        .strftime("%Y-%m")
        .tolist()
    )
    monthly = pd.DataFrame(
        {
            "YearMonth": months,
            "Total Budget": np.linspace(6000, 6800, 5),
            "Total Expenses": np.linspace(5800, 6100, 5),
        }
    )
    return df, monthly


def build_summary_from_df(df: pd.DataFrame) -> Dict[str, Any]:
    """Minimal AnalysisSummary-like dict so ExplanationAgent can run on demo data."""
    meta = {
        "row_count": int(len(df)),
        "materiality_abs": 0.0,
        "materiality_pct": 0.0,
    }

    aggregate = []
    for _, r in df.iterrows():
        aggregate.append(
            {
                "department": r["Category"],
                "budget_total": float(r["Budget"]),
                "actual_total": float(r["Spent"]),
                "variance_total": float(r["Variance"]),
                "variance_pct_total": float(
                    (r["Variance"] / r["Budget"]) * 100 if r["Budget"] != 0 else 0
                ),
            }
        )

    line_items = []
    for _, r in df.iterrows():
        line_items.append(
            {
                "department": r["Category"],
                "account": "Total",
                "period": None,
                "budget": float(r["Budget"]),
                "actual": float(r["Spent"]),
                "variance": float(r["Variance"]),
                "variance_pct": float(
                    (r["Variance"] / r["Budget"]) * 100 if r["Budget"] != 0 else 0
                ),
                "direction": "unfavorable"
                if r["Variance"] < 0
                else "favorable"
                if r["Variance"] > 0
                else "neutral",
                "material": True,
                "drivers": [],
            }
        )

    return {"metadata": meta, "aggregate": aggregate, "line_items": line_items}


# ======================================================
#  MAIN DASHBOARD (POWERBI STYLE)
# ======================================================
def main_dashboard():
    inject_css()

    # Ensure history list exists in session
    if "history" not in st.session_state:
        st.session_state.history = []

    # ------------ HEADER ------------
    header_left, header_right = st.columns([3, 1])
    with header_left:
        st.markdown(
            '<div class="page-title">📊 Monthly Budget vs Actual</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="page-subtitle">VarianceIQ – automated variance analysis for large public-sector budgets.</div>',
            unsafe_allow_html=True,
        )
    with header_right:
        st.markdown("<div style='text-align:right;'>Period</div>", unsafe_allow_html=True)
        period = st.radio(
            "",
            ["Month", "Quarter", "Total"],
            index=2,
            horizontal=True,
            label_visibility="collapsed",
        )

    # ------------ DATA & ANALYSIS ------------
    st.sidebar.subheader("Upload Budget vs Actual")
    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV/XLSX", type=["csv", "xlsx"]
    )

    summary_dict = None  # for ExplanationAgent
    file_name = "Sample data (built-in)"
    file_path = None

    if uploaded_file:
        # Save uploaded file to disk so we can reference it later in history
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_name = uploaded_file.name
        file_path = os.path.join(UPLOAD_DIR, file_name)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Read from the saved file
        if uploaded_file.name.endswith(".csv"):
            df_raw = pd.read_csv(file_path)
        else:
            df_raw = pd.read_excel(file_path)

        # Materiality in millions from Settings
        var_abs_millions = float(st.session_state.get("variance_threshold", 10))
        var_abs = var_abs_millions * 1_000_000.0
        var_pct = 0.05

        analysis_cfg = AnalysisConfig(
            department_col="Agency Name",
            account_col="Object Code",
            budget_col="Adopted Budget Amount",
            actual_col="Current Modified Budget Amount",
            materiality_threshold_abs=var_abs,
            materiality_threshold_pct=var_pct,
        )

        analysis_agent = AnalysisAgent(config=analysis_cfg)
        summary = analysis_agent.run(df_raw)
        summary_dict = summary.to_dict()

        agg_df = pd.DataFrame(summary_dict["aggregate"])
        df = agg_df.rename(
            columns={
                "department": "Category",
                "budget_total": "Budget",
                "actual_total": "Spent",
                "variance_total": "Variance",
                "variance_pct_total": "% Used",
            }
        )
        df["Variance"] = df["Budget"] - df["Spent"]
        df["% Used"] = (df["Spent"] / df["Budget"] * 100)

    else:
        # Built-in sample data
        df, _ = load_sample_data()
        summary_dict = build_summary_from_df(df)

    # ------------ KPI DATA (used in dashboard + history) ------------
    total_budget = df["Budget"].sum()
    total_spent = df["Spent"].sum()
    difference = total_budget - total_spent
    pct_used = (total_spent / total_budget * 100)

    # --------------- TOP KPI ROW ---------------
    st.write("")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.markdown(
            f"""
            <div class="dashboard-card">
                <div class="card-title">Total Budget</div>
                <div class="card-value">€ {total_budget:,.0f}</div>
                <div class="card-sub">Planned spend for selected period</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi2:
        st.markdown(
            f"""
            <div class="dashboard-card">
                <div class="card-title">Total Expenses</div>
                <div class="card-value">€ {total_spent:,.0f}</div>
                <div class="card-sub">Actual spend booked</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi3:
        sign = "favourable" if difference > 0 else "unfavourable"
        st.markdown(
            f"""
            <div class="dashboard-card">
                <div class="card-title">Variance</div>
                <div class="card-value">€ {difference:,.0f}</div>
                <div class="card-sub">{sign} vs budget</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi4:
        st.markdown(
            f"""
            <div class="dashboard-card">
                <div class="card-title">% of Budget Used</div>
                <div class="card-value">{pct_used:.1f}%</div>
                <div class="card-sub">Actual ÷ Budget</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # sort once for visuals
    df_sorted = df.sort_values("Spent", ascending=False)

    st.write("")
    # *** renamed heading to just "Overview" ***
    st.markdown(
        '<div class="section-title">Overview</div>',
        unsafe_allow_html=True,
    )

    # ========= MIDDLE ROW: BAR + PIE =========
    row1_col1, row1_col2 = st.columns([1.2, 1])

    with row1_col1:
        top15 = df_sorted.head(15)
        fig_bar = px.bar(
            top15.sort_values("Spent"),
            x="Spent",
            y="Category",
            orientation="h",
            labels={"Spent": "Spent (€)", "Category": "Agency"},
        )
        fig_bar.update_layout(
            height=430,
            xaxis_tickformat=",.0f",
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with row1_col2:
        top10 = df_sorted.head(10)
        other_spent = df_sorted["Spent"].iloc[10:].sum()
        pie_df = top10.copy()
        pie_df.loc[len(pie_df)] = {
            "Category": "Other Agencies",
            "Budget": 0.0,
            "Spent": other_spent,
            "Variance": 0.0,
            "% Used": 0.0,
        }
        fig_pie = px.pie(
            pie_df,
            names="Category",
            values="Spent",
            hole=0.45,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(height=430, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    # ========= SECOND ROW: GLOBAL BAR + TABLE =========
    st.write("")
    row2_col1, row2_col2 = st.columns([1, 1.2])

    with row2_col1:
        st.markdown(
            '<div class="section-title">Global Budget vs Expenses</div>',
            unsafe_allow_html=True,
        )
        global_df = pd.DataFrame(
            {"Metric": ["Budget", "Expenses"], "Value": [total_budget, total_spent]}
        )
        fig_global = px.bar(
            global_df,
            x="Metric",
            y="Value",
            text="Value",
            labels={"Value": "Amount (€)"},
        )
        fig_global.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig_global.update_layout(
            yaxis_tickformat=",.0f",
            height=400,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_global, use_container_width=True)

    with row2_col2:
        st.markdown(
            '<div class="section-title">Top 25 Agencies by Spending</div>',
            unsafe_allow_html=True,
        )
        table_df = df_sorted.copy()
        table_df["Budget"] = table_df["Budget"].map(lambda x: f"€ {x:,.0f}")
        table_df["Spent"] = table_df["Spent"].map(lambda x: f"€ {x:,.0f}")
        table_df["Variance"] = table_df["Variance"].map(lambda x: f"€ {x:,.0f}")
        table_df["% Used"] = table_df["% Used"].map(lambda x: f"{x:.1f}%")
        st.dataframe(table_df.head(25), use_container_width=True, height=360)

    # ==================================================
    #  EXPLANATION SECTION – ExplanationAgent
    # ==================================================
    st.write("")
    st.markdown(
        '<div class="section-title">🧠 Variance Explanations</div>',
        unsafe_allow_html=True,
    )

    use_llm = bool(st.session_state.get("use_llm", True))
    current_user = st.session_state.get("user_email", "")

    if st.button("Generate Variance Explanations"):
        if summary_dict is None:
            st.warning("No summary available to explain.")
        else:
            expl_cfg = ExplanationConfig(use_llm=use_llm)
            expl_agent = ExplanationAgent(config=expl_cfg)

            with st.spinner("Running ExplanationAgent..."):
                result = expl_agent.run(summary_dict)

            # Store in session for main dashboard display
            st.session_state["last_explanations"] = {
                "narrative": result.narrative,
                "bullets": result.bullet_points,
                "mode": result.mode,
            }

            # ---- Create a history entry for THIS user ----
            history = st.session_state.get("history", [])

            if history:
                next_run_id = max(int(h.get("run_id", 0)) for h in history) + 1
            else:
                next_run_id = 1

            entry = {
                "run_id": next_run_id,
                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_budget": float(total_budget),
                "total_spent": float(total_spent),
                "difference": float(difference),
                "file_name": file_name,
                "file_path": file_path,
                "explanation": {
                    "generated_at": pd.Timestamp.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "mode": result.mode,
                    "narrative": result.narrative,
                    "bullets": result.bullet_points,
                },
            }

            history.append(entry)
            st.session_state.history = history
            save_user_history(current_user, history)

    # ---- render explanations on main dashboard ----
    if "last_explanations" in st.session_state:
        ex = st.session_state["last_explanations"]

        st.markdown(
            f"<p style='color:#111827; font-weight:600; margin-bottom:0.4rem;'>"
            f"Explanation mode: <code>{ex['mode']}</code>"
            f"</p>",
            unsafe_allow_html=True,
        )

        st.markdown("#### Executive Narrative")
        clean_narrative = (
            ex["narrative"]
            .replace("*", r"\*")
            .replace("_", r"\_")
        )
        st.markdown(
            f"<div class='dashboard-card explanation-text'>{clean_narrative}</div>",
            unsafe_allow_html=True,
        )

        if ex["bullets"]:
            st.markdown("#### Key Points")
            bullet_html = ""
            for b in ex["bullets"]:
                clean_b = b.replace("*", r"\*").replace("_", r"\_")
                bullet_html += f"<li>{clean_b}</li>"
            st.markdown(
                f"<ul class='explanation-text'>{bullet_html}</ul>",
                unsafe_allow_html=True,
            )


# ======================================================
#  HISTORY PAGE (PER-USER)
# ======================================================
def history_page():
    inject_css()
    st.markdown(
        "<h1 style='color:black; font-weight:700;'>📜 Run History</h1>",
        unsafe_allow_html=True,
    )

    history_list = st.session_state.get("history", [])

    if not history_list:
        st.info("No history available.")
        return

    # Show newest first
    for entry in reversed(history_list):
        run_id = entry.get("run_id", "?")
        ts = entry.get("timestamp", "")
        total_budget = float(entry.get("total_budget", 0))
        total_spent = float(entry.get("total_spent", 0))
        diff = float(entry.get("difference", 0))

        # simple text label (no html tags) so color is handled by CSS
        exp_label = (
            f"Run {run_id} | Budget € {total_budget:,.0f} | "
            f"Spent € {total_spent:,.0f} | "
            f"Δ € {diff:,.0f} ({ts})"
        )

        with st.expander(exp_label, expanded=False):
            st.markdown(
                "<h4 style='color:black;'>Run Details</h4>",
                unsafe_allow_html=True,
            )

            st.write(f"**Timestamp:** {ts}")
            st.write(f"**Run ID:** {run_id}")
            st.write(f"**Total Budget:** € {total_budget:,.0f}")
            st.write(f"**Total Spent:** € {total_spent:,.0f}")

            if diff > 0:
                st.write(f"**Difference:** :green[€ {diff:,.0f}]")
            elif diff < 0:
                st.write(f"**Difference:** :red[€ {diff:,.0f}]")
            else:
                st.write(f"**Difference:** € {diff:,.0f}")

            # -------- FILE INFO --------
            file_name = entry.get("file_name")
            file_path = entry.get("file_path")

            st.write("### Uploaded File")
            if file_path:
                st.write(f"[📄 {file_name}]({file_path})")
            else:
                st.write("Sample data (built-in)")

            # -------- EXPLANATION --------
            explanation = entry.get("explanation")
            if explanation:
                st.markdown(
                    "<h4 style='color:black;'>Executive Narrative</h4>",
                    unsafe_allow_html=True,
                )
                st.markdown(explanation["narrative"])

                bullets = explanation.get("bullets") or []
                if bullets:
                    st.markdown(
                        "<h4 style='color:black;'>Key Points</h4>",
                        unsafe_allow_html=True,
                    )
                    for b in bullets:
                        st.markdown(f"- {b}")
            else:
                st.info("No explanations generated for this run.")


# ======================================================
#  SETTINGS PAGE
# ======================================================
def settings_page():
    inject_css()
    st.title("⚙️ Settings")

    current_var = int(st.session_state.get("variance_threshold", 10))
    st.session_state.variance_threshold = st.slider(
        "Material Variance Threshold (ABS, in millions)",
        1,
        200,
        current_var,
        help="Used by AnalysisAgent when running on the NYC budget file.",
    )

    styles = ["Formal & Concise", "Executive Summary", "Detailed Narrative"]
    current_style = st.session_state.get("explanation_style", styles[0])
    st.session_state.explanation_style = st.selectbox(
        "Explanation Style (stored for future use)",
        styles,
        index=styles.index(current_style),
    )

    st.session_state.max_explained_lines = st.number_input(
        "Max Lines to Explain (for future tuning)",
        min_value=3,
        max_value=50,
        value=int(st.session_state.get("max_explained_lines", 10)),
    )

    st.session_state.use_llm = st.checkbox(
        "Use Azure GPT-4o-mini (LLM mode)",
        value=bool(st.session_state.get("use_llm", True)),
        help="If unchecked, ExplanationAgent will use its rule-based fallback.",
    )

    st.success("Settings saved!")


# ======================================================
#  APP ENTRYPOINT
# ======================================================
def main():
    st.set_page_config(page_title="VarianceIQ", layout="wide")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # If not logged in, show only login page (no sidebar)
    if not st.session_state.authenticated:
        # Clear any previous user's history from memory (safety)
        st.session_state.history = []
        show_login_page()
        return

    # Logged-in view: show sidebar + dashboard pages
    inject_css()

    st.sidebar.title(f"👤 {st.session_state.get('user_name', '')}")
    if st.sidebar.button("Logout"):
        # Persist current user's history before logout
        email = st.session_state.get("user_email", "")
        save_user_history(email, st.session_state.get("history", []))
        st.session_state.authenticated = False
        # Optional: clear explanations on logout
        st.session_state.pop("last_explanations", None)
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Navigation")

    page = st.sidebar.radio(
        "",
        ["Main Dashboard", "History", "Settings"],
    )

    if page == "Main Dashboard":
        main_dashboard()
    elif page == "History":
        history_page()
    elif page == "Settings":
        settings_page()


if __name__ == "__main__":
    main()
