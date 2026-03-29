import React, { useState } from 'react'
import { api } from '../utils/api'

export default function ExportModal({ site, onClose }) {
  const [format, setFormat] = useState('json')
  const [exporting, setExporting] = useState(false)
  const [done, setDone] = useState(false)

  const handleExport = async () => {
    setExporting(true)
    try {
      if (format === 'json') {
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
      } else if (format === 'csv') {
        const res = await api.exportCsv([
          { lat: site.lat, lng: site.lng, use_case: 'retail', radius_km: 1.0 },
        ])
        const url = URL.createObjectURL(res.data)
        const a = document.createElement('a')
        a.href = url
        a.download = `site_${site.lat.toFixed(4)}_${site.lng.toFixed(4)}.csv`
        a.click()
        URL.revokeObjectURL(url)
      }
      setDone(true)
      setTimeout(onClose, 1500)
    } catch (err) {
      console.error('Export failed:', err)
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="glass-panel rounded-2xl p-6 w-80 shadow-2xl border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-slate-100">Export Report</h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-xl"
          >
            ×
          </button>
        </div>

        <div className="mb-4">
          <label className="text-xs text-slate-400 mb-2 block">Format</label>
          <div className="flex gap-2">
            {['json', 'csv'].map((f) => (
              <button
                key={f}
                onClick={() => setFormat(f)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all uppercase ${
                  format === f
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-4 text-xs text-slate-400 bg-slate-800/60 p-3 rounded-lg">
          <div>
            <strong className="text-slate-300">Site:</strong>{' '}
            {site.lat.toFixed(4)}, {site.lng.toFixed(4)}
          </div>
          <div>
            <strong className="text-slate-300">Score:</strong>{' '}
            {site.composite_score}/100 (Grade {site.grade})
          </div>
        </div>

        <button
          onClick={handleExport}
          disabled={exporting || done}
          className={`w-full py-2.5 rounded-xl text-sm font-semibold transition-all ${
            done
              ? 'bg-green-600 text-white'
              : exporting
              ? 'bg-slate-600 text-slate-400'
              : 'bg-blue-600 hover:bg-blue-500 text-white'
          }`}
        >
          {done ? '✓ Downloaded!' : exporting ? 'Exporting...' : `Download ${format.toUpperCase()}`}
        </button>
      </div>
    </div>
  )
}
