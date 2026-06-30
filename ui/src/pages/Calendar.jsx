import { useState, useEffect } from 'react'
import { Calendar as CalendarIcon, Clock, Check, RefreshCw } from 'lucide-react'
import { api } from '../api'

export default function Calendar() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // all, pending, synced
  const [syncingId, setSyncingId] = useState(null)

  useEffect(() => {
    fetchEvents()
  }, [])

  const fetchEvents = () => {
    setLoading(true)
    api.getCalendarEvents()
      .then(setEvents)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  const handleSync = async (eventIdDb) => {
    setSyncingId(eventIdDb)
    try {
      const res = await api.syncCalendarEvent(eventIdDb)
      setEvents(events.map(e => e.id === eventIdDb ? { ...e, status: 'synced', event_id: res.event_id } : e))
    } catch (err) {
      alert(err.message)
    } finally {
      setSyncingId(null)
    }
  }

  const filteredEvents = events.filter(e => {
    if (filter === 'pending') return e.status === 'pending'
    if (filter === 'synced') return e.status === 'synced'
    return true
  })

  const formatDateTime = (isoString) => {
    if (!isoString) return ''
    try {
      const dt = new Date(isoString)
      return {
        date: dt.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }),
        time: dt.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }),
      }
    } catch (err) {
      return { date: isoString, time: '' }
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-800">Calendar Invites & Events</h1>
          <p className="text-sm text-slate-500 mt-0.5">Time-sensitive meetings, deadlines, and event invites detected from emails.</p>
        </div>

        {/* Filters */}
        <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200/50">
          {['all', 'pending', 'synced'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded-md text-xs font-semibold uppercase tracking-wider transition-all
                ${filter === f 
                  ? 'bg-white text-slate-800 shadow-sm' 
                  : 'text-slate-400 hover:text-slate-700'}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64 text-slate-400 text-sm">
          Loading events...
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-100 p-12 text-center shadow-sm">
          <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center mx-auto mb-3">
            <CalendarIcon size={20} className="text-slate-400" />
          </div>
          <h3 className="text-sm font-medium text-slate-700">No events found</h3>
          <p className="text-xs text-slate-400 mt-1">There are no calendar invites matching the selected filter.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredEvents.map((evt) => {
            const isSynced = evt.status === 'synced'
            const isSyncing = syncingId === evt.id
            const startInfo = formatDateTime(evt.start_time)
            const endInfo = evt.end_time ? formatDateTime(evt.end_time) : null

            return (
              <div 
                key={evt.id} 
                className="bg-white rounded-xl border border-slate-100 p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:border-slate-200 transition-all shadow-sm"
              >
                {/* Event Time badge/col */}
                <div className="flex items-center gap-4 flex-1">
                  <div className="bg-indigo-50 border border-indigo-100/50 rounded-lg p-3 w-16 h-16 flex flex-col items-center justify-center shrink-0 text-center">
                    <span className="text-xs font-bold text-indigo-500 uppercase tracking-wide">
                      {new Date(evt.start_time).toLocaleString(undefined, { month: 'short' })}
                    </span>
                    <span className="text-xl font-bold text-indigo-700 leading-none">
                      {new Date(evt.start_time).getDate()}
                    </span>
                  </div>

                  {/* Event Detail details */}
                  <div className="min-w-0">
                    <h3 className="text-sm font-semibold text-slate-800 leading-tight">
                      {evt.title}
                    </h3>
                    {evt.description && (
                      <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">
                        {evt.description}
                      </p>
                    )}
                    
                    <div className="flex flex-wrap items-center gap-4 mt-2">
                      <div className="flex items-center gap-1 text-[11px] font-semibold text-slate-500">
                        <Clock size={12} className="text-slate-400" />
                        {startInfo.time} {endInfo ? `- ${endInfo.time}` : ''} UTC
                      </div>
                    </div>
                  </div>
                </div>

                {/* Sync status button */}
                <div className="shrink-0 flex items-center gap-2">
                  {isSynced ? (
                    <span className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold text-green-700 bg-green-50 border border-green-100">
                      <Check size={12} strokeWidth={2.5} />
                      Synced
                    </span>
                  ) : (
                    <button
                      onClick={() => handleSync(evt.id)}
                      disabled={isSyncing}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-100 transition-colors shadow-sm"
                    >
                      {isSyncing ? (
                        <>
                          <RefreshCw size={12} className="animate-spin text-indigo-600" />
                          Syncing...
                        </>
                      ) : (
                        <>
                          <CalendarIcon size={12} />
                          Sync Calendar
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
