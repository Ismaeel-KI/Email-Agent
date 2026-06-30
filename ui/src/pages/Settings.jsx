import { useState, useEffect } from 'react'
import { api } from '../api'

function SettingRow({ label, description, children }) {
  return (
    <div className="flex items-start justify-between gap-8 py-4 border-b border-slate-100 last:border-0">
      <div>
        <p className="text-sm font-medium text-slate-800">{label}</p>
        {description && <p className="text-xs text-slate-400 mt-0.5">{description}</p>}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  )
}

export default function Settings() {
  const [settings, setSettings] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [form, setForm] = useState({})

  useEffect(() => {
    api.getSettings().then(s => {
      setSettings(s)
      setForm({
        max_emails_per_run: s.max_emails_per_run,
        poll_interval_minutes: s.poll_interval_minutes,
        log_level: s.log_level,
      })
    })
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      const updated = await api.updateSettings(form)
      setSettings(updated)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      console.error(e)
    } finally {
      setSaving(false)
    }
  }

  if (!settings) return (
    <div className="flex items-center justify-center h-full text-slate-400 text-sm">
      Loading settings...
    </div>
  )

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-slate-800">Settings</h1>
        <p className="text-sm text-slate-500 mt-0.5">Configure how the agent runs</p>
      </div>

      {/* Agent settings */}
      <div className="bg-white rounded-xl border border-slate-100 p-5 mb-4">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">Agent</p>

        <SettingRow
          label="Max emails per run"
          description="How many emails to fetch and process in a single run"
        >
          <input
            type="number"
            min={1} max={100}
            value={form.max_emails_per_run || ''}
            onChange={e => setForm(f => ({ ...f, max_emails_per_run: Number(e.target.value) }))}
            className="w-20 text-sm text-right border border-slate-200 rounded-lg px-2 py-1
              focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </SettingRow>

        <SettingRow
          label="Poll interval"
          description="How often the scheduled task checks for new emails (minutes)"
        >
          <input
            type="number"
            min={5} max={1440}
            value={form.poll_interval_minutes || ''}
            onChange={e => setForm(f => ({ ...f, poll_interval_minutes: Number(e.target.value) }))}
            className="w-20 text-sm text-right border border-slate-200 rounded-lg px-2 py-1
              focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </SettingRow>

        <SettingRow
          label="Log level"
          description="Controls how verbose the agent logs are"
        >
          <select
            value={form.log_level || 'INFO'}
            onChange={e => setForm(f => ({ ...f, log_level: e.target.value }))}
            className="text-sm border border-slate-200 rounded-lg px-2 py-1
              focus:outline-none focus:ring-2 focus:ring-indigo-300"
          >
            {['DEBUG', 'INFO', 'WARNING', 'ERROR'].map(l => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </SettingRow>
      </div>

      {/* Read-only model info */}
      <div className="bg-white rounded-xl border border-slate-100 p-5 mb-6">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">Models</p>
        <SettingRow label="Coordinator" description="Used for final digest generation">
          <span className="text-xs font-mono text-slate-500 bg-slate-50 px-2 py-1 rounded">
            {settings.gemini_model}
          </span>
        </SettingRow>
        <SettingRow label="Worker nodes" description="Used for categorization, summarization, action detection">
          <span className="text-xs font-mono text-slate-500 bg-slate-50 px-2 py-1 rounded">
            {settings.openrouter_model}
          </span>
        </SettingRow>
      </div>

      {/* Save */}
      <button
        onClick={handleSave}
        disabled={saving}
        className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60
          text-white text-sm font-medium rounded-lg transition-colors"
      >
        {saving ? 'Saving...' : saved ? '✓ Saved' : 'Save changes'}
      </button>
    </div>
  )
}