import React, { useState, useRef, useEffect } from 'react'
import { api, aiApi } from '../utils/api'

function scoreColor(score) {
  if (score >= 80) return '#22c55e'
  if (score >= 65) return '#84cc16'
  if (score >= 50) return '#f59e0b'
  if (score >= 35) return '#f97316'
  return '#ef4444'
}

export default function SiteComparison({ sites, onRemove, useCase, openaiKey }) {
  const [comparing, setComparing] = useState(false)
  const [comparison, setComparison] = useState(null)
  const [error, setError] = useState(null)
  const [aiText, setAiText] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [showAi, setShowAi] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    if (bottomRef.current && aiText) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [aiText])

  const handleCompare = async () => {
    if (sites.length < 2) return
    setComparing(true)
    setError(null)
    try {
      const requests = sites.map((s) => ({
        lat: s.lat,
        lng: s.lng,
        use_case: 'retail',
        radius_km: 1.0,
      }))
      const res = await api.compareSites(requests)
      setComparison(res.data)
    } catch (err) {
      setError('Comparison failed.')
      console.error('Compare failed:', err)
    } finally {
      setComparing(false)
    }
  }

  const handleAiCompare = () => {
    if (sites.length < 2) return
    if (!openaiKey) { setAiText('Error: Enter your OpenAI API key in the sidebar first.'); setShowAi(true); return }
    setAiText('')
    setShowAi(true)
    setAiLoading(true)
    aiApi.compareSites(
      sites,
      useCase || 'retail',
      openaiKey,
      (chunk) => setAiText((prev) => prev + chunk),
      () => setAiLoading(false),
      (err) => { setAiText('Error: ' + err.message); setAiLoading(false) }
    )
  }

  const handleExportCsv = async () => {
    try {
      const requests = sites.map((s) => ({
        lat: s.lat,
        lng: s.lng,
        use_case: 'retail',
        radius_km: 1.0,
      }))
      const res = await api.exportCsv(requests)
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = 'site_comparison.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('CSV export failed:', err)
    }
  }

  // Best site from comparison ranking
  const bestIdx =
    comparison?.ranking?.[0] !== undefined ? comparison.ranking[0] : null

  return (
    <div className="p-3">
      <div className="flex items-start gap-3 overflow-x-auto">
        {/* Label */}
        <div className="text-xs text-slate-400 flex-shrink-0 pt-2">
          <div className="font-semibold">{sites.length} sites</div>
          <div className="text-slate-600">pinned</div>
        </div>

        {/* Site chips */}
        {sites.map((site, idx) => {
          const color = scoreColor(site.composite_score)
          const isBest = bestIdx === idx
          return (
            <div
              key={idx}
              className={`flex-shrink-0 flex items-center gap-2 rounded-lg px-3 py-2 border transition-all ${
                isBest
                  ? 'bg-green-900/30 border-green-500/50'
                  : 'bg-slate-700/60 border-slate-600/40'
              }`}
            >
              {isBest && (
                <span className="text-green-400 text-xs font-bold">★</span>
              )}
              <div
                className="text-xs font-bold"
                style={{ color }}
              >
                #{idx + 1} {site.composite_score.toFixed(0)}/100
              </div>
              <div className="text-xs text-slate-400">({site.grade})</div>
              <div className="text-xs text-slate-500">
                {site.lat.toFixed(3)}, {site.lng.toFixed(3)}
              </div>
              <button
                onClick={() => onRemove(idx)}
                className="text-slate-500 hover:text-red-400 text-base ml-1 transition-colors"
              >
                ×
              </button>
            </div>
          )
        })}

        {/* Recommendation */}
        {comparison && (
          <div className="flex-shrink-0 text-xs bg-blue-900/30 text-blue-300 px-3 py-2 rounded-lg border border-blue-500/30 max-w-xs">
            {comparison.recommendation}
          </div>
        )}

        {error && (
          <div className="flex-shrink-0 text-xs text-red-400 px-2 py-2">
            {error}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-2 flex-shrink-0 ml-auto items-center">
          {sites.length >= 2 && (
            <>
              <button
                onClick={handleCompare}
                disabled={comparing}
                className="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
              >
                {comparing ? 'Comparing...' : 'Score Rank'}
              </button>
              <button
                onClick={handleAiCompare}
                disabled={aiLoading}
                className="px-3 py-2 bg-purple-700 hover:bg-purple-600 text-white rounded-lg text-xs font-semibold transition-colors disabled:opacity-50 flex items-center gap-1"
              >
                <span>✦</span>
                {aiLoading ? 'AI thinking...' : 'AI Compare'}
              </button>
            </>
          )}
          <button
            onClick={handleExportCsv}
            className="px-3 py-2 bg-slate-600 hover:bg-slate-500 text-slate-200 rounded-lg text-xs font-semibold transition-colors"
          >
            CSV
          </button>
          <button
            onClick={() => { setComparison(null); setError(null); setAiText(''); setShowAi(false) }}
            className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-400 rounded-lg text-xs transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {/* AI Comparison output */}
      {showAi && (
        <div className="mt-2 mx-3 mb-2 bg-slate-800/80 border border-purple-700/30 rounded-xl p-3 max-h-48 overflow-y-auto">
          <div className="flex items-center gap-1.5 text-xs text-purple-400 font-semibold mb-2">
            {aiLoading ? <span className="animate-pulse">◉</span> : <span>✓</span>}
            <span>Claude AI Comparison</span>
          </div>
          <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
            {aiText || <span className="text-slate-500 animate-pulse">Analyzing sites...</span>}
          </div>
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  )
}
