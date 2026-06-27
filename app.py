"""
app.py — Streamlit Sandbox for Redrob Hackathon
------------------------------------------------
This is the hosted demo required for hackathon submission.
Run locally:  streamlit run app.py
Deploy free:  https://streamlit.io/cloud
"""

import json
import os
import sys
import streamlit as st
import pandas as pd

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from backend.scorer import rank_candidates

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Redrob AI Recruiter",
    page_icon="⚡",
    layout="wide",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .stButton button {
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        font-size: 1rem;
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
    }
    .rank-badge {
        display: inline-block;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #2563eb;
        color: white;
        font-weight: bold;
        text-align: center;
        line-height: 32px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("# ⚡ Redrob AI Recruiter")
st.markdown("**Intelligent Candidate Discovery & Ranking** — Redrob Hackathon Submission")
st.divider()

# ── Load candidates ──────────────────────────────────────────────────────────
@st.cache_data
def load_candidates(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# File uploader OR use sample data
st.sidebar.header("📂 Data Source")
upload_mode = st.sidebar.radio(
    "Choose data source:",
    ["Use sample data (50 candidates)", "Upload your own JSON file"]
)

candidates = []

if upload_mode == "Upload your own JSON file":
    uploaded = st.sidebar.file_uploader(
        "Upload candidates JSON file",
        type=["json"],
        help="Upload a JSON array of candidate objects"
    )
    if uploaded:
        candidates = json.load(uploaded)
        st.sidebar.success(f"Loaded {len(candidates)} candidates!")
    else:
        st.sidebar.info("Waiting for file upload...")
else:
    sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_candidates.json")
    if os.path.exists(sample_path):
        candidates = load_candidates(sample_path)
        st.sidebar.success(f"Loaded {len(candidates)} sample candidates")
    else:
        st.sidebar.error("sample_candidates.json not found in data/ folder")

# ── Sidebar settings ─────────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.header("⚙️ Settings")
top_n = st.sidebar.slider("Show top N candidates", 5, min(50, len(candidates)) if candidates else 50, 20)

st.sidebar.divider()
st.sidebar.markdown("### 📊 Scoring Weights")
st.sidebar.markdown("""
| Signal | Weight |
|--------|--------|
| Career Match | 35% |
| Semantic Fit | 30% |
| Availability | 20% |
| Key Skills | 10% |
| Logistics | 5% |
""")

# ── Job Description display ──────────────────────────────────────────────────
with st.expander("📋 Job Description — Senior AI Engineer @ Redrob AI", expanded=False):
    st.markdown("""
**Role:** Senior AI Engineer — Founding Team  
**Company:** Redrob AI (Series A)  
**Location:** Pune/Noida, India (Hybrid)  
**Experience:** 5–9 years

**Must have:**
- Production experience with embeddings-based retrieval (sentence-transformers, BGE, E5)
- Vector databases (Pinecone, Weaviate, Qdrant, FAISS, Elasticsearch)
- Strong Python + evaluation frameworks (NDCG, MRR, MAP, A/B testing)

**Looking for:** Someone who ships fast, thinks about systems not just frameworks, 
prefers product companies over pure consulting backgrounds.
    """)

st.divider()

# ── Main ranking section ──────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
if candidates:
    open_to_work = sum(1 for c in candidates if c.get("redrob_signals", {}).get("open_to_work_flag"))
    india_count = sum(1 for c in candidates if c.get("profile", {}).get("country") == "India")
    col1.metric("Total Candidates", len(candidates))
    col2.metric("Open to Work", open_to_work)
    col3.metric("India-based", india_count)
    col4.metric("Top N to Show", top_n)

st.divider()

# ── Rank button ───────────────────────────────────────────────────────────────
if not candidates:
    st.warning("Please load candidates first using the sidebar.")
else:
    if st.button("🚀 Rank Candidates Now", use_container_width=True):

        with st.spinner("Running AI scoring engine... (career + semantic + behavioral + skills)"):
            import time
            start = time.time()
            ranked = rank_candidates(candidates, top_n=top_n)
            elapsed = time.time() - start

        st.success(f"✅ Ranked {len(candidates)} candidates in {elapsed:.1f}s | Top candidate: **{ranked[0]['name']}**")
        st.divider()

        # ── Top candidate highlight ───────────────────────────────────────────
        top = ranked[0]
        st.markdown("### 🏆 Top Match")
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.markdown(f"**{top['name']}**")
            st.markdown(f"*{top['title']} @ {top['company']}*")
            st.markdown(f"📍 {top['location']} · {top['years_exp']}y experience")
            st.markdown(f"_{top['reasoning'][:200]}..._")
        with c2:
            st.metric("Overall Score", f"{top['final_score']*100:.1f}%")
            st.metric("Career Match", f"{top['career_score']*100:.0f}%")
            st.metric("Semantic Fit", f"{top['semantic_score']*100:.0f}%")
        with c3:
            st.metric("Availability", f"{top['behavioral_score']*100:.0f}%")
            st.metric("Key Skills", f"{top['skills_score']*100:.0f}%")
            st.metric("Logistics", f"{top['logistics_score']*100:.0f}%")

        st.divider()

        # ── Full ranking table ────────────────────────────────────────────────
        st.markdown(f"### 📊 Top {len(ranked)} Ranked Candidates")

        # Build dataframe
        rows = []
        for r in ranked:
            rows.append({
                "Rank": r["rank"],
                "Name": r["name"],
                "Title": r["title"],
                "Company": r["company"],
                "Location": r["location"],
                "Exp": f"{r['years_exp']}y",
                "Score": f"{r['final_score']*100:.1f}%",
                "Career": f"{r['career_score']*100:.0f}%",
                "Semantic": f"{r['semantic_score']*100:.0f}%",
                "Availability": f"{r['behavioral_score']*100:.0f}%",
                "Skills": f"{r['skills_score']*100:.0f}%",
            })

        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn(width="small"),
                "Score": st.column_config.TextColumn(width="small"),
            }
        )

        # ── Score breakdown chart ─────────────────────────────────────────────
        st.divider()
        st.markdown("### 📈 Score Distribution — Top 10")

        chart_data = pd.DataFrame({
            "Candidate": [r["name"].split()[0] for r in ranked[:10]],
            "Career": [r["career_score"] for r in ranked[:10]],
            "Semantic": [r["semantic_score"] for r in ranked[:10]],
            "Availability": [r["behavioral_score"] for r in ranked[:10]],
            "Skills": [r["skills_score"] for r in ranked[:10]],
        }).set_index("Candidate")

        st.bar_chart(chart_data, height=300)

        # ── Download submission CSV ───────────────────────────────────────────
        st.divider()
        st.markdown("### 📥 Download Submission CSV")

        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for r in ranked[:100]:
            writer.writerow([
                r["candidate_id"],
                r["rank"],
                f"{r['final_score']:.4f}",
                r["reasoning"]
            ])

        st.download_button(
            label="⬇️ Download submission.csv",
            data=output.getvalue(),
            file_name="submission.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.caption(f"CSV contains top {min(len(ranked), 100)} candidates in hackathon submission format.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#94a3b8; font-size:0.8rem;'>
Redrob AI Hackathon — Intelligent Candidate Discovery & Ranking<br>
Built with Python · FastAPI · React · Sentence Transformers · Streamlit
</div>
""", unsafe_allow_html=True)