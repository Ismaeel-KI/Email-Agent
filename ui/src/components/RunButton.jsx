import { useState } from 'react'
import { Play, Loader2 } from 'lucide-react'
import { api } from '../api'

export default function RunButton({ onComplete }) {
    const [state, setState] = useState('idle') // idle | running | done | error
    const [message, setMessage] = useState('')

    const handleRun = async () => {
        setState('running')
        setMessage('')
        try {
            const result = await api.runAgent()
            setMessage(result.email_count
                ? `${result.email_count} emails processed`
                : 'No new emails')
            setState('done')
            onComplete?.()
        } catch (e) {
            setMessage(e.message)
            setState('error')
        } finally {
            setTimeout(() => setState('idle'), 4000)
        }
    }

    return (
        <div className="space-y-1.5">
            <button
                onClick={handleRun}
                disabled={state === 'running'}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg
          bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60
          text-white text-sm font-medium transition-colors"
            >
                {state === 'running'
                    ? <><Loader2 size={14} className="animate-spin" /> Running...</>
                    : <><Play size={14} /> Run Now</>
                }
            </button>
            {message && (
                <p className={`text-xs text-center ${state === 'error' ? 'text-red-500' : 'text-slate-500'}`}>
                    {message}
                </p>
            )}
        </div>
    )
}