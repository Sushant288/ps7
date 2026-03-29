import React, { useState, useRef, useEffect } from 'react'
import { aiApi } from '../utils/api'

function renderMarkdown(text) {
  return text.split('\n').map((line, i) => {
    if (line.startsWith('## '))
      return <div key={i} className="text-blue-300 font-bold text-xs uppercase tracking-wider mt-4 mb-1 first:mt-0">{line.slice(3)}</div>
    if (line.startsWith('• ') || line.startsWith('- '))
      return <div key={i} className="flex gap-2 text-xs text-slate-300 leading-relaxed ml-2"><span className="text-blue-400 flex-shrink-0 mt-0.5">•</span><span dangerouslySetInnerHTML={{ __html: boldify(line.slice(2)) }} /></div>
    if (!line.trim()) return <div key={i} className="h-1" />
    return <div key={i} className="text-xs text-slate-300 leading-relaxed" dangerouslySetInnerHTML={{ __html: boldify(line) }} />
  })
}

function boldify(text) {
  return text
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="text-slate-100 font-semibold">$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="bg-slate-700 text-blue-300 px-1 rounded text-xs">$1</code>')
}

export default function AIAnalysisPanel({ site, useCase, openaiKey }) {
  const [mode, setMode] = useState(null)
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [question, setQuestion] = useState('')
  const [error, setError] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    if (bottomRef.current) bottomRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [text])

  const startAnalysis = () => {
    if (!openaiKey) { setError('Enter your OpenAI API key in the sidebar first.'); return }
    setText(''); setError(null); setMode('analysis'); setLoading(true)
    aiApi.analyzeSite(site, useCase, openaiKey,
      (chunk) => setText((prev) => prev + chunk),
      () => setLoading(false),
      (err) => { setError(err.message); setLoading(false) }
    )
  }

  const startQuery = () => {
    if (!question.trim()) return
    if (!openaiKey) { setError('Enter your OpenAI API key in the sidebar first.'); return }
    setText(''); setError(null); setMode('query'); setLoading(true)
    aiApi.querySite(question, site, useCase, openaiKey,
      (chunk) => setText((prev) => prev + chunk),
      () => setLoading(false),
      (err) => { setError(err.message); setLoading(false) }
    )
  }

  const reset = () => { setMode(null); setText(''); setError(null); setQuestion(''); setLoading(false) }

  return (
    <div className="mb-4">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
        <span className="text-purple-400">✦</span> AI Analysis
      </h3>

      {!mode && (
        <div className="space-y-2">
          <button onClick={startAnalysis}
            className="w-full py-2.5 px-3 bg-purple-700 hover:bg-purple-600 text-white rounded-xl text-xs font-semibold transition-all flex items-center justify-center gap-2 shadow-lg shadow-purple-900/30">
            <span>🧠</span><span>Deep AI Site Analysis</span>
          </button>
          <div className="flex gap-2">
            <input type="text" value={question} onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && startQuery()}
              placeholder="Ask anything about this site..."
              className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 placeholder-slate-500 focus:outline-none focus:border-purple-500" />
            <button onClick={startQuery} disabled={!question.trim()}
              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-slate-200 rounded-lg text-xs transition-all">
              Ask
            </button>
          </div>
        </div>
      )}

      {mode && (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5 text-xs text-purple-400 font-semibold">
              {loading ? <><span className="animate-pulse">◉</span><span>AI is analyzing...</span></> : <><span>✓</span><span>Analysis complete</span></>}
            </div>
            <button onClick={reset} className="text-slate-500 hover:text-slate-300 text-xs">✕ Clear</button>
          </div>
          <div className="space-y-0.5 max-h-96 overflow-y-auto pr-1">
            {text ? renderMarkdown(text) : <div className="text-xs text-slate-500 animate-pulse">Generating response...</div>}
            {error && <div className="text-xs text-red-400 mt-2 p-2 bg-red-900/20 rounded">⚠ {error}</div>}
            <div ref={bottomRef} />
          </div>
          {!loading && !error && (
            <div className="mt-3 pt-2 border-t border-slate-700/50 flex gap-2">
              <input type="text" value={question} onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && startQuery()}
                placeholder="Ask a follow-up question..."
                className="flex-1 bg-slate-700/60 border border-slate-600 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 placeholder-slate-500 focus:outline-none focus:border-purple-500" />
              <button onClick={startQuery} disabled={!question.trim()}
                className="px-2.5 py-1.5 bg-purple-700 hover:bg-purple-600 disabled:opacity-40 text-white rounded-lg text-xs transition-all">
                Ask
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
