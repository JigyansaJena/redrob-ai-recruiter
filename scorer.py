"""
scorer.py — Brain of the Redrob Candidate Ranking System
---------------------------------------------------------
Scores each candidate against the Senior AI Engineer JD
using 4 signals: career, semantic, behavioral, logistics.
"""

import json
import re
from datetime import datetime, date
from typing import Any

import numpy as np

# ── Sentence-transformers (runs fully offline after first download) ──────────
from sentence_transformers import SentenceTransformer, util

# ── Load model once at import time (downloads ~90MB on first run) ────────────
print("Loading sentence-transformer model...")
MODEL = SentenceTransformer("all-MiniLM-L6-v2")
print("Model loaded!")

# ════════════════════════════════════════════════════════════════════════════
# JOB DESCRIPTION — key facts we extract manually from the JD
# ════════════════════════════════════════════════════════════════════════════

JD_TEXT = """
Senior AI Engineer role at Redrob AI, Series A startup in Pune or Noida India.
Requires 5-9 years experience in applied ML at product companies not services firms.
Must have production experience with embeddings retrieval systems sentence-transformers
OpenAI embeddings BGE E5 vector databases Pinecone Weaviate Qdrant Milvus FAISS
Elasticsearch OpenSearch hybrid search infrastructure.
Must have strong Python and experience designing evaluation frameworks for ranking systems
NDCG MRR MAP offline online A/B testing.
Nice to have: LLM fine-tuning LoRA QLoRA PEFT learning-to-rank XGBoost neural ranking
HR tech recruiting tech marketplace products distributed systems large scale inference.
Looking for someone who ships working systems fast scrappy product engineering attitude
not pure researcher. Must write production code. Prefers product company background
not consulting TCS Infosys Wipro Accenture Cognizant Capgemini.
Sub 30 day notice period preferred. Located in India Pune Noida Hyderabad Mumbai Delhi.
"""

# Pre-compute JD embedding once
JD_EMBEDDING = MODEL.encode(JD_TEXT, convert_to_tensor=True)

# ════════════════════════════════════════════════════════════════════════════
# SIGNAL 1 — CAREER SCORER (weight: 40%)
# Looks at actual job titles and company types, not skill keywords
# ════════════════════════════════════════════════════════════════════════════

# Companies explicitly called out as red flags in the JD
DISQUALIFYING_COMPANIES = {
    "tcs", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "hcl", "tech mahindra", "mindtree", "mphasis"
}

# Job titles that signal real AI/ML engineering work
AI_TITLES = {
    "ml engineer", "machine learning engineer", "ai engineer",
    "nlp engineer", "applied scientist", "research engineer",
    "data scientist", "recommendation systems", "search engineer",
    "ranking engineer", "retrieval engineer", "applied ml",
    "deep learning engineer", "computer vision engineer"
}

# Titles that are clearly NOT AI/ML — hard penalty
NON_AI_TITLES = {
    "mechanical engineer", "civil engineer", "graphic designer",
    "accountant", "hr manager", "marketing manager", "operations manager",
    "customer support", "content writer", "sales executive",
    "project manager", "business analyst", "mobile developer"
}

# Industries that are product companies (good signal)
PRODUCT_INDUSTRIES = {
    "food delivery", "e-commerce", "fintech", "transportation",
    "saas", "software", "ai/ml", "edtech", "healthtech",
    "gaming", "media", "marketplace"
}

