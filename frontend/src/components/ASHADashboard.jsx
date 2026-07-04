import { useState, useEffect, useRef } from 'react'
import { supabase } from '../supabaseClient'
import { timeAgo } from '../timeAgo'
import RiskBadge from './RiskBadge'
import {
  Phone, MapPin, Check, Radio, ChevronDown, ChevronUp,
  AlertOctagon, Bell, BellOff,
} from 'lucide-react'

const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'high', label: 'High' },
  { key: 'medium', label: 'Medium' },
  { key: 'low', label: 'Low' },
]

// ---------------------------------------------------------------------------
// Alert Engine — three free, zero-asset techniques for surfacing a
// high-risk case the moment it arrives, even if the worker isn't looking
// at this tab right now:
//   1. Browser Notification (works across tabs/apps, needs permission)
//   2. A short synthesized chime (Web Audio API — no audio file needed)
//   3. Tab title flash (works everywhere, no permission needed)
// ---------------------------------------------------------------------------

function playAlertChime() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext
    const ctx = new AudioCtx()
    const playTone = (freq, startTime, duration) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.frequency.value = freq
      osc.type = 'sine'
      gain.gain.setValueAtTime(0.0001, startTime)
      gain.gain.exponentialRampToValueAtTime(0.3, startTime + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(startTime)
      osc.stop(startTime + duration)
    }
    const now = ctx.currentTime
    playTone(880, now, 0.18)
    playTone(1100, now + 0.22, 0.22)
  } catch (e) {
    console.warn('Could not play alert chime:', e)
  }
}

function notifyHighRisk(caseRow) {
  if (typeof Notification === 'undefined' || Notification.permission !== 'granted') return
  new Notification('🔴 High-risk patient case', {
    body: (caseRow.transcript || 'New high-risk case received').slice(0, 100),
    tag: caseRow.id, // prevents duplicate stacking if the same case fires twice
  })
}

