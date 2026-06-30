import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { api } from '../api'
import CategoryBadge from '../components/CategoryBadge'
import ActionFlag from '../components/ActionFlag'

function Field({ label, value }) {
    if (!value) return null
    return (
        <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">{label}</p>
            <p className="text-sm text-slate-700">{value}</p>
        </div>
    )
}

function renderBody(text) {
    if (!text) return <p className="text-sm text-slate-400">No content available.</p>

    const urlRegex = /(https?:\/\/[^\s]+)/g
    return text.split('\n').map((line, i) => {
        const parts = line.split(urlRegex)
        return (
            <p key={i} className="text-sm text-slate-700 leading-relaxed min-h-[1.25rem]">
                {parts.map((part, j) =>
                    urlRegex.test(part) ? (
                        <a
                            key={j}
                            href={part}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-indigo-600 hover:text-indigo-800 hover:underline break-all"
                        >
                            {part.length > 60 ? 'View link →' : part}
                        </a>
                    ) : part
                )}
            </p>
        )
    })
}

export default function Detail() {
    const { id } = useParams()
    const navigate = useNavigate()
    const [email, setEmail] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.getEmail(id)
            .then(setEmail)
            .catch(console.error)
            .finally(() => setLoading(false))
    }, [id])

    if (loading) return (
        <div className="flex items-center justify-center h-full text-slate-400 text-sm">
            Loading...
        </div>
    )

    if (!email) return (
        <div className="flex items-center justify-center h-full text-slate-400 text-sm">
            Email not found.
        </div>
    )

    return (
        <div className="p-8 max-w-3xl mx-auto">
            {/* Back */}
            <button
                onClick={() => navigate(-1)}
                className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 mb-6 transition-colors"
            >
                <ArrowLeft size={14} /> Back to digest
            </button>

            {/* Header */}
            <div className="bg-white rounded-xl border border-slate-100 p-6 mb-4">
                <div className="flex items-start justify-between gap-4 mb-4">
                    <h1 className="text-lg font-semibold text-slate-800 leading-tight">
                        {email.subject}
                    </h1>
                    <CategoryBadge category={email.category} />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <Field label="From" value={email.sender} />
                    <Field label="Date" value={email.date} />
                </div>
            </div>

            {/* AI Summary */}
            {email.summary && (
                <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-5 mb-4">
                    <p className="text-xs font-medium text-indigo-400 uppercase tracking-wide mb-1.5">
                        AI Summary
                    </p>
                    <p className="text-sm text-indigo-900 leading-relaxed">{email.summary}</p>
                    {email.reasoning && (
                        <p className="text-xs text-indigo-400 mt-2 italic">{email.reasoning}</p>
                    )}
                </div>
            )}

            {/* Action */}
            {email.requires_action && (
                <div className="bg-orange-50 border border-orange-100 rounded-xl p-5 mb-4">
                    <p className="text-xs font-medium text-orange-400 uppercase tracking-wide mb-1.5">
                        Action Required
                    </p>
                    <div className="flex items-center gap-2 mb-1">
                        <ActionFlag actionType={email.action_type} deadline={email.deadline} />
                    </div>
                    {email.action_detail && (
                        <p className="text-sm text-orange-800 mt-1">{email.action_detail}</p>
                    )}
                </div>
            )}

            {/* Body */}
            <div className="bg-white rounded-xl border border-slate-100 p-6">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-3">
                    Email Body
                </p>
                <div className="space-y-1">
                    {renderBody(email.body || email.snippet)}
                </div>
            </div>

            {/* Meta */}
            {email.confidence && (
                <p className="text-xs text-slate-400 text-center mt-4">
                    Categorized with {Math.round(email.confidence * 100)}% confidence
                </p>
            )}
        </div>
    )
}