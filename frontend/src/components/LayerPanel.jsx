import React from 'react'

const LAYERS = [
  {
    id: 'demographic',
    label: 'Demographics',
    description: 'Population density & income',
    color: '#22c55e',
    icon: '👥',
  },
  {
    id: 'roads',
    label: 'Road Network',
    description: 'Highways, arterials, local',
    color: '#f59e0b',
    icon: '🛣️',
  },
  {
    id: 'poi',
    label: 'Points of Interest',
    description: 'Retail, dining, services',
    color: '#8b5cf6',
    icon: '📍',
  },
  {
    id: 'land_use',
    label: 'Land Use / Zoning',
    description: 'Commercial, residential, industrial',
    color: '#3b82f6',
    icon: '🏗️',
  },
  {
    id: 'environmental',
    label: 'Environmental Risk',
    description: 'Flood, seismic, air quality',
    color: '#ef4444',
    icon: '⚠️',
  },
  {
    id: 'competitor_locations',
    label: 'Competitors',
    description: 'Competing businesses',
    color: '#dc2626',
    icon: '🏪',
  },
]

export default function LayerPanel({ activeLayers, setActiveLayers }) {
  const toggle = (id) => {
    setActiveLayers((prev) =>
      prev.includes(id) ? prev.filter((l) => l !== id) : [...prev, id]
    )
  }

  const allActive = LAYERS.every((l) => activeLayers.includes(l.id))
  const toggleAll = () => {
    if (allActive) {
      setActiveLayers([])
    } else {
      setActiveLayers(LAYERS.map((l) => l.id))
    }
  }

  return (
    <div className="p-4 border-b border-slate-700/60">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Data Layers
        </h3>
        <button
          onClick={toggleAll}
          className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
        >
          {allActive ? 'Hide all' : 'Show all'}
        </button>
      </div>

      {LAYERS.map((layer) => {
        const isActive = activeLayers.includes(layer.id)
        return (
          <button
            key={layer.id}
            onClick={() => toggle(layer.id)}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm mb-1 transition-all text-left ${
              isActive
                ? 'bg-slate-700/70 text-white'
                : 'text-slate-500 hover:bg-slate-800/60 hover:text-slate-400'
            }`}
          >
            <div
              className="w-2.5 h-2.5 rounded-sm flex-shrink-0 transition-colors"
              style={{
                backgroundColor: isActive ? layer.color : '#374151',
              }}
            />
            <span className="text-sm">{layer.icon}</span>
            <div className="min-w-0 flex-1">
              <div className="truncate font-medium text-xs">{layer.label}</div>
            </div>
            <div
              className={`w-4 h-4 rounded border flex-shrink-0 flex items-center justify-center transition-all ${
                isActive
                  ? 'border-blue-500 bg-blue-500'
                  : 'border-slate-600'
              }`}
            >
              {isActive && (
                <svg
                  className="w-2.5 h-2.5 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={3}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              )}
            </div>
          </button>
        )
      })}
    </div>
  )
}
