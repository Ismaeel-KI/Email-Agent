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
            <p className="text-sm text-slate-700 dark:text-slate-300">{value}</p>
        </div>
    )
}

function renderBody(text) {
    if (!text) return <p className="text-sm text-slate-400">No content available.</p>

    const urlRegex = /(https?:\/\/[^\s]+)/g
    const paragraphs = text
        .replace(/\r\n?/g, '\n')
        .split(/\n\s*\n/)
        .flatMap(paragraph => {
            const lines = paragraph.split('\n')
            const blocks = []
            let prose = []

            for (const line of lines) {
                if (/^\s*(?:[-*•]|\d+[.)])\s+/.test(line)) {
                    if (prose.length) blocks.push(prose.join(' ').trim())
                    prose = []
                    blocks.push(line.trim())
                } else if (line.trim()) {
                    prose.push(line.trim())
                }
            }
            if (prose.length) blocks.push(prose.join(' ').trim())
            return blocks
        })

    return paragraphs.map((paragraph, i) => {
        const parts = paragraph.split(urlRegex)
        return (
            <p key={i} className="w-full text-base text-slate-700 leading-7 min-h-[1.5rem] whitespace-pre-wrap break-words dark:text-slate-200">
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
        <div className="mx-auto w-full max-w-screen-2xl px-6 py-6 lg:px-12">
            {/* Back */}
            <button
                onClick={() => navigate(-1)}
                className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 mb-6 transition-colors"
            >
                <ArrowLeft size={14} /> Back to digest
            </button>

            {/* Header */}
            <div className="bg-white rounded-xl border border-slate-100 p-7 mb-5 dark:bg-slate-900 dark:border-slate-800">
                <div className="flex items-start justify-between gap-4 mb-4">
                    <h1 className="text-2xl font-semibold text-slate-800 leading-snug dark:text-slate-100">
                        {email.subject}
                    </h1>
                    <CategoryBadge category={email.category} />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <Field label="From" value={email.sender} />
                    <Field label="Date" value={email.date} />
                </div>
            </div>
            
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
                {/* Body */}
                <div className="min-w-0 bg-white rounded-xl border border-slate-100 p-5 lg:p-8 dark:bg-slate-900 dark:border-slate-800">
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-3">
                        Email Body
                    </p>
                    <div className="w-full max-w-none space-y-2">
                        {renderBody(email.body || email.snippet)}
                    </div>
                </div>
                <aside className="space-y-4 lg:sticky lg:top-6 self-start">
                    {/* AI Summary */}
                    {email.summary && (
                        <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-5 mb-4 dark:bg-indigo-950/70 dark:border-indigo-900">
                            <p className="text-xs font-medium text-indigo-500 uppercase tracking-wide mb-1.5 dark:text-indigo-300">
                                AI Summary
                            </p>
                            <p className="text-base text-indigo-900 leading-relaxed dark:text-indigo-100">{email.summary}</p>
                            {email.reasoning && (
                                <p className="text-xs text-indigo-500 mt-2 italic dark:text-indigo-300">{email.reasoning}</p>
                            )}
                        </div>
                    )}

                    {/* Action */}
                    {email.requires_action && (
                        <div className="bg-orange-50 border border-orange-100 rounded-xl p-5 mb-4 dark:bg-orange-950/60 dark:border-orange-900">
                            <p className="text-xs font-medium text-orange-500 uppercase tracking-wide mb-1.5 dark:text-orange-300">
                                Action Required
                            </p>
                            <div className="flex items-center gap-2 mb-1">
                                <ActionFlag actionType={email.action_type} deadline={email.deadline} />
                            </div>
                            {email.action_detail && (
                                <p className="text-sm text-orange-800 mt-1 dark:text-orange-100">{email.action_detail}</p>
                            )}
                        </div>
                    )}

                </aside>
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
