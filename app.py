import streamlit as st

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