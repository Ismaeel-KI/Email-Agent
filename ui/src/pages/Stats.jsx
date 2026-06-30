import { useState, useEffect } from 'react'
import {
    PieChart, Pie, Cell, BarChart, Bar,
    XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts'
import { api } from '../api'

const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#94a3b8', '#cbd5e1']

function StatCard({ label, value, sub }) {
    return (
        <div className="bg-white rounded-xl border border-slate-100 p-5">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">{label}</p>
            <p className="text-3xl font-semibold text-slate-800">{value}</p>
            {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
        </div>
    )
}

export default function Stats() {
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.getStats()
            .then(setStats)
            .catch(console.error)
            .finally(() => setLoading(false))
    }, [])

    if (loading) return (
        <div className="flex items-center justify-center h-full text-slate-400 text-sm">
            Loading stats...
        </div>
    )

    if (!stats) return null

    const lastRunDate = stats.latest_run
        ? new Date(stats.latest_run.run_at).toLocaleString()
        : 'Never'

    return (
        <div className="p-8 max-w-4xl mx-auto">
            <div className="mb-6">
                <h1 className="text-xl font-semibold text-slate-800">Stats</h1>
                <p className="text-sm text-slate-500 mt-0.5">Last run: {lastRunDate}</p>
            </div>

            {/* Stat cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <StatCard
                    label="Emails this run"
                    value={stats.total_emails}
                />
                <StatCard
                    label="Action required"
                    value={`${stats.action_rate}%`}
                    sub={`${stats.action_count} emails`}
                />
                <StatCard
                    label="Total runs"
                    value={stats.total_runs}
                />
                <StatCard
                    label="All-time emails"
                    value={stats.all_time_emails}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Category breakdown */}
                <div className="bg-white rounded-xl border border-slate-100 p-5">
                    <p className="text-sm font-medium text-slate-700 mb-4">By Category (Today)</p>
                    {stats.category_breakdown.length === 0 ? (
                        <p className="text-sm text-slate-400 text-center py-8">No data yet</p>
                    ) : (
                        <ResponsiveContainer width="100%" height={220}>
                            <PieChart>
                                <Pie
                                    data={stats.category_breakdown}
                                    dataKey="count"
                                    nameKey="category"
                                    cx="50%"
                                    cy="50%"
                                    outerRadius={80}
                                    label={({ category, percent }) =>
                                        `${category} ${(percent * 100).toFixed(0)}%`
                                    }
                                    labelLine={false}
                                >
                                    {stats.category_breakdown.map((_, i) => (
                                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip formatter={(v, n) => [v, n]} />
                            </PieChart>
                        </ResponsiveContainer>
                    )}
                </div>

                {/* Daily volume */}
                <div className="bg-white rounded-xl border border-slate-100 p-5">
                    <p className="text-sm font-medium text-slate-700 mb-4">Daily Volume (7 days)</p>
                    {stats.daily_volume.length === 0 ? (
                        <p className="text-sm text-slate-400 text-center py-8">No data yet</p>
                    ) : (
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={stats.daily_volume} barSize={24}>
                                <XAxis
                                    dataKey="day"
                                    tick={{ fontSize: 11, fill: '#94a3b8' }}
                                    tickFormatter={d => d.slice(5)}
                                    axisLine={false}
                                    tickLine={false}
                                />
                                <YAxis
                                    tick={{ fontSize: 11, fill: '#94a3b8' }}
                                    axisLine={false}
                                    tickLine={false}
                                    allowDecimals={false}
                                />
                                <Tooltip
                                    contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
                                />
                                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    )}
                </div>
            </div>

            {/* Top senders */}
            {stats.top_senders.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-100 p-5">
                    <p className="text-sm font-medium text-slate-700 mb-4">Top Senders</p>
                    <div className="space-y-2">
                        {stats.top_senders.map((s, i) => (
                            <div key={i} className="flex items-center justify-between">
                                <span className="text-sm text-slate-600 truncate max-w-xs">{s.sender}</span>
                                <div className="flex items-center gap-2">
                                    <div
                                        className="h-1.5 bg-indigo-200 rounded-full"
                                        style={{ width: `${(s.count / stats.top_senders[0].count) * 80}px` }}
                                    />
                                    <span className="text-xs text-slate-400 w-4 text-right">{s.count}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}