"""
Live data layer for the PHCORE Streamlit dashboard.

Pulls Bronze data straight from the deployed FastAPI
(https://phcore-api.onrender.com), then replicates the Fabric Silver
cleanup (fabric/dataflow_gen2_silver.md) and Gold star-schema joins
(fabric/gold_model.md) in pandas, so the dashboard works independently
of the Fabric trial.
"""

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = "https://phcore-api.onrender.com"

ENDPOINTS = [
    "branches", "employees", "courses", "sessions",
    "enrollments", "evaluations", "monthly_performance", "certifications",
]


@st.cache_data(ttl=3600, show_spinner="Waking up the PHCORE API (cold start can take ~60s)...")
def _fetch(endpoint: str) -> pd.DataFrame:
    response = requests.get(f"{API_BASE_URL}/{endpoint}", timeout=90)
    response.raise_for_status()
    return pd.DataFrame(response.json())


@st.cache_data(ttl=3600)
def load_silver_tables() -> dict[str, pd.DataFrame]:
    """Fetch raw Bronze data and apply the same cleanup as the Silver
    Dataflow Gen2 (typed dates, synthetic email, date-truncated session
    timestamp)."""
    tables = {name: _fetch(name) for name in ENDPOINTS}

    employees = tables["employees"].copy()
    employees["hire_date"] = pd.to_datetime(employees["hire_date"])
    employees["termination_date"] = pd.to_datetime(employees["termination_date"])
    employees["email"] = (
        employees["first_name"].str.lower() + employees["employee_id"].str.lower() + "@phcore.com"
    )
    tables["employees"] = employees

    sessions = tables["sessions"].copy()
    sessions["start_timestamp"] = pd.to_datetime(sessions["start_timestamp"]).dt.normalize()
    tables["sessions"] = sessions

    monthly_performance = tables["monthly_performance"].copy()
    monthly_performance["report_month"] = pd.to_datetime(monthly_performance["report_month"])
    tables["monthly_performance"] = monthly_performance

    certifications = tables["certifications"].copy()
    certifications["issue_date"] = pd.to_datetime(certifications["issue_date"])
    certifications["expiration_date"] = pd.to_datetime(certifications["expiration_date"])
    tables["certifications"] = certifications

    return tables


