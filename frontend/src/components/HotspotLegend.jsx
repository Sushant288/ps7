import React from 'react'

const SCORE_BANDS = [
  { color: '#22c55e', label: '80–100', sublabel: 'Excellent' },
  { color: '#84cc16', label: '65–80', sublabel: 'Good' },
  { color: '#f59e0b', label: '50–65', sublabel: 'Fair' },
  { color: '#f97316', label: '35–50', sublabel: 'Poor' },
  { color: '#ef4444', label: '0–35', sublabel: 'Critical' },
]

export default function HotspotLegend() {
  return (
    <div className="absolute bottom-8 right-4 glass-panel p-3 rounded-xl z-30 shadow-2xl pointer-events-none">
      <div className="text-xs font-semibold text-slate-300 mb-2 uppercase tracking-wider">
        Site Readiness Score
      </div>
      {SCORE_BANDS.map((item) => (
        <div key={item.label} className="flex items-center gap-2 mb-1">
          <div
            className="w-3 h-3 rounded-sm flex-shrink-0"
            style={{ backgroundColor: item.color, opacity: 0.85 }}
          />
          <span className="text-xs text-slate-400">
            {item.label}
          </span>
          <span className="text-xs text-slate-600">
            {item.sublabel}
          </span>
        </div>
      ))}
      <div className="mt-2 pt-2 border-t border-slate-700/50 text-xs text-slate-600">
        H3 hexagonal binning
      </div>
    </div>
  )
}