def score_career(candidate: dict) -> tuple[float, str]:
    """
    Returns (score 0-1, reasoning string)
    Checks: job titles, company types, years of experience,
    career progression, no pure-consulting background
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])

    years_exp = profile.get("years_of_experience", 0)
    current_title = profile.get("current_title", "").lower()
    current_company = profile.get("current_company", "").lower()
    current_industry = profile.get("current_industry", "").lower()

    score = 0.0
    reasons = []

    # ── Experience years (0-20 points) ──────────────────────────────────────
    if 5 <= years_exp <= 9:
        score += 0.20
        reasons.append(f"{years_exp}y exp (ideal range)")
    elif 4 <= years_exp < 5:
        score += 0.14
        reasons.append(f"{years_exp}y exp (slightly under)")
    elif 9 < years_exp <= 12:
        score += 0.14
        reasons.append(f"{years_exp}y exp (slightly over)")
    elif years_exp > 12:
        score += 0.08
        reasons.append(f"{years_exp}y exp (over-experienced)")
    elif years_exp < 4:
        score += 0.04
        reasons.append(f"{years_exp}y exp (too junior)")

    # ── Current title check (0-25 points) ───────────────────────────────────
    title_match = any(t in current_title for t in AI_TITLES)
    if title_match:
        score += 0.25
        reasons.append(f"AI/ML title: {profile.get('current_title')}")
    elif any(t in current_title for t in NON_AI_TITLES):
        score += 0.0
        reasons.append(f"Non-AI title: {profile.get('current_title')} (hard penalty)")
    elif any(kw in current_title for kw in ["engineer", "developer", "scientist"]):
        score += 0.10
        reasons.append(f"Tech title: {profile.get('current_title')}")
    else:
        reasons.append(f"Non-tech title: {profile.get('current_title')} (penalty)")

    # ── Consulting company check (hard penalty) ──────────────────────────────
    all_companies = [j.get("company", "").lower() for j in career]
    all_companies.append(current_company)

    consulting_count = sum(
        1 for c in all_companies
        if any(bad in c for bad in DISQUALIFYING_COMPANIES)
    )
    total_jobs = max(len(career), 1)

    if consulting_count == 0:
        score += 0.20
        reasons.append("No consulting-only background")
    elif consulting_count / total_jobs < 0.5:
        score += 0.10
        reasons.append("Mix of product + consulting")
    else:
        score += 0.02
        reasons.append(f"Mostly consulting background ({consulting_count}/{total_jobs} jobs)")

    # ── Career descriptions: look for AI/ML keywords in actual work ──────────
    ai_keywords = [
        "embedding", "retrieval", "ranking", "recommendation", "nlp",
        "transformer", "vector", "search", "fine-tun", "llm", "bert",
        "model", "ml pipeline", "training", "inference", "a/b test",
        "ndcg", "faiss", "pinecone", "qdrant", "weaviate", "elasticsearch"
    ]

    descriptions = " ".join(
        j.get("description", "") for j in career
    ).lower()

    keyword_hits = sum(1 for kw in ai_keywords if kw in descriptions)

    if keyword_hits >= 6:
        score += 0.25
        reasons.append(f"Strong AI/ML work evidence ({keyword_hits} signals)")
    elif keyword_hits >= 3:
        score += 0.15
        reasons.append(f"Some AI/ML work evidence ({keyword_hits} signals)")
    elif keyword_hits >= 1:
        score += 0.05
        reasons.append(f"Weak AI/ML work evidence ({keyword_hits} signals)")
    else:
        reasons.append("No AI/ML work evidence in career descriptions")

    # ── Product company industry bonus ───────────────────────────────────────
    product_jobs = sum(
        1 for j in career
        if any(ind in j.get("industry", "").lower() for ind in PRODUCT_INDUSTRIES)
    )
    if product_jobs >= 2:
        score += 0.10
        reasons.append(f"Product company experience ({product_jobs} roles)")
    elif product_jobs == 1:
        score += 0.05
        reasons.append("Some product company experience")

    if any(t in current_title for t in NON_AI_TITLES):
        score = min(score, 0.30)
        reasons.append("CAPPED: non-AI current title")

    score = min(score, 1.0)
    return round(score, 3), " | ".join(reasons)


# ════════════════════════════════════════════════════════════════════════════
# SIGNAL 2 — SEMANTIC SCORER (weight: 30%)
# Compares candidate text to JD using AI embeddings
# ════════════════════════════════════════════════════════════════════════════

def score_semantic(candidate: dict) -> tuple[float, str]:
    """
    Builds a text representation of the candidate and computes
    cosine similarity against the JD embedding.
    Returns (score 0-1, reasoning)
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])

    # Build candidate text from all meaningful fields
    parts = []

    if profile.get("headline"):
        parts.append(profile["headline"])

    if profile.get("summary"):
        parts.append(profile["summary"])

    # Add career descriptions (most important)
    for job in career:
        if job.get("description"):
            parts.append(job["description"])
        if job.get("title"):
            parts.append(job["title"])

    # Add skills
    skill_names = [s["name"] for s in skills if s.get("name")]
    if skill_names:
        parts.append("Skills: " + ", ".join(skill_names))

    candidate_text = " ".join(parts)

    if not candidate_text.strip():
        return 0.0, "No text to analyze"

    # Compute embedding and similarity
    candidate_embedding = MODEL.encode(candidate_text, convert_to_tensor=True)
    similarity = float(util.cos_sim(JD_EMBEDDING, candidate_embedding)[0][0])

    # Cosine similarity is usually 0.2-0.7 for good matches
    # Normalize to 0-1 range (0.2 = 0, 0.65+ = 1)
    normalized = max(0.0, (similarity - 0.20) / 0.45)
    normalized = min(normalized, 1.0)

    reason = f"Semantic similarity: {similarity:.3f}"
    return round(normalized, 3), reason


