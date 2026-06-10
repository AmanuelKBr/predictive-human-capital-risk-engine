from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ai_assistant import get_ai_response
from data import build_data_context, build_executive_summary, build_gold_facts, compute_kpis, load_silver_tables

# Configure the page
st.set_page_config(page_title="PHCORE | Data Engineering Portfolio", layout="wide", initial_sidebar_state="collapsed")

# Modern AI-themed dark CSS: animated gradient background, glowing/pulsating cards
st.markdown("""
    <style>
    @keyframes gradientShift {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    @keyframes pulseGlow {
        0%, 100% {box-shadow: 0 0 14px rgba(88,166,255,0.25), inset 0 0 8px rgba(163,113,247,0.12);}
        50% {box-shadow: 0 0 28px rgba(163,113,247,0.45), inset 0 0 14px rgba(88,166,255,0.2);}
    }
    .stApp {
        background: linear-gradient(120deg, #0D1117, #161B22, #1A1033, #0D1117);
        background-size: 400% 400%;
        animation: gradientShift 22s ease infinite;
        color: #E6EDF3;
    }
    h1 {
        background: linear-gradient(90deg, #58A6FF, #A371F7, #F778BA, #58A6FF);
        background-size: 300% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 8s linear infinite;
        font-weight: 800 !important;
    }
    h2, h3, h4 {color: #A371F7;}
    .metric-card {
        background: rgba(22, 27, 34, 0.55);
        backdrop-filter: blur(12px);
        padding: 20px;
        border-radius: 14px;
        border: 1px solid rgba(88, 166, 255, 0.25);
        animation: pulseGlow 5s ease-in-out infinite;
    }
    div[data-testid="stMetric"] {
        background: rgba(22, 27, 34, 0.55);
        backdrop-filter: blur(12px);
        border-radius: 14px;
        border: 1px solid rgba(163, 113, 247, 0.3);
        padding: 14px;
        animation: pulseGlow 6s ease-in-out infinite;
    }
    div[data-testid="stChatMessage"] {
        background: rgba(22, 27, 34, 0.55);
        backdrop-filter: blur(8px);
        border-radius: 12px;
        border: 1px solid rgba(88, 166, 255, 0.2);
    }
    a {color: #79C0FF;}
    </style>
    """, unsafe_allow_html=True)

# Header Section
st.title("Predictive Human Capital & Operational Risk Engine (PHCORE)")
st.markdown("**Role:** Data & Analytics Engineer | **Tech Stack:** Microsoft Fabric, Python, Spark, DAX, Machine Learning")
st.markdown("---")

GITHUB_REPO_URL = "https://github.com/AmanuelKBr/predictive-human-capital-risk-engine"
PBIX_URL = f"{GITHUB_REPO_URL}/blob/main/fabric/Predictive%20Human%20Capital%20Risk%20Engine%20Dashboard.pbix"

