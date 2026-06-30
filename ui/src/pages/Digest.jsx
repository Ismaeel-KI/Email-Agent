import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { RefreshCw } from 'lucide-react'
import { api } from '../api'
import CategoryBadge from '../components/CategoryBadge'
import ActionFlag from '../components/ActionFlag'

const CATEGORY_ORDER = ['important', 'work', 'jobs', 'personal', 'finance', 'technology', 'other', 'ads']

function groupByCategory(emails) {
    const groups = {}
    for (const email of emails) {
        const cat = email.category || 'other'
        if (!groups[cat]) groups[cat] = []
        groups[cat].push(email)
    }
    return Object.entries(groups).sort(
        ([a], [b]) => CATEGORY_ORDER.indexOf(a) - CATEGORY_ORDER.indexOf(b)
    )
}

export default function Digest() {
    const [emails, setEmails] = useState([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState('all')
    const navigate = useNavigate()

    const load = async () => {
        setLoading(true)
        try {
            const data = await api.getEmails(filter === 'all' ? null : filter)
            setEmails(data)
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load() }, [filter])

    const groups = groupByCategory(emails)
    const categories = ['all', ...new Set(emails.map(e => e.category).filter(Boolean))]

    return (
        <div className="p-8 max-w-4xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-xl font-semibold text-slate-800">Inbox Digest</h1>
                    <p className="text-sm text-slate-500 mt-0.5">
                        {emails.length} emails from last run
                    </p>
                </div>
                <button
                    onClick={load}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600
            hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
                >
                    <RefreshCw size={14} /> Refresh
                </button>
            </div>

            {/* Category filter */}
            <div className="flex gap-2 flex-wrap mb-6">
                {categories.map(cat => (
                    <button
                        key={cat}
                        onClick={() => setFilter(cat)}
                        className={`px-3 py-1 rounded-full text-xs font-medium capitalize transition-colors
              ${filter === cat
                                ? 'bg-indigo-600 text-white'
                                : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300'}`}
                    >
                        {cat}
                    </button>
                ))}
            </div>

            {/* Email groups */}
            {loading ? (
                <div className="flex items-center justify-center h-48 text-slate-400 text-sm">
                    Loading emails...
                </div>
            ) : emails.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-48 text-center">
                    <p className="text-slate-400 text-sm">No emails found.</p>
                    <p className="text-slate-400 text-xs mt-1">Run the agent to fetch new emails.</p>
                </div>
            ) : (
                <div className="space-y-6">
                    {groups.map(([category, groupEmails]) => (
                        <div key={category}>
                            <div className="flex items-center gap-2 mb-2">
                                <CategoryBadge category={category} />
                                <span className="text-xs text-slate-400">{groupEmails.length}</span>
                            </div>
                            <div className="space-y-1">
                                {groupEmails.map(email => (
                                    <div
                                        key={email.id}
                                        onClick={() => navigate(`/email/${email.id}`)}
                                        className="flex items-start gap-3 p-3 bg-white rounded-lg border border-slate-100
                      hover:border-indigo-200 hover:shadow-sm cursor-pointer transition-all group"
                                    >
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <span className="text-sm font-medium text-slate-800 truncate group-hover:text-indigo-700">
                                                    {email.subject}
                                                </span>
                                                {email.requires_action && (
                                                    <ActionFlag
                                                        actionType={email.action_type}
                                                        deadline={email.deadline}
                                                    />
                                                )}
                                            </div>
                                            <p className="text-xs text-slate-500 mt-0.5 truncate">
                                                {email.summary || email.snippet}
                                            </p>
                                            <p className="text-xs text-slate-400 mt-0.5">{email.sender}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}