# ════════════════════════════════════════════════════════════════════════════
# SIGNAL 3 — BEHAVIORAL SCORER (weight: 20%)
# Is this person actually available and responsive?
# ════════════════════════════════════════════════════════════════════════════

def days_since(date_str: str) -> int:
    """How many days since a given date string (YYYY-MM-DD)"""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (date.today() - d).days
    except Exception:
        return 999

def score_behavioral(candidate: dict) -> tuple[float, str]:
    """
    Scores based on platform activity signals.
    A great candidate who isn't responsive/available isn't actually hireable.
    """
    signals = candidate.get("redrob_signals", {})
    score = 0.0
    reasons = []

    # ── Recency: when did they last log in? (0-25 points) ───────────────────
    last_active = signals.get("last_active_date", "2020-01-01")
    days_inactive = days_since(last_active)

    if days_inactive <= 30:
        score += 0.25
        reasons.append("Active in last 30 days")
    elif days_inactive <= 90:
        score += 0.15
        reasons.append(f"Active {days_inactive}d ago")
    elif days_inactive <= 180:
        score += 0.08
        reasons.append(f"Inactive {days_inactive}d (concerning)")
    else:
        score += 0.0
        reasons.append(f"Inactive {days_inactive}d (likely unavailable)")

    # ── Open to work flag (0-20 points) ─────────────────────────────────────
    if signals.get("open_to_work_flag"):
        score += 0.20
        reasons.append("Marked open to work")
    else:
        reasons.append("Not marked open to work")

    # ── Recruiter response rate (0-20 points) ────────────────────────────────
    response_rate = signals.get("recruiter_response_rate", 0)
    if response_rate >= 0.6:
        score += 0.20
        reasons.append(f"High response rate ({response_rate:.0%})")
    elif response_rate >= 0.3:
        score += 0.10
        reasons.append(f"Moderate response rate ({response_rate:.0%})")
    else:
        reasons.append(f"Low response rate ({response_rate:.0%})")

    # ── Profile completeness (0-15 points)
    completeness = signals.get("profile_completeness_score", 0)
    score += (completeness / 100) * 0.15

    # ── GitHub activity (0-10 points) 
    github = signals.get("github_activity_score", -1)
    if github >= 30:
        score += 0.10
        reasons.append(f"Active GitHub ({github:.0f})")
    elif github >= 10:
        score += 0.05
        reasons.append(f"Some GitHub activity ({github:.0f})")
    elif github == -1:
        reasons.append("No GitHub linked")

    # ── Interview completion rate (0-10 points)
    interview_rate = signals.get("interview_completion_rate", 0)
    score += interview_rate * 0.10

    score = min(score, 1.0)
    return round(score, 3), " | ".join(reasons)


# SIGNAL 4 — LOGISTICS SCORER (weight: 10%)
# Location, notice period, work mode, salary

PREFERRED_LOCATIONS = {
    "noida", "pune", "hyderabad", "mumbai", "delhi",
    "bangalore", "gurgaon", "chennai", "india"
}

