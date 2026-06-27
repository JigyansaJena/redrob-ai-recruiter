# ⚡ Redrob AI Recruiter
### Intelligent Candidate Discovery & Ranking — Redrob Hackathon Submission

---

## What it does

An AI-powered candidate ranking system that goes beyond keyword matching to intelligently score and rank candidates for a Senior AI Engineer role. It combines **career analysis**, **semantic similarity**, **behavioral signals**, and **skill verification** into a single composite score.

---

## Architecture

```
candidates.json/jsonl/jsonl.gz
        │
        ▼
┌─────────────────────────────────────┐
│           scorer.py (Brain)         │
│                                     │
│  ┌──────────┐  ┌──────────────────┐ │
│  │ Career   │  │ Semantic (AI)    │ │
│  │ Scorer   │  │ sentence-        │ │
│  │ 35%      │  │ transformers 30% │ │
│  └──────────┘  └──────────────────┘ │
│  ┌──────────┐  ┌──────────────────┐ │
│  │Behavioral│  │ Skills Bonus     │ │
│  │ Scorer   │  │ + Logistics      │ │
│  │ 20%      │  │ 10% + 5%         │ │
│  └──────────┘  └──────────────────┘ │
│                                     │
│  ┌──────────────────────────────┐   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
        │
        ▼
  submission.csv (top 100 ranked)
```

---

## Scoring Signals

| Signal | Weight | What it measures |
|--------|--------|-----------------|
| Career Match | 35% | Job titles, company types (product vs consulting), AI/ML work in descriptions |
| Semantic Fit | 30% | Sentence-transformer embeddings vs JD — finds matches beyond keywords |
| Behavioral | 20% | Platform activity, recruiter response rate, last active date |
| Key Skills | 10% | Critical JD skills (embeddings, vector DBs, ranking systems) with proficiency weighting |
| Logistics | 5% | Location (India preferred), notice period, work mode |

---

## Key Design Decisions

**1. Career-first, not keyword-first**
The system looks at actual job titles and work descriptions, not just skills listed. A "Marketing Manager" with Pinecone in their skills gets a low career score regardless of keywords.

**2. Semantic similarity catches non-obvious matches**
A candidate who built recommendation systems using XGBoost and feature engineering matches the JD even without using words like RAG or Pinecone.

**3. Behavioral signals as a multiplier**
A perfect-on-paper candidate who hasn't logged in for 6 months and has 5% recruiter response rate is effectively unavailable. We penalize them appropriately.

**4. Honeypot detection**
Candidates with impossible profiles are automatically scored near 0.

**5. Consulting company penalty**
The JD explicitly calls out TCS, Infosys, Wipro, Accenture etc. as poor fits.

---

## Project Structure

```
redrob-ai-recruiter/
├── backend/
│   ├── scorer.py        # Core scoring engine
│   ├── main.py          # FastAPI REST API
│   └── rank.py          # CLI submission script
├── frontend/
│   └── src/App.jsx      # React dashboard
├── data/
│   └── sample_candidates.json
├── app.py               # Streamlit sandbox demo
├── requirements.txt
└── README.md
```

---

## Reproduce the submission

```bash
python backend/rank.py --candidates data/sample_candidates.json --out submission.csv
```

For the full 100K dataset:
```bash
python backend/rank.py --candidates data/candidates.jsonl.gz --out submission.csv
```

---

## Compute constraints

| Constraint | Limit | Our system |
|------------|-------|------------|
| Runtime | 5 min | ~2.5s for 50 candidates |
| Memory | 16 GB | ~500MB |
| GPU | Not allowed | CPU only |
| Network | Not allowed | Fully offline |

---

## Tech Stack

- Python 3.11, sentence-transformers, FastAPI, React + Vite + Tailwind, Streamlit, pandas

## AI Tools Used

- Claude — architecture discussion, code review
- GitHub Copilot — autocomplete