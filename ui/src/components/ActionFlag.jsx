const TYPES = {
    reply: { label: 'Reply needed', color: 'text-orange-600 bg-orange-50' },
    review: { label: 'Review needed', color: 'text-blue-600 bg-blue-50' },
    deadline: { label: 'Deadline', color: 'text-red-600 bg-red-50' },
    click: { label: 'Action needed', color: 'text-indigo-600 bg-indigo-50' },
}

export default function ActionFlag({ actionType, deadline }) {
    if (!actionType || actionType === 'none') return null
    const t = TYPES[actionType] || TYPES.click

    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${t.color}`}>
            ▶ {t.label}{deadline ? ` · ${deadline}` : ''}
        </span>
    )
}