def score_logistics(candidate: dict) -> tuple[float, str]:
    """
    Scores practical hiring fit: location, notice period, work mode.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    score = 0.0
    reasons = []

    # ── Location (0-40 points) ───────────────────────────────────────────────
    location = profile.get("location", "").lower()
    country = profile.get("country", "").lower()

    if any(loc in location for loc in PREFERRED_LOCATIONS) or country == "india":
        score += 0.40
        reasons.append(f"India-based ({profile.get('location')})")
    elif signals.get("willing_to_relocate"):
        score += 0.20
        reasons.append("Willing to relocate")
    else:
        reasons.append(f"Outside India ({profile.get('country')}), not relocating")

    # ── Notice period (0-35 points) ──────────────────────────────────────────
    notice = signals.get("notice_period_days", 90)
    if notice <= 30:
        score += 0.35
        reasons.append(f"Notice: {notice}d (ideal)")
    elif notice <= 60:
        score += 0.20
        reasons.append(f"Notice: {notice}d (acceptable)")
    elif notice <= 90:
        score += 0.10
        reasons.append(f"Notice: {notice}d (long)")
    else:
        score += 0.0
        reasons.append(f"Notice: {notice}d (too long)")

    # ── Work mode preference (0-25 points) ──────────────────────────────────
    work_mode = signals.get("preferred_work_mode", "")
    if work_mode in ["hybrid", "flexible", "onsite"]:
        score += 0.25
        reasons.append(f"Work mode: {work_mode} (fits hybrid role)")
    elif work_mode == "remote":
        score += 0.10
        reasons.append("Prefers remote (JD is hybrid)")

    score = min(score, 1.0)
    return round(score, 3), " | ".join(reasons)


# ════════════════════════════════════════════════════════════════════════════
# SKILLS BONUS — extra points for key skills from JD
# ════════════════════════════════════════════════════════════════════════════

CRITICAL_SKILLS = {
    "embeddings", "sentence transformers", "faiss", "pinecone", "qdrant",
    "weaviate", "milvus", "elasticsearch", "opensearch", "vector search",
    "information retrieval", "hugging face transformers", "machine learning",
    "recommendation systems", "ranking", "nlp", "bm25", "fine-tuning llms",
    "peft", "lora", "mlflow", "scikit-learn", "feature engineering"
}

def score_skills_bonus(candidate: dict) -> tuple[float, str]:
    """
    Bonus score for having critical JD skills with good proficiency.
    Also checks skill assessment scores (verified skills).
    """
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    assessments = signals.get("skill_assessment_scores", {})

    score = 0.0
    matched = []

    proficiency_weights = {
        "expert": 1.0,
        "advanced": 0.8,
        "intermediate": 0.5,
        "beginner": 0.2
    }

    for skill in skills:
        name = skill.get("name", "").lower()
        proficiency = skill.get("proficiency", "beginner")
        duration = skill.get("duration_months", 0)

        if any(crit in name for crit in CRITICAL_SKILLS):
            weight = proficiency_weights.get(proficiency, 0.2)
            # Bonus for long duration (real experience)
            duration_bonus = min(duration / 60, 1.0) * 0.2
            skill_score = weight + duration_bonus
            score += skill_score
            matched.append(f"{skill.get('name')}({proficiency})")

    # Bonus for verified assessment scores on relevant skills
    for skill_name, assessment_score in assessments.items():
        if any(crit in skill_name.lower() for crit in CRITICAL_SKILLS):
            if assessment_score >= 70:
                score += 0.3
                matched.append(f"Verified:{skill_name}({assessment_score:.0f})")
            elif assessment_score >= 50:
                score += 0.15

    # Normalize: cap at 1.0
    normalized = min(score / 3.0, 1.0)
    reason = f"Key skills: {', '.join(matched[:5])}" if matched else "No critical skills matched"
    return round(normalized, 3), reason


# ════════════════════════════════════════════════════════════════════════════
# HONEYPOT DETECTOR
# The dataset has ~80 fake candidates with impossible profiles
# ════════════════════════════════════════════════════════════════════════════

def is_honeypot(candidate: dict) -> bool:
    """
    Detects candidates with impossible/suspicious profiles.
    Returns True if candidate looks like a honeypot.
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])

    # Check: company founded after candidate's tenure started
    for job in career:
        start = job.get("start_date", "")
        company = job.get("company", "").lower()
        duration = job.get("duration_months", 0)
        # Unrealistically long duration at a tiny company
        if duration > 120 and job.get("company_size") == "1-10":
            return True

    # Check: expert in too many skills with 0 months experience
    expert_zero = sum(
        1 for s in skills
        if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0
    )
    if expert_zero >= 3:
        return True

    # Check: years of experience impossibly high vs career history
    years_exp = profile.get("years_of_experience", 0)
    total_career_months = sum(j.get("duration_months", 0) for j in career)
    if years_exp > 5 and total_career_months < 12:
        return True

    return False


# ════════════════════════════════════════════════════════════════════════════
# MAIN SCORER — combines all signals
# ════════════════════════════════════════════════════════════════════════════

WEIGHTS = {
    "career":    0.35,
    "semantic":  0.30,
    "behavioral":0.20,
    "skills":    0.10,
    "logistics": 0.05,
}

