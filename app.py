import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from data import build_executive_summary, build_gold_facts, compute_kpis, load_silver_tables

# Configure the page
st.set_page_config(page_title="PHCORE | Data Engineering Portfolio", layout="wide", initial_sidebar_state="collapsed")

# Custom Dark Theme CSS
st.markdown("""
    <style>
    .main {background-color: #0D1117; color: #FFFFFF;}
    h1, h2, h3 {color: #58A6FF;}
    .metric-card {background-color: #161B22; padding: 20px; border-radius: 10px; border: 1px solid #30363D;}
    </style>
    """, unsafe_allow_html=True)

# Header Section
st.title("Predictive Human Capital & Operational Risk Engine (PHCORE)")
st.markdown("**Role:** Data & Analytics Engineer | **Tech Stack:** Microsoft Fabric, Python, Spark, DAX, Machine Learning")
st.markdown("---")

# Video & Links Section
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Architecture & Executive Overview")
    # Replace the URL below with your actual Loom video link once recorded
    st.video("https://www.youtube.com/watch?v=YOUR_VIDEO_ID_OR_LOOM_LINK") 

with col2:
    st.subheader("Project Resources")
    st.markdown("""
    <div class="metric-card">
        <h4>🔗 Live Deployments</h4>
        <p><a href="YOUR_POWER_BI_PUBLISH_TO_WEB_LINK" target="_blank">View Live Interactive Dashboard</a></p>
        <p><a href="YOUR_GITHUB_REPO_LINK" target="_blank">View GitHub Repository & Code</a></p>
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