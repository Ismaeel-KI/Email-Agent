const CONFIG = {
    important: { icon: '🔴', bg: 'bg-red-50', text: 'text-red-700', label: 'Important' },
    work: { icon: '💼', bg: 'bg-blue-50', text: 'text-blue-700', label: 'Work' },
    jobs: { icon: '🧳', bg: 'bg-cyan-50', text: 'text-cyan-700', label: 'Jobs' },
    personal: { icon: '👤', bg: 'bg-green-50', text: 'text-green-700', label: 'Personal' },
    finance: { icon: '💰', bg: 'bg-yellow-50', text: 'text-yellow-700', label: 'Finance' },
    technology: { icon: '⚙️', bg: 'bg-purple-50', text: 'text-purple-700', label: 'Technology' },
    ads: { icon: '📣', bg: 'bg-slate-100', text: 'text-slate-500', label: 'Ads' },
    other: { icon: '📋', bg: 'bg-slate-50', text: 'text-slate-600', label: 'Other' },
}

export default function CategoryBadge({ category }) {
    const c = CONFIG[category?.toLowerCase()] || CONFIG.other
    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
            {c.icon} {c.label}
        </span>
    )
}