export default function ASHADashboard() {
  const [cases, setCases] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [connected, setConnected] = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const [notifPermission, setNotifPermission] = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'unsupported'
  )
  const newCaseIds = useRef(new Set())
  const [, forceRerender] = useState(0) // re-render trigger for the highlight timeout

  const titleIntervalRef = useRef(null)
  const originalTitleRef = useRef(document.title)

  function startTitleFlash() {
    if (titleIntervalRef.current) return
    let toggled = false
    titleIntervalRef.current = setInterval(() => {
      document.title = toggled ? originalTitleRef.current : '🔴 New High-Risk Case!'
      toggled = !toggled
    }, 1000)
  }

  function stopTitleFlash() {
    if (titleIntervalRef.current) {
      clearInterval(titleIntervalRef.current)
      titleIntervalRef.current = null
      document.title = originalTitleRef.current
    }
  }

  useEffect(() => {
    const handleVisibility = () => {
      if (!document.hidden) stopTitleFlash()
    }
    document.addEventListener('visibilitychange', handleVisibility)
    return () => document.removeEventListener('visibilitychange', handleVisibility)
  }, [])

  async function enableAlerts() {
    if (typeof Notification === 'undefined') return
    const result = await Notification.requestPermission()
    setNotifPermission(result)
  }

  useEffect(() => {
    loadInitialCases()

    const channel = supabase
      .channel('cases-feed')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'cases' },
        (payload) => {
          newCaseIds.current.add(payload.new.id)
          setCases((prev) => [payload.new, ...prev])
          setTimeout(() => {
            newCaseIds.current.delete(payload.new.id)
            forceRerender((n) => n + 1)
          }, 4500)

          // Alert Engine — only for high-risk arrivals
          if (payload.new.risk_level === 'high') {
            playAlertChime()
            if (document.hidden) {
              notifyHighRisk(payload.new)
              startTitleFlash()
            }
          }
        }
      )
      .on(
        'postgres_changes',
        { event: 'UPDATE', schema: 'public', table: 'cases' },
        (payload) => {
          setCases((prev) => prev.map((c) => (c.id === payload.new.id ? payload.new : c)))
        }
      )
      .subscribe((status) => setConnected(status === 'SUBSCRIBED'))

    return () => supabase.removeChannel(channel)
  }, [])

  async function loadInitialCases() {
    setLoading(true)
    const { data, error } = await supabase
      .from('cases')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(100)

    if (!error) setCases(data || [])
    setLoading(false)
  }

  async function markContacted(caseId) {
    setCases((prev) => prev.map((c) => (c.id === caseId ? { ...c, asha_notified: true } : c)))
    await supabase.from('cases').update({ asha_notified: true }).eq('id', caseId)
  }

  const filtered = filter === 'all' ? cases : cases.filter((c) => c.risk_level === filter)
  const counts = {
    all: cases.length,
    high: cases.filter((c) => c.risk_level === 'high').length,
    medium: cases.filter((c) => c.risk_level === 'medium').length,
    low: cases.filter((c) => c.risk_level === 'low').length,
  }
  const urgentCount = cases.filter((c) => c.risk_level === 'high' && !c.asha_notified).length

  return (
    <div className="min-h-screen">
      <header className="px-6 pt-6 pb-4 max-w-3xl mx-auto flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-2xl text-teal-bright">ASHA Dashboard</h1>
          <p className="text-sm text-ink-soft mt-0.5">Live patient case feed</p>
        </div>
        <div className="flex items-center gap-3">
          {notifPermission === 'default' && (
            <button
              onClick={enableAlerts}
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full bg-teal-deep text-white"
            >
              <Bell className="w-3.5 h-3.5" />
              Enable Alerts
            </button>
          )}
          {notifPermission === 'granted' && (
            <span className="flex items-center gap-1.5 text-xs font-medium text-risk-low">
              <Bell className="w-3.5 h-3.5" />
              Alerts On
            </span>
          )}
          {notifPermission === 'denied' && (
            <span className="flex items-center gap-1.5 text-xs text-ink-soft/60">
              <BellOff className="w-3.5 h-3.5" />
              Alerts Blocked
            </span>
          )}
          <div className="flex items-center gap-1.5 text-xs font-medium">
            <Radio
              className={`w-3.5 h-3.5 ${connected ? 'text-risk-low' : 'text-ink-soft/40'}`}
              fill={connected ? 'currentColor' : 'none'}
            />
            <span className={connected ? 'text-risk-low' : 'text-ink-soft/60'}>
              {connected ? 'Live' : 'Connecting...'}
            </span>
          </div>
        </div>
      </header>

      {/* Persistent banner — always reflects outstanding high-risk cases,
          not just ones that arrived this session, so refreshing never loses it */}
      {urgentCount > 0 && (
        <div className="px-6 max-w-3xl mx-auto pb-3">
          <button
            onClick={() => setFilter('high')}
            className="w-full flex items-center gap-2 bg-risk-high-bg border border-risk-high/30 text-risk-high font-medium text-sm rounded-xl px-4 py-2.5 animate-fadeUp"
          >
            <AlertOctagon className="w-4 h-4 shrink-0" />
            {urgentCount} high-risk case{urgentCount > 1 ? 's' : ''} need attention — tap to view
          </button>
        </div>
      )}

      {/* Filter tabs */}
      <div className="px-6 max-w-3xl mx-auto flex gap-2 pb-4 overflow-x-auto">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`
              px-4 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors
              ${
                filter === f.key
                  ? 'bg-teal-deep text-white'
                  : 'bg-surface text-ink-soft border border-ink-soft/15'
              }
            `}
          >
            {f.label} <span className="opacity-70">({counts[f.key]})</span>
          </button>
        ))}
      </div>

      <main className="px-6 max-w-3xl mx-auto pb-12 space-y-3">
        {loading && <p className="text-center text-ink-soft py-12">Loading cases...</p>}

        {!loading && filtered.length === 0 && (
          <p className="text-center text-ink-soft py-12">No cases yet in this filter.</p>
        )}

        {filtered.map((c) => {
          const isNew = newCaseIds.current.has(c.id)
          const isExpanded = expandedId === c.id
          const flashClass = isNew
            ? c.risk_level === 'high'
              ? 'animate-flashAlert'
              : 'animate-flashTeal'
            : ''

          return (
            <div
              key={c.id}
              className={`bg-surface rounded-2xl shadow-card p-4 animate-fadeUp ${flashClass}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3 flex-wrap">
                  <RiskBadge level={c.risk_level} label={c.risk_level.toUpperCase()} />
                  <span className="text-xs text-ink-soft">{timeAgo(c.created_at)}</span>
                  {c.district && (
                    <span className="flex items-center gap-1 text-xs text-ink-soft">
                      <MapPin className="w-3 h-3" />
                      {c.district}
                    </span>
                  )}
                </div>

                {c.asha_notified ? (
                  <span className="flex items-center gap-1 text-xs font-medium text-risk-low shrink-0">
                    <Check className="w-3.5 h-3.5" />
                    Contacted
                  </span>
                ) : (
                  <button
                    onClick={() => markContacted(c.id)}
                    className="shrink-0 px-3 py-1 rounded-full bg-teal-deep text-white text-xs font-medium"
                  >
                    Mark Contacted
                  </button>
                )}
              </div>

              <button
                onClick={() => setExpandedId(isExpanded ? null : c.id)}
                className="w-full text-left mt-3 flex items-start justify-between gap-2"
              >
                <p className={`text-ink text-sm ${isExpanded ? '' : 'line-clamp-2'}`}>
                  {c.transcript}
                </p>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-ink-soft shrink-0 mt-0.5" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-ink-soft shrink-0 mt-0.5" />
                )}
              </button>

              {isExpanded && (
                <div className="mt-2 pt-2 border-t border-ink-soft/10 text-sm text-ink-soft">
                  {c.advice}
                </div>
              )}

              {c.patient_phone && (
                <a
                  href={`tel:${c.patient_phone}`}
                  className="inline-flex items-center gap-1.5 mt-3 text-sm font-medium text-teal-bright"
                >
                  <Phone className="w-3.5 h-3.5" />
                  {c.patient_phone}
                </a>
              )}
            </div>
          )
        })}
      </main>
    </div>
  )
}