# Power BI Screenshots & Links Section
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Power BI Semantic Model — Report Walkthrough")
    screenshot_dir = Path(__file__).parent / "assets" / "screenshots"
    screenshots = sorted(p for p in screenshot_dir.glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    if screenshots:
        tabs = st.tabs([p.stem.replace("_", " ").replace("-", " ").title() for p in screenshots])
        for tab, path in zip(tabs, screenshots):
            with tab:
                st.image(str(path), use_container_width=True)
    else:
        st.info(
            "Power BI report screenshots go here. Drop PNG/JPG files into "
            "`assets/screenshots/` (e.g. `01_executive_overview.png`, "
            "`02_compliance_risk.png`) and they'll appear as tabs automatically."
        )

with col2:
    st.subheader("Project Resources")
    st.markdown(f"""
    <div class="metric-card">
        <h4>🔗 Project Links</h4>
        <p><a href="{GITHUB_REPO_URL}" target="_blank">View GitHub Repository & Code</a></p>
        <p><a href="{PBIX_URL}" target="_blank">Download Power BI Report (.pbix)</a></p>
        <p style="font-size:0.85em; color:#8B949E;">The .pbix uses a Direct Lake connection to
        Microsoft Fabric OneLake — visuals and the data model open in Power BI Desktop, but live
        data requires access to the source Fabric workspace.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.subheader("Key Engineering Highlights")
    st.markdown("""
    * **Medallion Lakehouse:** Bronze/Silver/Gold architecture deployed in Microsoft Fabric.
    * **Automated ETL:** Dataflow Gen2 pipelines handling JSON ingestion and Delta Parquet upserts.
    * **Enterprise Semantic Model:** Star schema optimization with dynamic Row-Level Security (RLS).
    * **Predictive AI:** Integrated Key Influencer logistic regression and NLP Smart Narratives.
    """)

# Architecture Deep Dive
st.markdown("---")
st.subheader("The Data Pipeline Architecture")
st.markdown("""
This project solves the fundamental disconnect between HR operations and financial performance. By integrating isolated system endpoints into a unified semantic layer, the business can now mathematically track the ROI of training hours against hard operational metrics like transaction error rates and 90-day employee attrition.
""")

# --- Live Dashboard Section ---
st.markdown("---")
st.subheader("Live Dashboard")
st.markdown(
    "Data below is pulled live from the "
    "[PHCORE Synthetic API](https://phcore-api.onrender.com/docs) and transformed "
    "in pandas using the same Silver and Gold logic built in Microsoft Fabric "
    "(see `fabric/dataflow_gen2_silver.md` and `fabric/gold_model.md`). "
    "The Render free-tier API may take ~60 seconds to wake up on first load."
)

tables = load_silver_tables()
gold = build_gold_facts(tables)
kpis = compute_kpis(tables, gold)

# KPI row
kpi_cols = st.columns(4)
kpi_cols[0].metric(
    "90-Day Separation Rate",
    f"{kpis['separation_rate_90d']:.1%}",
)
kpi_cols[1].metric(
    f"Avg Transaction Error Rate ({kpis['current_year']})",
    f"{kpis['avg_error_rate_current']:.1%}",
    delta=f"{(kpis['avg_error_rate_current'] - kpis['avg_error_rate_prior']):+.1%} vs {kpis['prior_year']}",
    delta_color="inverse",
)
kpi_cols[2].metric(
    "Total Training Investment",
    f"${kpis['total_investment']:,.0f}",
    delta=f"{kpis['yoy_investment_change']:+.1%} YoY",
)
kpi_cols[3].metric(
    "No-Show Rate",
    f"{kpis['no_show_rate']:.1%}",
)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div class="metric-card">
<h4>📋 Master Executive Briefing: Risk & Human Capital</h4>
{build_executive_summary(kpis)}
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    employees = tables["employees"]
    hires_by_year = (
        employees.groupby(employees["hire_date"].dt.year).size().rename("New Hires")
    )
    terms_by_year = (
        employees.dropna(subset=["termination_date"])
        .groupby(employees["termination_date"].dt.year)
        .size()
        .rename("Terminations")
    )
    trend_df = (
        pd.concat([hires_by_year, terms_by_year], axis=1)
        .fillna(0)
        .reset_index()
        .rename(columns={"index": "Year"})
    )
    fig_trend = px.line(
        trend_df, x="Year", y=["New Hires", "Terminations"],
        markers=True, title="Hiring vs. Attrition Trend (YoY)",
        color_discrete_map={"New Hires": "#58A6FF", "Terminations": "#F85149"},
    )
    fig_trend.update_layout(template="plotly_dark", legend_title_text="")
    st.plotly_chart(fig_trend, use_container_width=True)

with chart_col2:
    cert_facts = gold["certification_facts"]
    cert_summary = (
        cert_facts.groupby(["license_name", "status"]).size().reset_index(name="Count")
    )
    fig_cert = px.bar(
        cert_summary, x="license_name", y="Count", color="status",
        title="Compliance Risk Radar: Certifications by Status",
        color_discrete_map={"Active": "#3FB950", "Grace Period": "#D29922", "Expired": "#F85149"},
    )
    fig_cert.update_layout(
        template="plotly_dark", xaxis_title="", legend_title_text="",
        xaxis_tickangle=-30,
    )
    st.plotly_chart(fig_cert, use_container_width=True)

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    enrollment_facts = gold["enrollment_facts"]
    investment_by_year = enrollment_facts.groupby("year")["training_investment"].sum()
    error_by_year = gold["performance_facts"].groupby("year")["transaction_error_rate"].mean()
    yoy_df = pd.DataFrame({
        "Training Investment": investment_by_year,
        "Avg Transaction Error Rate": error_by_year,
    }).dropna().reset_index().rename(columns={"index": "year"})

    fig_yoy = make_subplots(specs=[[{"secondary_y": True}]])
    fig_yoy.add_trace(
        go.Bar(x=yoy_df["year"], y=yoy_df["Training Investment"], name="Training Investment ($)",
               marker_color="#58A6FF"),
        secondary_y=False,
    )
    fig_yoy.add_trace(
        go.Scatter(x=yoy_df["year"], y=yoy_df["Avg Transaction Error Rate"],
                   name="Avg Transaction Error Rate", mode="lines+markers",
                   line=dict(color="#F85149")),
        secondary_y=True,
    )
    fig_yoy.update_layout(
        template="plotly_dark", title="YoY Training Investment vs. Transaction Error Rate",
        legend_title_text="",
    )
    fig_yoy.update_yaxes(title_text="Training Investment ($)", secondary_y=False)
    fig_yoy.update_yaxes(title_text="Avg Error Rate", tickformat=".1%", secondary_y=True)
    fig_yoy.update_xaxes(title_text="Year", dtick=1)
    st.plotly_chart(fig_yoy, use_container_width=True)

with chart_col4:
    cost_by_dept = (
        enrollment_facts.groupby("department")["training_investment"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig_cost = px.bar(
        cost_by_dept, x="department", y="training_investment",
        title="Training Cost by Department",
        color_discrete_sequence=["#58A6FF"],
    )
    fig_cost.update_layout(
        template="plotly_dark", xaxis_title="", yaxis_title="Training Investment ($)",
    )
    st.plotly_chart(fig_cost, use_container_width=True)

# --- AI Insights Section ---
st.markdown("---")
st.subheader("🤖 Ask PHCORE AI")
st.markdown(
    "Conversational analyst grounded in the live KPIs above, powered by "
    "[Groq](https://groq.com/) (Llama 3.3 70B). Ask things like *\"which "
    "department has the highest attrition risk?\"* or *\"how does training "
    "investment compare year over year?\"*"
)

try:
    groq_api_key = st.secrets["GROQ_API_KEY"]
except (KeyError, FileNotFoundError):
    groq_api_key = ""
if not groq_api_key:
    with st.expander("🔑 Enter a Groq API key to enable the assistant"):
        groq_api_key = st.text_input(
            "Groq API key", type="password",
            help="Get a free key at console.groq.com. For permanent deployments, set "
                 "GROQ_API_KEY in .streamlit/secrets.toml instead.",
        )

if groq_api_key:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about the workforce, training, or compliance data..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                data_context = build_data_context(tables, gold, kpis)
                try:
                    reply = get_ai_response(groq_api_key, data_context, st.session_state.chat_history)
                except Exception as exc:
                    reply = f"⚠️ Couldn't reach Groq: {exc}"
            st.markdown(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
else:
    st.info("Provide a Groq API key above to start chatting with the data.")