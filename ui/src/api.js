const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  // Emails
  getEmails: (category) =>
    request(`/emails/${category ? `?category=${category}` : ''}`),
  getEmail: (id) => request(`/emails/${id}`),

  // Agent
  getStatus: () => request('/agent/status'),
  runAgent: () => request('/agent/run', { method: 'POST' }),

  // Stats
  getStats: () => request('/stats/'),

  // Settings
  getSettings: () => request('/settings/'),
  updateSettings: (data) =>
    request('/settings/', { method: 'PUT', body: JSON.stringify(data) }),

  // Drafts
  getPendingDrafts: () => request('/drafts/pending'),
  sendReply: (draftId, body) =>
    request(`/drafts/${draftId}/send`, { method: 'POST', body: JSON.stringify({ body }) }),
  discardDraft: (draftId) =>
    request(`/drafts/${draftId}/discard`, { method: 'POST' }),

  // Tasks
  getTasks: (status) => request(`/tasks/${status ? `?status=${status}` : ''}`),
  toggleTask: (taskId, status) =>
    request(`/tasks/${taskId}/toggle`, { method: 'POST', body: JSON.stringify({ status }) }),

  // Calendar
  getCalendarEvents: (status) =>
    request(`/calendar/${status ? `?status=${status}` : ''}`),
  syncCalendarEvent: (eventIdDb) =>
    request(`/calendar/${eventIdDb}/sync`, { method: 'POST' }),
}