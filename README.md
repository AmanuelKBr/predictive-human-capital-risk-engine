# PHCORE — Predictive Human Capital & Operational Risk Engine

A People Analytics platform for a regional bank that links **training
investment** (completions, hours, spend) directly to **operational
outcomes** (transaction error rates, cross-sell performance, employee
retention) — turning L&D from a cost-center checkbox into a measurable
strategic ROI story.

**Live demo:** _add your Streamlit Cloud URL here_ ·
**Synthetic API:** [phcore-api.onrender.com/docs](https://phcore-api.onrender.com/docs)

> The Streamlit app's API call may take ~60 seconds on first load — it's
> hosted on Render's free tier, which sleeps after periods of inactivity.

---

## What this project demonstrates

- An end-to-end **Medallion Lakehouse** (Bronze → Silver → Gold) built in
  Microsoft Fabric on top of a synthetic FastAPI data source.
- A **Power BI semantic model** (star schema, DAX measures, dynamic
  Row-Level Security) built on the Gold layer.
- A **self-contained Streamlit dashboard** that replicates the Silver/Gold
  transformations and DAX measures in pandas, so the live demo works
  independently of the Fabric trial.
- A **conversational AI assistant** (Groq / Llama 3.3 70B) grounded in the
  live KPIs, for natural-language Q&A over the dataset.

---

## Architecture

```
FastAPI (synthetic data) ──▶ Fabric Bronze (raw JSON via Data Pipeline)
                                   │
                                   ▼
                          Fabric Silver (Dataflow Gen2 / Power Query M)
                                   │
                                   ▼
                    Power BI Gold (star schema + DAX + RLS, Direct Lake)

FastAPI (synthetic data) ──▶ Streamlit app (pandas: Silver + Gold logic
                                              replicated, live KPIs,
                                              Plotly charts, AI assistant)
```

### 1. Data source — `main.py`
A FastAPI service generates a relationally-consistent synthetic dataset for
a 20-branch regional bank: branches, employees, courses, training sessions,
enrollments, evaluations, certifications, and 3 years of monthly
performance data (seeded for restart-stability). Deployed on Render.

Endpoints: `/branches`, `/employees`, `/courses`, `/sessions`,
`/enrollments`, `/evaluations`, `/certifications`, `/monthly_performance`.

### 2. Microsoft Fabric Lakehouse — `fabric/`
- **Bronze** — `PL_Ingest_PHCORE_Bronze/`: a Data Pipeline that wakes the
  API, then copies each endpoint's JSON into `Files/bronze/raw_json/`.
- **Silver** — `dataflow_gen2_silver.md`: Power Query M for all 8 entities
  (type enforcement, null normalization, dedup, audit columns, plus a
  synthetic `email` column on employees for RLS and a date-truncated
  `start_timestamp` on sessions).
  `NB_Cleanse_PHCORE_Silver.ipynb` is a PySpark notebook equivalent that was
  prototyped but not used in the final pipeline (Fabric trial capacity
  limits forced a pivot to Dataflow Gen2).
- **Gold** — `gold_model.md`: the star schema (Dim_Date + fact/dimension
  relationships) built directly in the Power BI semantic model — there is
  no separate Gold notebook.
- **Power BI** — `Predictive Human Capital Risk Engine Dashboard.pbix`
  (Direct Lake semantic model):
  - `dax_measures.md` — 90-Day Separation Rate, Total Training Investment,
    YoY Training Investment Change, Avg Transaction Error Rate, Avg
    Cross-Sell Ratio, No-Show Rate, and an AI-style "Dynamic Executive
    Summary" narrative measure.
  - `rls_roles.md` — dynamic Row-Level Security scoping each branch
    manager to their own branch via `USERPRINCIPALNAME()`.

### 3. Streamlit dashboard — `app.py`, `data.py`, `ai_assistant.py`
Since the Fabric trial doesn't allow Power BI embedding (Publish to Web
disabled, Direct Lake requires live Fabric access), the dashboard is
rebuilt as a standalone app:

- `data.py` pulls Bronze data live from the FastAPI, applies the same
  Silver cleanup and Gold star-schema joins as the Fabric pipeline, and
  computes pandas equivalents of every DAX measure.
- `app.py` renders live KPIs, an auto-generated executive briefing, and
  Plotly charts (hiring vs. attrition, compliance risk by certification
  status, YoY training investment vs. error rate, training cost by
  department).
- `ai_assistant.py` wires up a Groq-powered chat assistant (Llama 3.3 70B)
  grounded in a generated summary of the live data.

---

## Running locally

```bash
pip install -r requirements.txt

# Run the synthetic data API
uvicorn main:app --reload

# Run the dashboard (in another terminal)
streamlit run app.py
```

To enable the AI assistant, create `.streamlit/secrets.toml` (gitignored):

```toml
GROQ_API_KEY = "your-groq-api-key"
```

(Get a free key at [console.groq.com](https://console.groq.com).) Without
a secrets file, the app shows a sidebar field to enter a key for the
current session only.

---

## Tech stack

Python · FastAPI · Faker · Docker · Microsoft Fabric (Data Pipelines,
Dataflow Gen2, Power BI Direct Lake) · DAX · Power Query M · Streamlit ·
Pandas · Plotly · Groq (Llama 3.3 70B)
