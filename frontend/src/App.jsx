import React, { useState, useCallback } from 'react'
import Map from './components/Map'
import LayerPanel from './components/LayerPanel'
import ScorePanel from './components/ScorePanel'
import SiteComparison from './components/SiteComparison'
import HotspotLegend from './components/HotspotLegend'
import { api } from './utils/api'

const USE_CASES = [
  { id: 'retail', label: 'Retail Store', icon: '🏪' },
  { id: 'warehouse', label: 'Warehouse', icon: '🏭' },
  { id: 'ev_charging', label: 'EV Charging', icon: '⚡' },
  { id: 'telecom', label: 'Telecom Tower', icon: '📡' },
  { id: 'renewable', label: 'Renewable Energy', icon: '☀️' },
]

const USE_CASE_WEIGHTS = {
  retail:     { demographic: 0.35, transportation: 0.20, poi: 0.25, land_use: 0.15, environmental: 0.05 },
  warehouse:  { demographic: 0.05, transportation: 0.45, poi: 0.05, land_use: 0.35, environmental: 0.10 },
  ev_charging:{ demographic: 0.15, transportation: 0.45, poi: 0.10, land_use: 0.20, environmental: 0.10 },
  telecom:    { demographic: 0.25, transportation: 0.15, poi: 0.05, land_use: 0.30, environmental: 0.25 },
  renewable:  { demographic: 0.05, transportation: 0.10, poi: 0.05, land_use: 0.35, environmental: 0.45 },
}

const DEFAULT_WEIGHTS = USE_CASE_WEIGHTS.retail

