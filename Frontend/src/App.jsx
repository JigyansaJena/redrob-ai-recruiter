import { useState, useEffect } from "react"
import axios from "axios"

const API = "http://localhost:8000"

// Score bar component 
function ScoreBar({ value, color = "bg-blue-500" }) {
  const pct = Math.round(value * 100)
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-200 rounded-full h-2">
        <div
          className={`${color} h-2 rounded-full transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-600 w-8 text-right">{pct}%</span>
    </div>
  )
}

//  Score badge
function ScoreBadge({ score }) {
  const pct = Math.round(score * 100)
  const color =
    pct >= 70 ? "bg-green-100 text-green-800 border-green-300" :
    pct >= 50 ? "bg-yellow-100 text-yellow-800 border-yellow-300" :
                "bg-red-100 text-red-800 border-red-300"
  return (
    <span className={`px-2 py-1 rounded-full text-sm font-bold border ${color}`}>
      {pct}%
    </span>
  )
}

//  Candidate detail modal 
function CandidateModal({ candidate, onClose }) {
  if (!candidate) return null
  const p = candidate.profile || {}
  const signals = candidate.redrob_signals || {}
  const skills = candidate.skills || []
  const career = candidate.career_history || []

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-2xl">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold">{candidate.name}</h2>
              <p className="text-blue-100">{candidate.title} @ {candidate.company}</p>
              <p className="text-blue-200 text-sm">{candidate.location} · {candidate.years_exp}y exp</p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-black">{Math.round(candidate.final_score * 100)}</div>
              <div className="text-blue-200 text-sm">/ 100</div>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-5">
          {/* Score breakdown */}
          <div>
            <h3 className="font-bold text-gray-800 mb-3">Score Breakdown</h3>
            <div className="space-y-2">
              {[
                { label: "Career Match", value: candidate.career_score, color: "bg-blue-500" },
                { label: "Semantic Fit", value: candidate.semantic_score, color: "bg-purple-500" },
                { label: "Availability", value: candidate.behavioral_score, color: "bg-green-500" },
                { label: "Key Skills", value: candidate.skills_score, color: "bg-yellow-500" },
                { label: "Logistics", value: candidate.logistics_score, color: "bg-pink-500" },
              ].map(({ label, value, color }) => (
                <div key={label} className="flex items-center gap-3">
                  <span className="text-sm text-gray-600 w-28">{label}</span>
                  <div className="flex-1"><ScoreBar value={value} color={color} /></div>
                </div>
              ))}
            </div>
          </div>

          {/* Reasoning */}
          <div>
            <h3 className="font-bold text-gray-800 mb-2">AI Reasoning</h3>
            <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3 leading-relaxed">
              {candidate.reasoning}
            </p>
          </div>

          {/* Skills */}
          {skills.length > 0 && (
            <div>
              <h3 className="font-bold text-gray-800 mb-2">Skills</h3>
              <div className="flex flex-wrap gap-2">
                {skills.slice(0, 12).map((s, i) => {
                  const colors = {
                    expert: "bg-purple-100 text-purple-800",
                    advanced: "bg-blue-100 text-blue-800",
                    intermediate: "bg-green-100 text-green-800",
                    beginner: "bg-gray-100 text-gray-700",
                  }
                  return (
                    <span key={i} className={`px-2 py-1 rounded text-xs font-medium ${colors[s.proficiency] || colors.beginner}`}>
                      {s.name}
                    </span>
                  )
                })}
              </div>
            </div>
          )}

          {/* Career */}
          {career.length > 0 && (
            <div>
              <h3 className="font-bold text-gray-800 mb-2">Career History</h3>
              <div className="space-y-2">
                {career.slice(0, 3).map((job, i) => (
                  <div key={i} className="flex gap-3 text-sm">
                    <div className="w-2 h-2 rounded-full bg-blue-400 mt-1.5 shrink-0" />
                    <div>
                      <span className="font-medium">{job.title}</span>
                      <span className="text-gray-500"> @ {job.company}</span>
                      <span className="text-gray-400 text-xs ml-2">({job.duration_months}mo)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Signals */}
          <div>
            <h3 className="font-bold text-gray-800 mb-2">Platform Signals</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {[
                { label: "Last Active", value: signals.last_active_date },
                { label: "Notice Period", value: `${signals.notice_period_days}d` },
                { label: "Response Rate", value: `${Math.round((signals.recruiter_response_rate || 0) * 100)}%` },
                { label: "GitHub Score", value: signals.github_activity_score === -1 ? "Not linked" : signals.github_activity_score },
                { label: "Open to Work", value: signals.open_to_work_flag ? "Yes ✅" : "No" },
                { label: "Work Mode", value: signals.preferred_work_mode },
              ].map(({ label, value }) => (
                <div key={label} className="bg-gray-50 rounded p-2">
                  <div className="text-gray-500 text-xs">{label}</div>
                  <div className="font-medium">{value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="p-4 border-t">
          <button
            onClick={onClose}
            className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 rounded-lg transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

// Candidate row 
function CandidateRow({ candidate, onClick }) {
  const rankColor =
    candidate.rank <= 3 ? "bg-yellow-400 text-yellow-900" :
    candidate.rank <= 10 ? "bg-blue-100 text-blue-800" :
    "bg-gray-100 text-gray-600"

  return (
    <tr
      className="hover:bg-blue-50 cursor-pointer transition-colors border-b border-gray-100"
      onClick={() => onClick(candidate)}
    >
      <td className="py-3 px-4">
        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${rankColor}`}>
          {candidate.rank}
        </span>
      </td>
      <td className="py-3 px-4">
        <div className="font-medium text-gray-900">{candidate.name}</div>
        <div className="text-xs text-gray-500">{candidate.location}</div>
      </td>
      <td className="py-3 px-4">
        <div className="text-sm text-gray-700">{candidate.title}</div>
        <div className="text-xs text-gray-400">{candidate.company}</div>
      </td>
      <td className="py-3 px-4 text-sm text-gray-600">{candidate.years_exp}y</td>
      <td className="py-3 px-4">
        <ScoreBadge score={candidate.final_score} />
      </td>
      <td className="py-3 px-4">
        <div className="w-24">
          <ScoreBar
            value={candidate.career_score}
            color="bg-blue-400"
          />
          <ScoreBar
            value={candidate.semantic_score}
            color="bg-purple-400"
          />
          <ScoreBar
            value={candidate.behavioral_score}
            color="bg-green-400"
          />
        </div>
      </td>
    </tr>
  )
}

