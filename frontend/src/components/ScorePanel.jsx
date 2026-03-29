import React, { useState } from 'react'
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
} from 'recharts'
import { api } from '../utils/api'
import AIAnalysisPanel from './AIAnalysisPanel'

function scoreColor(score) {
  if (score >= 80) return '#22c55e'
  if (score >= 65) return '#84cc16'
  if (score >= 50) return '#f59e0b'
  if (score >= 35) return '#f97316'
  return '#ef4444'
}

function gradeColor(grade) {
  return (
    { A: '#22c55e', B: '#84cc16', C: '#f59e0b', D: '#f97316', F: '#ef4444' }[
      grade
    ] || '#94a3b8'
  )
}

function gradeLabel(grade) {
  return (
    {
      A: 'Excellent',
      B: 'Good',
      C: 'Fair',
      D: 'Poor',
      F: 'Critical',
    }[grade] || 'Unknown'
  )
}

const LAYER_ICONS = {
  demographic: '👥',
  transportation: '🛣️',
  poi: '📍',
  land_use: '🏗️',
  environmental: '🌿',
}

export default function ScorePanel({ site, onPin, onClose, isochroneData, isPinned, useCase, geminiKey }) {
  const [expandedLayer, setExpandedLayer] = useState(null)
  const [exporting, setExporting] = useState(false)
  const [activeChart, setActiveChart] = useState('radar') // 'radar' | 'bar'

  const radarData = site.breakdowns.map((b) => ({
    layer: b.layer_name.replace('_', ' '),
    score: b.score,
    fullMark: 100,
  }))

  const mainColor = scoreColor(site.composite_score)
  const gc = gradeColor(site.grade)

  const handleExport = async () => {
    setExporting(true)
    try {
      const res = await api.exportJson({
        lat: site.lat,
        lng: site.lng,
        use_case: 'retail',
        radius_km: 1.0,
      })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `site_${site.lat.toFixed(4)}_${site.lng.toFixed(4)}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Export failed:', err)
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="p-4 text-white min-h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="font-bold text-slate-100 text-sm">Site Analysis</h2>
          <div className="text-xs text-slate-500 mt-0.5">
            {site.lat.toFixed(5)}, {site.lng.toFixed(5)}
          </div>
        </div>
        <button
          onClick={onClose}
          className="w-7 h-7 rounded-full bg-slate-700 hover:bg-slate-600 text-slate-400 hover:text-white flex items-center justify-center text-lg transition-colors"
        >
          ×
        </button>
      </div>

      {/* Score Hero */}
      <div className="flex items-center gap-4 mb-5 p-4 rounded-xl bg-slate-800/60 border border-slate-700/50">
        <div
          className="relative flex-shrink-0 w-20 h-20 rounded-full flex items-center justify-center text-2xl font-black border-4"
          style={{ borderColor: mainColor, color: mainColor }}
        >
          {Math.round(site.composite_score)}
          <div
            className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white"
            style={{ backgroundColor: gc }}
          >
            {site.grade}
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div
            className="text-lg font-bold"
            style={{ color: gc }}
          >
            {gradeLabel(site.grade)}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Composite readiness score
          </div>
          <div className="text-xs text-slate-600 mt-1 font-mono truncate">
            H3: {site.h3_index}
          </div>
        </div>
      </div>

      {/* Chart Tabs */}
      <div className="flex gap-1 mb-2">
        {['radar', 'bar'].map((type) => (
          <button
            key={type}
            onClick={() => setActiveChart(type)}
            className={`flex-1 py-1.5 text-xs rounded-lg capitalize transition-all ${
              activeChart === type
                ? 'bg-slate-700 text-white'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {type} chart
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="h-44 mb-4">
        <ResponsiveContainer width="100%" height="100%">
          {activeChart === 'radar' ? (
            <RadarChart data={radarData}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis
                dataKey="layer"
                tick={{ fill: '#94a3b8', fontSize: 9 }}
              />
              <Radar
                dataKey="score"
                stroke={mainColor}
                fill={mainColor}
                fillOpacity={0.25}
                strokeWidth={2}
              />
              <Tooltip
                contentStyle={{
                  background: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#e2e8f0',
                  fontSize: '12px',
                }}
              />
            </RadarChart>
          ) : (
            <BarChart
              data={site.breakdowns.map((b) => ({
                name: b.layer_name.replace('_', ' '),
                score: b.score,
                contribution: b.contribution,
              }))}
              margin={{ top: 4, right: 4, left: -20, bottom: 4 }}
            >
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 9 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 9 }} />
              <Tooltip
                contentStyle={{
                  background: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#e2e8f0',
                  fontSize: '12px',
                }}
              />
              <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                {site.breakdowns.map((b, i) => (
                  <Cell key={i} fill={scoreColor(b.score)} />
                ))}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Layer Breakdowns */}
      <div className="mb-4">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Layer Scores
        </h3>
        {site.breakdowns.map((b) => (
          <div key={b.layer_name} className="mb-2">
            <button
              className="w-full text-left group"
              onClick={() =>
                setExpandedLayer(
                  expandedLayer === b.layer_name ? null : b.layer_name
                )
              }
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm">
                  {LAYER_ICONS[b.layer_name] || '📊'}
                </span>
                <span className="text-xs text-slate-300 capitalize flex-1">
                  {b.layer_name.replace('_', ' ')}
                </span>
                <span
                  className="text-xs font-bold"
                  style={{ color: scoreColor(b.score) }}
                >
                  {b.score.toFixed(0)}
                </span>
                <span className="text-xs text-slate-600">
                  {expandedLayer === b.layer_name ? '▲' : '▼'}
                </span>
              </div>
              <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${b.score}%`,
                    backgroundColor: scoreColor(b.score),
                  }}
                />
              </div>
            </button>

            {expandedLayer === b.layer_name && (
              <div className="mt-2 p-3 bg-slate-800/70 rounded-lg text-xs space-y-1.5 border border-slate-700/50 fade-in">
                {Object.entries(b.factors).map(([k, v]) => (
                  <div key={k} className="flex justify-between items-start gap-2">
                    <span className="text-slate-500 capitalize leading-relaxed">
                      {k.replace(/_/g, ' ')}
                    </span>
                    <span className="text-slate-200 font-medium text-right">
                      {typeof v === 'boolean' ? (
                        <span
                          className={v ? 'text-green-400' : 'text-red-400'}
                        >
                          {v ? '✓ Yes' : '✗ No'}
                        </span>
                      ) : typeof v === 'number' ? (
                        v.toLocaleString()
                      ) : Array.isArray(v) ? (
                        v.length ? v.join(', ') : 'None'
                      ) : (
                        String(v)
                      )}
                    </span>
                  </div>
                ))}
                <div className="border-t border-slate-700 pt-1.5 flex justify-between text-slate-500">
                  <span>Weight: {(b.weight * 100).toFixed(0)}%</span>
                  <span>+{b.contribution.toFixed(1)} pts</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Isochrone Catchment Areas */}
      {isochroneData?.isochrones?.length > 0 && (
        <div className="mb-4">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Catchment Areas
          </h3>
          <div className="grid grid-cols-3 gap-1.5">
            {isochroneData.isochrones.map((iso) => (
              <div
                key={iso.minutes}
                className="bg-slate-800/60 rounded-lg p-2.5 text-center border border-slate-700/40"
              >
                <div className="text-xs font-bold text-purple-400">
                  {iso.minutes} min
                </div>
                <div className="text-sm font-bold text-slate-200 mt-0.5">
                  {iso.population_within.toLocaleString()}
                </div>
                <div className="text-xs text-slate-500">people</div>
                <div className="text-xs text-slate-600 mt-0.5">
                  {iso.area_sqkm.toFixed(1)} km²
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Analysis */}
      <AIAnalysisPanel site={site} useCase={useCase || 'retail'} geminiKey={geminiKey} />

      {/* Recommendations */}
      <div className="mb-4">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Recommendations
        </h3>
        <div className="space-y-2">
          {site.recommendations.map((rec, i) => (
            <div
              key={i}
              className="flex gap-2 text-xs bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/40"
            >
              <span className="text-blue-400 flex-shrink-0 mt-0.5">→</span>
              <span className="text-slate-300 leading-relaxed">{rec}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 sticky bottom-0 pb-1 pt-2 bg-gradient-to-t from-slate-900/95">
        <button
          onClick={onPin}
          disabled={isPinned}
          className={`flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all ${
            isPinned
              ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/40'
          }`}
        >
          {isPinned ? '✓ Pinned' : '📌 Pin Site'}
        </button>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="flex-1 py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-xl text-sm font-semibold transition-all disabled:opacity-50"
        >
          {exporting ? '...' : '📥 Export JSON'}
        </button>
      </div>
    </div>
  )
}