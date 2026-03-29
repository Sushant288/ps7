import React, { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { api } from '../utils/api'

// Fix Leaflet default icon paths (broken in Vite builds)
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl:
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const LAYER_COLORS = {
  roads: {
    highway: '#f59e0b',
    arterial: '#60a5fa',
    local: '#94a3b8',
  },
  poi: {
    retail: '#8b5cf6',
    restaurant: '#f97316',
    cafe: '#84cc16',
    grocery: '#06b6d4',
    gym: '#ec4899',
    pharmacy: '#10b981',
    competitor_retail: '#ef4444',
    competitor_restaurant: '#dc2626',
  },
  land_use: {
    commercial: '#3b82f6',
    residential: '#22c55e',
    industrial: '#f59e0b',
    mixed: '#8b5cf6',
    park: '#10b981',
    institutional: '#64748b',
  },
  environmental: {
    flood_zone: '#0ea5e9',
    low_flood: '#38bdf8',
    earthquake_high: '#ef4444',
    earthquake_medium: '#f97316',
    air_quality_poor: '#a855f7',
    air_quality_moderate: '#f59e0b',
    air_quality_good: '#22c55e',
  },
}

function scoreToColor(score) {
  if (score >= 80) return '#22c55e'
  if (score >= 65) return '#84cc16'
  if (score >= 50) return '#f59e0b'
  if (score >= 35) return '#f97316'
  return '#ef4444'
}

function createScoreMarker(score, isPrimary = true) {
  const color = scoreToColor(score)
  const size = isPrimary ? 44 : 34
  const fontSize = isPrimary ? 13 : 11
  return L.divIcon({
    html: `<div style="
      background: ${color};
      color: white;
      font-weight: 700;
      font-size: ${fontSize}px;
      width: ${size}px;
      height: ${size}px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 3px solid rgba(255,255,255,0.9);
      box-shadow: 0 4px 16px rgba(0,0,0,0.5), 0 0 0 4px ${color}33;
      font-family: system-ui, sans-serif;
    ">${Math.round(score)}</div>`,
    className: '',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  })
}

export default function Map({
  onMapClick,
  activeLayers = [],
  selectedSite,
  pinnedSites = [],
  hotspotData,
  isochroneData,
  onDrawPolygon,
}) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const layerGroupsRef = useRef({})
  const selectedMarkerRef = useRef(null)
  const pinnedMarkersRef = useRef([])
  const hotspotLayerRef = useRef(null)
  const isochroneLayerRef = useRef(null)
  const isComponentMounted = useRef(true) // Global unmount protection
  const [layerStatus, setLayerStatus] = useState({})
  const onMapClickRef = useRef(onMapClick)

  // Keep click handler ref fresh
  useEffect(() => {
    onMapClickRef.current = onMapClick
  }, [onMapClick])

  // Track global mount status for async callbacks
  useEffect(() => {
    isComponentMounted.current = true
    return () => {
      isComponentMounted.current = false
    }
  }, [])

  // Initialize map
  useEffect(() => {
    if (mapInstanceRef.current || !mapRef.current) return

    // FIX: Extremely aggressive Vite HMR cleanup
    if (mapRef.current._leaflet_id) {
      mapRef.current._leaflet_id = null
      mapRef.current.innerHTML = ''
    }

    const map = L.map(mapRef.current, {
      center: [37.765, -122.42],
      zoom: 13,
      zoomControl: false,
      attributionControl: true,
    })

    // Dark basemap
    L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19,
      }
    ).addTo(map)

    L.control.zoom({ position: 'bottomright' }).addTo(map)

    // Scale bar
    L.control.scale({ position: 'bottomleft', imperial: false }).addTo(map)

    map.on('click', (e) => {
      onMapClickRef.current(e.latlng.lat, e.latlng.lng)
    })

    mapInstanceRef.current = map

    // Draw control setup
    try {
      if (window.L && window.L.Control && window.L.Control.Draw) {
        const drawnItems = new L.FeatureGroup()
        map.addLayer(drawnItems)
        const drawControl = new window.L.Control.Draw({
          edit: { featureGroup: drawnItems },
          draw: {
            polygon: { shapeOptions: { color: '#3b82f6', fillOpacity: 0.15 } },
            rectangle: { shapeOptions: { color: '#3b82f6', fillOpacity: 0.15 } },
            circle: false,
            marker: false,
            circlemarker: false,
            polyline: false,
          },
        })
        map.addControl(drawControl)
        map.on('draw:created', (e) => {
          drawnItems.clearLayers()
          drawnItems.addLayer(e.layer)
          if (onDrawPolygon) onDrawPolygon(e.layer.toGeoJSON())
        })
      }
    } catch (_) {
      // Draw control not available
    }

    return () => {
      map.remove()
      mapInstanceRef.current = null
      
      // Wipe DOM container completely to ensure safe remounting
      if (mapRef.current) {
        mapRef.current._leaflet_id = null
        mapRef.current.innerHTML = ''
      }

      layerGroupsRef.current = {}
      selectedMarkerRef.current = null
      pinnedMarkersRef.current = []
      hotspotLayerRef.current = null
      isochroneLayerRef.current = null
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // FIX: Stringify activeLayers so React doesn't endlessly re-trigger if array reference changes
  const activeLayersStr = JSON.stringify(activeLayers)

  // Layer management
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return

    const currentActiveLayers = JSON.parse(activeLayersStr) || []

    // 1. Remove de-activated layers
    Object.keys(layerGroupsRef.current).forEach((name) => {
      if (!currentActiveLayers.includes(name)) {
        const currentMap = mapInstanceRef.current
        // Verify map health before removal
        if (currentMap && currentMap._panes && layerGroupsRef.current[name]) {
          currentMap.removeLayer(layerGroupsRef.current[name])
        }
        delete layerGroupsRef.current[name]
        setLayerStatus((prev) => {
          const next = { ...prev }
          delete next[name]
          return next
        })
      }
    })

    // 2. Add newly active layers
    currentActiveLayers.forEach(async (layerName) => {
      if (layerGroupsRef.current[layerName]) return
      if (layerStatus[layerName] === 'loading') return

      setLayerStatus((prev) => ({ ...prev, [layerName]: 'loading' }))

      try {
        const res = await api.getLayer(layerName)
        
        // --- THE DEEP HEALTH CHECK ---
        const currentMap = mapInstanceRef.current
        
        // Abort if component unmounted
        if (!isComponentMounted.current) return
        
        // Abort if map was destroyed (Leaflet strips _panes on .remove())
        if (!currentMap || !currentMap._panes || !currentMap._panes.overlayPane) {
           return 
        }

        // Abort if layer was deselected while we were fetching
        const latestActiveLayers = JSON.parse(activeLayersStr)
        if (!latestActiveLayers.includes(layerName)) return

        const geojson = res.data
        const group = L.layerGroup()

        L.geoJSON(geojson, {
          style: (feature) => {
            if (layerName === 'demographic') {
              const density = feature.properties.population_density || 0
              const t = Math.min(1, density / 15000)
              const r = Math.round(239 * (1 - t) + 34 * t)
              const g = Math.round(68 * (1 - t) + 197 * t)
              const b = Math.round(68 * (1 - t) + 94 * t)
              return { fillColor: `rgb(${r},${g},${b})`, weight: 0.5, opacity: 0.5, color: '#0f172a', fillOpacity: 0.38 }
            }
            if (layerName === 'land_use') {
              const zone = feature.properties.zone_type
              return { fillColor: LAYER_COLORS.land_use[zone] || '#64748b', weight: 0.5, opacity: 0.4, color: '#0f172a', fillOpacity: 0.32 }
            }
            if (layerName === 'environmental') {
              const riskType = feature.properties.risk_type
              const c = LAYER_COLORS.environmental[riskType] || '#64748b'
              return { fillColor: c, weight: 1, opacity: 0.7, color: c, fillOpacity: 0.30, dashArray: riskType.includes('flood') ? '4,3' : null }
            }
            if (layerName === 'roads') {
              const roadType = feature.properties.road_type
              return { color: LAYER_COLORS.roads[roadType] || '#94a3b8', weight: roadType === 'highway' ? 3 : roadType === 'arterial' ? 1.5 : 0.8, opacity: roadType === 'highway' ? 0.9 : 0.7 }
            }
            return { color: '#3b82f6', weight: 1, fillOpacity: 0.25, fillColor: '#3b82f6' }
          },

          pointToLayer: (feature, latlng) => {
            if (layerName === 'poi') {
              const cat = feature.properties.category
              return L.circleMarker(latlng, { radius: 5, fillColor: LAYER_COLORS.poi[cat] || '#94a3b8', color: '#0f172a', weight: 1, fillOpacity: 0.85 })
            }
            if (layerName === 'competitor_locations') {
              return L.circleMarker(latlng, { radius: 6, fillColor: '#ef4444', color: '#7f1d1d', weight: 1.5, fillOpacity: 0.9 })
            }
            return L.circleMarker(latlng, { radius: 5, fillColor: '#60a5fa', fillOpacity: 0.8, color: '#1e40af', weight: 1 })
          },

          onEachFeature: (feature, layer) => {
            const props = feature.properties
            const entries = Object.entries(props).slice(0, 6)
            const rows = entries.map(([k, v]) => `<tr><td style="color:#94a3b8;padding-right:8px;">${k.replace(/_/g, ' ')}</td><td style="color:#e2e8f0;font-weight:500;">${typeof v === 'number' ? v.toLocaleString() : String(v)}</td></tr>`).join('')
            layer.bindTooltip(`<table style="font-size:11px;font-family:system-ui;">${rows}</table>`, { className: 'custom-tooltip', sticky: true })
          },
        }).addTo(group)

        group.addTo(currentMap) 
        layerGroupsRef.current[layerName] = group
        setLayerStatus((prev) => ({ ...prev, [layerName]: 'loaded' }))
      } catch (err) {
        if (!isComponentMounted.current) return
        console.error(`Failed to load layer ${layerName}:`, err)
        setLayerStatus((prev) => ({ ...prev, [layerName]: 'error' }))
      }
    })
  }, [activeLayersStr]) // FIX: Stable string dependency prevents rapid teardowns

  // Selected site marker
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map || !map._panes) return

    if (selectedMarkerRef.current) {
      map.removeLayer(selectedMarkerRef.current)
      selectedMarkerRef.current = null
    }

    if (!selectedSite) return

    const { lat, lng, composite_score, grade } = selectedSite
    const color = scoreToColor(composite_score)

    const marker = L.marker([lat, lng], {
      icon: createScoreMarker(composite_score, true),
      zIndexOffset: 1000,
    })

    marker.bindPopup(
      `<div style="font-family:system-ui;min-width:180px;">
        <div style="font-size:22px;font-weight:800;color:${color}">${composite_score}/100</div>
        <div style="color:#94a3b8;font-size:13px;margin-top:2px;">Grade: <strong style="color:${color}">${grade}</strong></div>
        <hr style="border-color:#334155;margin:8px 0;">
        <div style="font-size:11px;color:#64748b;">${lat.toFixed(5)}, ${lng.toFixed(5)}</div>
      </div>`,
      { className: 'custom-popup', offset: [0, -20] }
    )

    marker.addTo(map)
    marker.openPopup()
    selectedMarkerRef.current = marker
  }, [selectedSite])

  // Pinned site markers
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map || !map._panes) return

    pinnedMarkersRef.current.forEach((m) => map.removeLayer(m))
    pinnedMarkersRef.current = []

    pinnedSites.forEach((site, idx) => {
      const color = scoreToColor(site.composite_score)
      const marker = L.marker([site.lat, site.lng], {
        icon: L.divIcon({
          html: `<div style="background:#1e293b;color:${color};font-size:10px;font-weight:700;width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2px solid ${color};box-shadow:0 2px 8px rgba(0,0,0,0.5);font-family:system-ui;">#${idx + 1}</div>`,
          className: '', iconSize: [30, 30], iconAnchor: [15, 15],
        }),
        zIndexOffset: 500,
      })
      marker.bindTooltip(`Site #${idx + 1} — Score: ${site.composite_score}/100 (${site.grade})`)
      marker.addTo(map)
      pinnedMarkersRef.current.push(marker)
    })
  }, [pinnedSites])

  // Hotspot H3 hexagon layer
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map || !map._panes) return

    if (hotspotLayerRef.current) {
      map.removeLayer(hotspotLayerRef.current)
      hotspotLayerRef.current = null
    }

    if (!hotspotData?.h3_cells?.length) return

    const group = L.layerGroup()

    hotspotData.h3_cells.forEach((cell) => {
      const color = scoreToColor(cell.score)
      const opacity = 0.25 + (cell.score / 100) * 0.55
      const lat = cell.centroid_lat
      const lng = cell.centroid_lng
      const r = 0.0028
      const hexPoints = Array.from({ length: 6 }, (_, i) => {
        const angle = ((i * 60 - 30) * Math.PI) / 180
        return [lat + r * Math.cos(angle), lng + r * 1.4 * Math.sin(angle)]
      })

      L.polygon(hexPoints, { fillColor: color, fillOpacity: opacity, color: color, weight: 0.8, opacity: 0.6 })
        .bindTooltip(`Score: <strong>${cell.score.toFixed(1)}</strong> | Cluster: ${cell.cluster_id >= 0 ? `#${cell.cluster_id}` : 'isolated'}`, { className: 'custom-tooltip' })
        .addTo(group)
    })

    group.addTo(map)
    hotspotLayerRef.current = group
  }, [hotspotData])

  // Isochrone layer
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map || !map._panes) return

    if (isochroneLayerRef.current) {
      map.removeLayer(isochroneLayerRef.current)
      isochroneLayerRef.current = null
    }

    if (!isochroneData?.isochrones?.length) return

    const group = L.layerGroup()
    const COLORS = ['#8b5cf6', '#3b82f6', '#06b6d4']

    ;[...isochroneData.isochrones].reverse().forEach((iso, idx) => {
      if (!iso.geojson_geometry) return
      const colorIdx = isochroneData.isochrones.length - 1 - idx
      const color = COLORS[colorIdx] || '#94a3b8'

      L.geoJSON(
        { type: 'Feature', geometry: iso.geojson_geometry },
        { style: { fillColor: color, fillOpacity: 0.12, color: color, weight: 2, opacity: 0.8, dashArray: '6,4' } }
      )
        .bindTooltip(`<strong>${iso.minutes} min ${iso.mode}</strong><br>Population: ~${iso.population_within.toLocaleString()}<br>Area: ${iso.area_sqkm.toFixed(1)} km²`, { className: 'custom-tooltip', sticky: true })
        .addTo(group)
    })

    group.addTo(map)
    isochroneLayerRef.current = group
  }, [isochroneData])

  return <div ref={mapRef} className="map-container" style={{ width: '100%', height: '100%' }} />
}