// Stat card 
function StatCard({ label, value, icon, color }) {
  return (
    <div className={`bg-white rounded-xl p-4 shadow-sm border border-gray-100`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-500 text-sm">{label}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
        </div>
        <div className="text-3xl">{icon}</div>
      </div>
    </div>
  )
}

// MAIN APP

export default function App() {
  const [ranked, setRanked] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(null)
  const [selectedDetail, setSelectedDetail] = useState(null)
  const [search, setSearch] = useState("")
  const [hasRanked, setHasRanked] = useState(false)
  const [processingTime, setProcessingTime] = useState(null)

  // Load stats on mount
  useEffect(() => {
    axios.get(`${API}/stats`)
      .then(r => setStats(r.data))
      .catch(() => {})
  }, [])

  // Fetch candidate detail when selected
  useEffect(() => {
    if (!selected) { setSelectedDetail(null); return }
    axios.get(`${API}/candidate/${selected.candidate_id}`)
      .then(r => setSelectedDetail(r.data))
      .catch(() => setSelectedDetail(selected))
  }, [selected])

  const handleRank = async () => {
    setLoading(true)
    setHasRanked(false)
    try {
      const res = await axios.post(`${API}/rank`, { top_n: 50 })
      setRanked(res.data.ranked)
      setProcessingTime(res.data.processing_time_ms)
      setHasRanked(true)
    } catch (e) {
      alert("Error: Make sure the backend is running on port 8000!")
    }
    setLoading(false)
  }

  const filtered = ranked.filter(c =>
    !search ||
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    c.location.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-700 to-purple-700 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-black tracking-tight">⚡ Redrob AI Recruiter</h1>
            <p className="text-blue-200 text-sm">Intelligent Candidate Discovery & Ranking</p>
          </div>
          <div className="flex items-center gap-3">
            {stats && (
              <span className="text-blue-200 text-sm">
                {stats.total_candidates} candidates loaded
              </span>
            )}
            <button
              onClick={handleRank}
              disabled={loading}
              className="bg-white text-blue-700 font-bold px-6 py-2.5 rounded-xl hover:bg-blue-50 transition disabled:opacity-50 disabled:cursor-not-allowed shadow"
            >
              {loading ? "Ranking..." : "🚀 Rank Candidates"}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {/* Stats row */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Candidates" value={stats.total_candidates} icon="👥" color="text-blue-600" />
            <StatCard label="Open to Work" value={stats.open_to_work} icon="✅" color="text-green-600" />
            <StatCard label="Top Country" value={Object.keys(stats.countries || {})[0] || "—"} icon="🌍" color="text-purple-600" />
            <StatCard label="Processing Time" value={processingTime ? `${(processingTime/1000).toFixed(1)}s` : "—"} icon="⚡" color="text-orange-600" />
          </div>
        )}

        {/* Welcome / empty state */}
        {!hasRanked && !loading && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
            <div className="text-6xl mb-4">🎯</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Ready to find the best candidates</h2>
            <p className="text-gray-500 mb-6 max-w-md mx-auto">
              Click <strong>Rank Candidates</strong> above to run the AI scoring engine
              and see the top matches for the Senior AI Engineer role.
            </p>
            <div className="flex justify-center gap-6 text-sm text-gray-400">
              <span>✦ Career matching</span>
              <span>✦ Semantic similarity</span>
              <span>✦ Behavioral signals</span>
              <span>✦ Honeypot detection</span>
            </div>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
            <div className="text-5xl mb-4 animate-bounce">⚙️</div>
            <h2 className="text-xl font-bold text-gray-700 mb-2">Scoring candidates...</h2>
            <p className="text-gray-400">Running career, semantic, behavioral and skills analysis</p>
          </div>
        )}

        {/* Results table */}
        {hasRanked && ranked.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            {/* Table header */}
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h2 className="font-bold text-gray-800">
                  Top {ranked.length} Candidates
                </h2>
                <p className="text-sm text-gray-500">
                  Ranked for: Senior AI Engineer — Redrob AI
                  {processingTime && ` · Scored in ${(processingTime/1000).toFixed(1)}s`}
                </p>
              </div>
              <input
                type="text"
                placeholder="Search by name, title, location..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-300"
              />
            </div>

            {/* Legend */}
            <div className="px-4 py-2 bg-gray-50 border-b border-gray-100 flex gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-blue-400 rounded inline-block"/> Career</span>
              <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-purple-400 rounded inline-block"/> Semantic</span>
              <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-green-400 rounded inline-block"/> Availability</span>
              <span className="ml-auto">Click any row for details</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs text-gray-500 uppercase tracking-wide border-b border-gray-100">
                    <th className="py-3 px-4">Rank</th>
                    <th className="py-3 px-4">Candidate</th>
                    <th className="py-3 px-4">Role</th>
                    <th className="py-3 px-4">Exp</th>
                    <th className="py-3 px-4">Score</th>
                    <th className="py-3 px-4">Signals</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(c => (
                    <CandidateRow
                      key={c.candidate_id}
                      candidate={c}
                      onClick={setSelected}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {filtered.length === 0 && (
              <div className="text-center py-8 text-gray-400">
                No candidates match your search
              </div>
            )}
          </div>
        )}

        {/* Score legend */}
        {hasRanked && (
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <p className="text-xs text-gray-500 font-medium mb-2">SCORING WEIGHTS</p>
            <div className="flex flex-wrap gap-4 text-sm">
              {[
                { label: "Career Match", w: "35%", color: "bg-blue-500" },
                { label: "Semantic Fit", w: "30%", color: "bg-purple-500" },
                { label: "Availability", w: "20%", color: "bg-green-500" },
                { label: "Key Skills", w: "10%", color: "bg-yellow-500" },
                { label: "Logistics", w: "5%", color: "bg-pink-500" },
              ].map(({ label, w, color }) => (
                <div key={label} className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${color}`} />
                  <span className="text-gray-600">{label}</span>
                  <span className="font-bold text-gray-800">{w}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Candidate detail modal */}
      {selected && selectedDetail && (
        <CandidateModal
          candidate={selectedDetail}
          onClose={() => { setSelected(null); setSelectedDetail(null) }}
        />
      )}
    </div>
  )
}