export default function App() {
  const [selectedUseCase, setSelectedUseCase] = useState('retail')
  const [geminiKey, setGeminiKey] = useState(() => {
    const stored = localStorage.getItem('gemini_key')
    if (stored) return stored
    const defaultKey = import.meta.env.VITE_GEMINI_API_KEY || ''
    if (defaultKey) localStorage.setItem('gemini_key', defaultKey)
    return defaultKey
  })
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS)
  const [activeLayers, setActiveLayers] = useState(['demographic', 'roads', 'poi'])
  const [selectedSite, setSelectedSite] = useState(null)
  const [pinnedSites, setPinnedSites] = useState([])
  const [isScoring, setIsScoring] = useState(false)
  const [showHotspots, setShowHotspots] = useState(false)
  const [hotspotData, setHotspotData] = useState(null)
  const [isochroneData, setIsochroneData] = useState(null)
  const [showIsochrone, setShowIsochrone] = useState(false)
  const [isochroneMode, setIsochroneMode] = useState('drive')
  const [loadingHotspots, setLoadingHotspots] = useState(false)
  const [drawnPolygon, setDrawnPolygon] = useState(null)
  const [error, setError] = useState(null)

  const handleMapClick = useCallback(
    async (lat, lng) => {
      setIsScoring(true)
      setError(null)
      try {
        const res = await api.scoresite(lat, lng, selectedUseCase, weights)
        setSelectedSite(res.data)

        if (showIsochrone) {
          try {
            const isoRes = await api.getIsochrone(lat, lng, isochroneMode)
            setIsochroneData(isoRes.data)
          } catch {
            // Non-critical: isochrone failure won't block score display
          }
        }
      } catch (err) {
        setError('Scoring failed. Is the backend running?')
        console.error('Scoring failed:', err)
      } finally {
        setIsScoring(false)
      }
    },
    [selectedUseCase, weights, showIsochrone, isochroneMode]
  )

  const handlePinSite = () => {
    if (selectedSite && pinnedSites.length < 10) {
      // Avoid duplicate pins for same location
      const alreadyPinned = pinnedSites.some(
        (s) => Math.abs(s.lat - selectedSite.lat) < 0.0001 &&
               Math.abs(s.lng - selectedSite.lng) < 0.0001
      )
      if (!alreadyPinned) {
        setPinnedSites((prev) => [...prev, selectedSite])
      }
    }
  }

  const handleRemovePinnedSite = (idx) => {
    setPinnedSites((prev) => prev.filter((_, i) => i !== idx))
  }

  const handleToggleHotspots = async () => {
    if (!showHotspots && !hotspotData) {
      setLoadingHotspots(true)
      try {
        const res = await api.getHotspots(
          [-122.5, 37.7, -122.35, 37.82],
          selectedUseCase
        )
        setHotspotData(res.data)
      } catch (err) {
        console.error('Hotspot analysis failed:', err)
        setError('Hotspot analysis failed. Ensure the backend is running.')
      } finally {
        setLoadingHotspots(false)
      }
    }
    setShowHotspots((v) => !v)
  }

  const handleIsochroneToggle = async () => {
    const next = !showIsochrone
    setShowIsochrone(next)
    if (next && selectedSite) {
      try {
        const res = await api.getIsochrone(
          selectedSite.lat,
          selectedSite.lng,
          isochroneMode
        )
        setIsochroneData(res.data)
      } catch (err) {
        console.error('Isochrone failed:', err)
      }
    }
    if (!next) {
      setIsochroneData(null)
    }
  }

  const handleUseCaseChange = (id) => {
    setSelectedUseCase(id)
    setWeights(USE_CASE_WEIGHTS[id])
    setHotspotData(null)
  }

  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0)

  return (
    <div className="flex h-screen bg-slate-900 overflow-hidden">
      {/* Left Sidebar */}
      <div className="w-80 flex-shrink-0 glass-panel border-r border-slate-700/60 flex flex-col overflow-y-auto z-10">
        {/* Logo/Header */}
        <div className="p-4 border-b border-slate-700/60">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-sm font-bold">
              G
            </div>
            <div>
              <h1 className="text-sm font-bold text-white leading-tight">GeoSite Analyzer</h1>
              <p className="text-xs text-slate-400">AI-Powered Location Intelligence</p>
            </div>
          </div>
          <div className="mt-2 text-xs text-slate-500 flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full inline-block"></span>
            San Francisco Bay Area
          </div>
        </div>

        {/* Use Case Selector */}
        <div className="p-4 border-b border-slate-700/60">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Use Case
          </h3>
          <div className="grid grid-cols-1 gap-1">
            {USE_CASES.map((uc) => (
              <button
                key={uc.id}
                onClick={() => handleUseCaseChange(uc.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all ${
                  selectedUseCase === uc.id
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/30'
                    : 'text-slate-400 hover:bg-slate-700/60 hover:text-slate-200'
                }`}
              >
                <span className="text-base">{uc.icon}</span>
                <span>{uc.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Layer Weights */}
        <div className="p-4 border-b border-slate-700/60">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Layer Weights
            </h3>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              Math.abs(totalWeight - 1.0) < 0.01
                ? 'bg-green-900/50 text-green-400'
                : 'bg-yellow-900/50 text-yellow-400'
            }`}>
              {(totalWeight * 100).toFixed(0)}%
            </span>
          </div>
          {Object.entries(weights).map(([layer, weight]) => (
            <div key={layer} className="mb-3">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 capitalize">{layer.replace('_', ' ')}</span>
                <span className="text-blue-400 font-medium">{(weight * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={weight}
                onChange={(e) =>
                  setWeights((prev) => ({ ...prev, [layer]: parseFloat(e.target.value) }))
                }
                className="w-full h-1"
              />
            </div>
          ))}
          <button
            onClick={() => setWeights(DEFAULT_WEIGHTS)}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            Reset to equal weights
          </button>
        </div>

        <LayerPanel activeLayers={activeLayers} setActiveLayers={setActiveLayers} />

        {/* Analysis Tools */}
        <div className="p-4 border-t border-slate-700/60 mt-auto">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Analysis Tools
          </h3>
          <button
            onClick={handleToggleHotspots}
            disabled={loadingHotspots}
            className={`w-full py-2 px-3 rounded-lg text-sm mb-2 transition-all font-medium ${
              showHotspots
                ? 'bg-orange-600 text-white shadow-lg shadow-orange-900/30'
                : 'bg-slate-700/60 text-slate-300 hover:bg-slate-600'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {loadingHotspots
              ? '⏳ Analyzing...'
              : showHotspots
              ? '🔥 Hide Hotspots'
              : '🔥 Show Hotspots'}
          </button>

          <div className="flex gap-2">
            <select
              value={isochroneMode}
              onChange={(e) => setIsochroneMode(e.target.value)}
              className="flex-1 bg-slate-700/60 text-slate-300 text-sm rounded-lg px-2 py-2 border border-slate-600/60"
            >
              <option value="drive">🚗 Drive</option>
              <option value="walk">🚶 Walk</option>
              <option value="transit">🚌 Transit</option>
            </select>
            <button
              onClick={handleIsochroneToggle}
              className={`flex-1 py-2 px-3 rounded-lg text-sm transition-all font-medium ${
                showIsochrone
                  ? 'bg-purple-600 text-white shadow-lg shadow-purple-900/30'
                  : 'bg-slate-700/60 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {showIsochrone ? '⏱ Hide Iso' : '⏱ Isochrone'}
            </button>
          </div>

          <div className="mt-3 text-xs text-slate-500 text-center">
            Click anywhere on the map to score a site
          </div>
        </div>
      </div>

      {/* Main Map Area */}
      <div className="flex-1 relative">
        {/* Loading overlay */}
        {isScoring && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 glass-panel px-5 py-2.5 rounded-full text-sm text-blue-300 border border-blue-500/30 shadow-xl fade-in">
            <span className="inline-block animate-spin mr-2">⏳</span>
            Analyzing site...
          </div>
        )}

        {/* Error toast */}
        {error && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 glass-panel px-5 py-2.5 rounded-full text-sm text-red-300 border border-red-500/30 shadow-xl fade-in">
            ⚠️ {error}
            <button
              onClick={() => setError(null)}
              className="ml-3 text-slate-400 hover:text-white"
            >
              ×
            </button>
          </div>
        )}

        <Map
          onMapClick={handleMapClick}
          activeLayers={activeLayers}
          selectedSite={selectedSite}
          pinnedSites={pinnedSites}
          hotspotData={showHotspots ? hotspotData : null}
          isochroneData={showIsochrone ? isochroneData : null}
          onDrawPolygon={setDrawnPolygon}
        />

        {/* Hotspot Legend */}
        {(showHotspots && hotspotData) && <HotspotLegend />}
      </div>

      {/* Right Score Panel */}
      {selectedSite && (
        <div className="w-96 flex-shrink-0 glass-panel border-l border-slate-700/60 overflow-y-auto z-10 fade-in">
          <ScorePanel
            site={selectedSite}
            onPin={handlePinSite}
            onClose={() => setSelectedSite(null)}
            isochroneData={isochroneData}
            isPinned={pinnedSites.some(
              (s) =>
                Math.abs(s.lat - selectedSite.lat) < 0.0001 &&
                Math.abs(s.lng - selectedSite.lng) < 0.0001
            )}
            useCase={selectedUseCase}
            geminiKey={geminiKey}
          />
        </div>
      )}

      {/* Bottom Comparison Bar */}
      {pinnedSites.length > 0 && (
        <div
          className="absolute bottom-0 glass-panel border-t border-slate-700/60 z-20"
          style={{ left: '320px', right: selectedSite ? '384px' : '0' }}
        >
          <SiteComparison sites={pinnedSites} onRemove={handleRemovePinnedSite} useCase={selectedUseCase} geminiKey={geminiKey} />
        </div>
      )}
    </div>
  )
}