def build_gold_facts(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Replicate the Gold-layer star schema joins (fabric/gold_model.md)."""
    employees = tables["employees"]
    branches = tables["branches"]
    courses = tables["courses"]
    sessions = tables["sessions"]
    enrollments = tables["enrollments"]
    monthly_performance = tables["monthly_performance"]
    certifications = tables["certifications"]

    enrollment_facts = (
        enrollments
        .merge(sessions, on="session_id", how="left")
        .merge(courses, on="course_id", how="left")
        .merge(
            employees[["employee_id", "department", "branch_id", "hourly_rate", "status"]],
            on="employee_id", how="left", suffixes=("", "_employee"),
        )
        .merge(branches[["branch_id", "branch_name", "region"]], on="branch_id", how="left")
    )
    enrollment_facts["year"] = enrollment_facts["start_timestamp"].dt.year
    enrollment_facts["training_investment"] = (
        enrollment_facts["duration_hours"] * enrollment_facts["hourly_rate"]
    )

    performance_facts = monthly_performance.merge(
        employees[["employee_id", "department", "branch_id", "status"]],
        on="employee_id", how="left",
    )
    performance_facts["year"] = performance_facts["report_month"].dt.year

    certification_facts = certifications.merge(
        employees[["employee_id", "department", "branch_id"]], on="employee_id", how="left"
    )

    return {
        "enrollment_facts": enrollment_facts,
        "performance_facts": performance_facts,
        "certification_facts": certification_facts,
    }


def compute_kpis(tables: dict[str, pd.DataFrame], gold: dict[str, pd.DataFrame]) -> dict:
    """Re-implement the DAX measures from fabric/dax_measures.md in pandas."""
    employees = tables["employees"]
    enrollments = tables["enrollments"]
    enrollment_facts = gold["enrollment_facts"]
    performance_facts = gold["performance_facts"]

    current_year = int(performance_facts["year"].max())
    prior_year = current_year - 1

    total_employees = len(employees)
    terminated = employees[employees["status"] == "Terminated"]
    early_separations = terminated[
        (terminated["termination_date"] - terminated["hire_date"]).dt.days <= 90
    ]
    separation_rate_90d = len(early_separations) / total_employees if total_employees else 0.0

    new_hires_current = int((employees["hire_date"].dt.year == current_year).sum())
    new_hires_prior = int((employees["hire_date"].dt.year == prior_year).sum())

    avg_error_rate = performance_facts["transaction_error_rate"].mean()
    avg_error_rate_current = performance_facts.loc[
        performance_facts["year"] == current_year, "transaction_error_rate"
    ].mean()
    avg_error_rate_prior = performance_facts.loc[
        performance_facts["year"] == prior_year, "transaction_error_rate"
    ].mean()

    avg_cross_sell = performance_facts["cross_sell_ratio"].mean()

    no_show_rate = (enrollments["status"] == "No-Show").mean()

    investment_by_year = enrollment_facts.groupby("year")["training_investment"].sum()
    total_investment = enrollment_facts["training_investment"].sum()
    investment_current = investment_by_year.get(current_year, 0.0)
    investment_prior = investment_by_year.get(prior_year, 0.0)
    yoy_investment_change = (
        (investment_current - investment_prior) / investment_prior if investment_prior else 0.0
    )

    avg_hours_retained = enrollment_facts.loc[
        enrollment_facts["status_employee"] == "Active", "duration_hours"
    ].mean()

    return {
        "current_year": current_year,
        "prior_year": prior_year,
        "total_employees": total_employees,
        "active_employees": int((employees["status"] == "Active").sum()),
        "separation_rate_90d": separation_rate_90d,
        "new_hires_current": new_hires_current,
        "new_hires_prior": new_hires_prior,
        "avg_error_rate": avg_error_rate,
        "avg_error_rate_current": avg_error_rate_current,
        "avg_error_rate_prior": avg_error_rate_prior,
        "avg_cross_sell": avg_cross_sell,
        "no_show_rate": no_show_rate,
        "total_investment": total_investment,
        "investment_by_year": investment_by_year,
        "investment_current": investment_current,
        "investment_prior": investment_prior,
        "yoy_investment_change": yoy_investment_change,
        "avg_hours_retained": avg_hours_retained,
    }


def build_data_context(tables: dict[str, pd.DataFrame], gold: dict[str, pd.DataFrame], kpis: dict) -> str:
    """Build a compact text summary of the dataset for grounding the AI assistant."""
    employees = tables["employees"]
    branches = tables["branches"]
    enrollment_facts = gold["enrollment_facts"]
    cert_facts = gold["certification_facts"]
    performance_facts = gold["performance_facts"]

    headcount_by_dept = employees.groupby("department")["employee_id"].count().to_dict()
    headcount_by_region = (
        employees.merge(branches[["branch_id", "region"]], on="branch_id")
        .groupby("region")["employee_id"].count().to_dict()
    )
    error_by_dept = performance_facts.groupby("department")["transaction_error_rate"].mean().round(4).to_dict()
    cross_sell_by_dept = performance_facts.groupby("department")["cross_sell_ratio"].mean().round(3).to_dict()
    error_by_year = performance_facts.groupby("year")["transaction_error_rate"].mean().round(4).to_dict()
    cost_by_dept = enrollment_facts.groupby("department")["training_investment"].sum().round(2).to_dict()
    cert_status_counts = cert_facts["status"].value_counts().to_dict()
    investment_by_year = kpis["investment_by_year"].round(2).to_dict()

    return f"""PHCORE People Analytics dataset summary (synthetic banking data, 3-year history through {kpis['current_year']}-06):

KEY METRICS
- Total employees: {kpis['total_employees']} ({kpis['active_employees']} active, {kpis['total_employees'] - kpis['active_employees']} terminated)
- 90-Day Separation Rate (early attrition): {kpis['separation_rate_90d']:.1%}
- New hires: {kpis['new_hires_current']} in {kpis['current_year']}, {kpis['new_hires_prior']} in {kpis['prior_year']}
- Avg Transaction Error Rate: {kpis['avg_error_rate']:.2%} overall ({kpis['current_year']}: {kpis['avg_error_rate_current']:.2%}, {kpis['prior_year']}: {kpis['avg_error_rate_prior']:.2%})
- Avg Cross-Sell Ratio: {kpis['avg_cross_sell']:.2f}
- Training No-Show Rate: {kpis['no_show_rate']:.1%}
- Total Training Investment (3yr): ${kpis['total_investment']:,.0f}
- Avg Training Hours per active employee: {kpis['avg_hours_retained']:.1f}

BREAKDOWNS
- Headcount by department: {headcount_by_dept}
- Headcount by region: {headcount_by_region}
- Avg transaction error rate by department: {error_by_dept}
- Avg cross-sell ratio by department: {cross_sell_by_dept}
- Training investment by department: {cost_by_dept}
- Training investment by year: {investment_by_year}
- Avg transaction error rate by year: {error_by_year}
- Certification status counts: {cert_status_counts}
- Branches: {len(branches)} across regions {sorted(branches['region'].unique().tolist())}

Note: {kpis['current_year']} is a partial year (data through ~June), so {kpis['current_year']} totals are not directly comparable to full prior years.
"""


def build_executive_summary(kpis: dict) -> str:
    """Re-implement the Dynamic Executive Summary DAX measure as narrative text."""
    investment = f"${kpis['total_investment']:,.0f}"

    no_show = kpis["no_show_rate"]
    no_show_text = f"{no_show:.1%}"
    no_show_trend = (
        "HIGH: Bleeding overhead on empty seats." if no_show > 0.12
        else "HEALTHY: Attendance within tolerance."
    )

    error_rate = kpis["avg_error_rate"]
    error_text = f"{error_rate:.1%}"
    error_trend = (
        "CRITICAL: Exceeds 2.0% risk threshold." if error_rate > 0.02
        else "ON TRACK: Operating safely."
    )

    cross_sell = kpis["avg_cross_sell"]
    cross_text = f"{cross_sell:.2f}"
    cross_trend = (
        "LOW: Revenue generation lagging." if cross_sell < 0.20
        else "STRONG: Above standard baseline."
    )

    sep_rate = kpis["separation_rate_90d"]
    sep_text = f"{sep_rate:.1%}"
    sep_trend = (
        "HIGH FLIGHT RISK: Early attrition elevated." if sep_rate > 0.15
        else "STABLE: Retention holding."
    )

    return (
        f"**Capital Deployed:** {investment}  \n"
        f"**Training Waste (No-Shows):** {no_show_text} — {no_show_trend}\n\n"
        f"**Transaction Error Rate:** {error_text} — {error_trend}  \n"
        f"**Cross-Sell Conversion:** {cross_text} — {cross_trend}\n\n"
        f"**New Hires ({kpis['current_year']}):** {kpis['new_hires_current']:,}  \n"
        f"**90-Day Separation Rate:** {sep_text} — {sep_trend}  \n"
        f"**Avg Training (Retained Hires):** {kpis['avg_hours_retained']:.1f} hours"
    )