def score_candidate(candidate: dict) -> dict:
    """
    Scores a single candidate against the JD.
    Returns a dict with final score, sub-scores, and reasoning.
    """
    cid = candidate.get("candidate_id", "UNKNOWN")

    # Honeypot check first
    if is_honeypot(candidate):
        return {
            "candidate_id": cid,
            "final_score": 0.001,
            "career_score": 0,
            "semantic_score": 0,
            "behavioral_score": 0,
            "skills_score": 0,
            "logistics_score": 0,
            "reasoning": "Honeypot detected — impossible profile",
            "name": candidate.get("profile", {}).get("anonymized_name", ""),
            "title": candidate.get("profile", {}).get("current_title", ""),
            "location": candidate.get("profile", {}).get("location", ""),
            "years_exp": candidate.get("profile", {}).get("years_of_experience", 0),
        }

    # Compute all signals
    career_score,    career_reason    = score_career(candidate)
    semantic_score,  semantic_reason  = score_semantic(candidate)
    behavioral_score,behavioral_reason= score_behavioral(candidate)
    skills_score,    skills_reason    = score_skills_bonus(candidate)
    logistics_score, logistics_reason = score_logistics(candidate)

    # Weighted fusion
    final_score = (
        career_score     * WEIGHTS["career"]    +
        semantic_score   * WEIGHTS["semantic"]  +
        behavioral_score * WEIGHTS["behavioral"]+
        skills_score     * WEIGHTS["skills"]    +
        logistics_score  * WEIGHTS["logistics"]
    )

    # Build reasoning string for submission CSV
    profile = candidate.get("profile", {})
    name = profile.get("anonymized_name", "")
    title = profile.get("current_title", "")
    company = profile.get("current_company", "")
    years = profile.get("years_of_experience", 0)

    reasoning = (
        f"{title} at {company} ({years}y exp). "
        f"Career: {career_reason[:80]}. "
        f"Skills: {skills_reason[:60]}. "
        f"Availability: {behavioral_reason[:60]}."
    )

    return {
        "candidate_id": cid,
        "final_score": round(final_score, 4),
        "career_score": career_score,
        "semantic_score": semantic_score,
        "behavioral_score": behavioral_score,
        "skills_score": skills_score,
        "logistics_score": logistics_score,
        "reasoning": reasoning,
        "name": name,
        "title": title,
        "company": company,
        "location": profile.get("location", ""),
        "years_exp": years,
    }


def rank_candidates(candidates: list[dict], top_n: int = 100) -> list[dict]:
    """
    Scores all candidates and returns top N sorted by score descending.
    """
    print(f"Scoring {len(candidates)} candidates...")
    results = []

    for i, candidate in enumerate(candidates):
        if i % 10 == 0:
            print(f"  {i}/{len(candidates)} done...")
        result = score_candidate(candidate)
        results.append(result)

    # Sort by final score descending
    results.sort(key=lambda x: x["final_score"], reverse=True)

    # Assign ranks
    for i, result in enumerate(results[:top_n]):
        result["rank"] = i + 1

    print(f"Done! Top candidate: {results[0]['name']} ({results[0]['final_score']:.3f})")
    return results[:top_n]


# ════════════════════════════════════════════════════════════════════════════
# QUICK TEST — run this file directly to test on sample data
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    import os

    # Load sample candidates
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_candidates.json")

    with open(data_path, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    print(f"\nLoaded {len(candidates)} candidates from sample data")
    print("=" * 60)

    ranked = rank_candidates(candidates, top_n=len(candidates))

    print("\n🏆 TOP 10 CANDIDATES:")
    print("-" * 60)
    for r in ranked[:10]:
        print(f"#{r['rank']:2d} | {r['name']:<20} | {r['title']:<30} | Score: {r['final_score']:.3f}")
        print(f"      Career:{r['career_score']:.2f} Semantic:{r['semantic_score']:.2f} "
              f"Behavioral:{r['behavioral_score']:.2f} Skills:{r['skills_score']:.2f} "
              f"Logistics:{r['logistics_score']:.2f}")
        print()

    print("\n❌ BOTTOM 5 (should be non-AI people):")
    print("-" * 60)
    for r in ranked[-5:]:
        print(f"#{r['rank']:2d} | {r['name']:<20} | {r['title']:<30} | Score: {r['final_score']:.3f}")