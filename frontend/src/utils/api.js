import axios from 'axios'

const BASE_URL = '/api'

// Axios instance with defaults
const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
})

export const api = {
  scoresite: (lat, lng, useCase, weights, radiusKm = 1.0) =>
    client.post('/score/site', {
      lat,
      lng,
      use_case: useCase,
      weights,
      radius_km: radiusKm,
    }),

  compareSites: (sites) =>
    client.post('/score/compare', sites),

  getLayer: (layerName) =>
    client.get(`/layers/${layerName}`),

  listLayers: () =>
    client.get('/layers/'),

  getHotspots: (bbox, useCase, h3Resolution = 8) =>
    client.get('/analysis/hotspots', {
      params: {
        min_lng: bbox[0],
        min_lat: bbox[1],
        max_lng: bbox[2],
        max_lat: bbox[3],
        use_case: useCase,
        h3_resolution: h3Resolution,
      },
    }),

  getIsochrone: (lat, lng, mode = 'drive', minutes = '10,20,30') =>
    client.get('/isochrone/', { params: { lat, lng, mode, minutes } }),

  exportJson: (scoreRequest) =>
    client.post('/export/json', scoreRequest, { responseType: 'blob' }),

  exportCsv: (scoreRequests) =>
    client.post('/export/csv', scoreRequests, { responseType: 'blob' }),
}

function streamSSE(url, body, onChunk, onDone, onError, apiKey = '') {
  const headers = { 'Content-Type': 'application/json' }
  if (apiKey) headers['x-gemini-key'] = apiKey

  fetch(url, { method: 'POST', headers, body: JSON.stringify(body) })
    .then(async (res) => {
      if (!res.ok) { onError(new Error(`HTTP ${res.status}`)); return }
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (raw === '[DONE]') { onDone(); return }
          try {
            const parsed = JSON.parse(raw)
            if (parsed.error) { onError(new Error(parsed.error)); return }
            if (parsed.text) onChunk(parsed.text)
          } catch (_) {}
        }
      }
      onDone()
    })
    .catch(onError)
}

export const aiApi = {
  analyzeSite: (site, useCase, apiKey, onChunk, onDone, onError) =>
    streamSSE('/api/ai/analyze', { site, use_case: useCase }, onChunk, onDone, onError, apiKey),
  compareSites: (sites, useCase, apiKey, onChunk, onDone, onError) =>
    streamSSE('/api/ai/compare', { sites, use_case: useCase }, onChunk, onDone, onError, apiKey),
  querySite: (question, site, useCase, apiKey, onChunk, onDone, onError) =>
    streamSSE('/api/ai/query', { question, site, use_case: useCase }, onChunk, onDone, onError, apiKey),
}
