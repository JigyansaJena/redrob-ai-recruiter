"""
main.py — FastAPI Backend for Redrob AI Recruiter
--------------------------------------------------
Endpoints:
  POST /rank        → rank a list of candidates against the JD
  GET  /candidate/:id → get a single candidate's full score breakdown
  GET  /health      → health check

Run with:
  uvicorn backend.main:app --reload --port 8000
"""

import json
import os
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))
from scorer import rank_candidates, score_candidate

# ════════════════════════════════════════════════════════════════════════════
# APP SETUP
# ════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Redrob AI Recruiter",
    description="Intelligent candidate ranking system for the Redrob hackathon",
    version="1.0.0"
)

# Allow React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ════════════════════════════════════════════════════════════════════════════
# LOAD SAMPLE DATA ON STARTUP
# ════════════════════════════════════════════════════════════════════════════

CANDIDATES_CACHE = []

def load_sample_data():
    """Load sample candidates into memory when server starts."""
    global CANDIDATES_CACHE
    data_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "sample_candidates.json"
    )
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            CANDIDATES_CACHE = json.load(f)
        print(f"Loaded {len(CANDIDATES_CACHE)} candidates into cache")
    else:
        print("Warning: sample_candidates.json not found")

load_sample_data()

# ════════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ════════════════════════════════════════════════════════════════════════════

class RankRequest(BaseModel):
    top_n: Optional[int] = 50
    # In future: custom JD text could go here

class CandidateScore(BaseModel):
    candidate_id: str
    rank: int
    final_score: float
    career_score: float
    semantic_score: float
    behavioral_score: float
    skills_score: float
    logistics_score: float
    reasoning: str
    name: str
    title: str
    company: str
    location: str
    years_exp: float

class RankResponse(BaseModel):
    total_candidates: int
    ranked: list[CandidateScore]
    top_candidate: str
    processing_time_ms: float

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.get("/health")
def health_check():
    """Simple health check — lets the frontend know the backend is running."""
    return {
        "status": "ok",
        "candidates_loaded": len(CANDIDATES_CACHE),
        "message": "Redrob AI Recruiter is running!"
    }


@app.post("/rank", response_model=RankResponse)
def rank(request: RankRequest):
    """
    Rank all loaded candidates and return top N.
    This is the main endpoint the React frontend calls.
    """
    import time
    start = time.time()

    if not CANDIDATES_CACHE:
        raise HTTPException(status_code=500, detail="No candidates loaded")

    top_n = min(request.top_n or 50, len(CANDIDATES_CACHE))

    # Run the ranker
    ranked = rank_candidates(CANDIDATES_CACHE, top_n=top_n)

    elapsed_ms = (time.time() - start) * 1000

    return RankResponse(
        total_candidates=len(CANDIDATES_CACHE),
        ranked=[CandidateScore(**r) for r in ranked],
        top_candidate=ranked[0]["name"] if ranked else "None",
        processing_time_ms=round(elapsed_ms, 1)
    )


@app.get("/candidate/{candidate_id}")
def get_candidate(candidate_id: str):
    """
    Get full details + score breakdown for a single candidate.
    Called when user clicks on a candidate card in the frontend.
    """
    # Find candidate in cache
    candidate = next(
        (c for c in CANDIDATES_CACHE if c.get("candidate_id") == candidate_id),
        None
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate {candidate_id} not found"
        )

    # Score this single candidate
    result = score_candidate(candidate)

    # Add full profile data for the frontend to display
    result["profile"] = candidate.get("profile", {})
    result["career_history"] = candidate.get("career_history", [])
    result["skills"] = candidate.get("skills", [])
    result["education"] = candidate.get("education", [])
    result["redrob_signals"] = candidate.get("redrob_signals", {})

    return result


@app.get("/candidates/all")
def get_all_candidates():
    """
    Return basic info for all candidates (for the frontend table).
    """
    results = []
    for c in CANDIDATES_CACHE:
        profile = c.get("profile", {})
        results.append({
            "candidate_id": c.get("candidate_id"),
            "name": profile.get("anonymized_name", ""),
            "title": profile.get("current_title", ""),
            "company": profile.get("current_company", ""),
            "location": profile.get("location", ""),
            "years_exp": profile.get("years_of_experience", 0),
            "country": profile.get("country", ""),
        })
    return {"total": len(results), "candidates": results}


@app.get("/stats")
def get_stats():
    """
    Return summary statistics about the candidate pool.
    Used by the frontend dashboard.
    """
    if not CANDIDATES_CACHE:
        return {"error": "No candidates loaded"}

    total = len(CANDIDATES_CACHE)

    # Count by country
    countries = {}
    industries = {}
    open_to_work = 0

    for c in CANDIDATES_CACHE:
        profile = c.get("profile", {})
        signals = c.get("redrob_signals", {})

        country = profile.get("country", "Unknown")
        countries[country] = countries.get(country, 0) + 1

        industry = profile.get("current_industry", "Unknown")
        industries[industry] = industries.get(industry, 0) + 1

        if signals.get("open_to_work_flag"):
            open_to_work += 1

    return {
        "total_candidates": total,
        "open_to_work": open_to_work,
        "countries": dict(sorted(countries.items(), key=lambda x: -x[1])[:10]),
        "top_industries": dict(sorted(industries.items(), key=lambda x: -x[1])[:10]),
    }