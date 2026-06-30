import { useState, useEffect } from 'react'
import { FileText, Send, Trash2, Edit3, ArrowRight } from 'lucide-react'
import { api } from '../api'

export default function Drafts() {
  const [drafts, setDrafts] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState(null)
  const [editedBody, setEditedBody] = useState('')
  const [actionLoading, setActionLoading] = useState(null)

  useEffect(() => {
    fetchDrafts()
  }, [])

  const fetchDrafts = () => {
    setLoading(true)
    api.getPendingDrafts()
      .then(setDrafts)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  const handleExpand = (draft) => {
    if (expandedId === draft.id) {
      setExpandedId(null)
    } else {
      setExpandedId(draft.id)
      setEditedBody(draft.body)
    }
  }

  const handleSend = async (draftId) => {
    setActionLoading(draftId)
    try {
      await api.sendReply(draftId, editedBody)
      setDrafts(drafts.filter(d => d.id !== draftId))
      setExpandedId(null)
    } catch (err) {
      alert(err.message)
    } finally {
      setActionLoading(null)
    }
  }

  const handleDiscard = async (draftId) => {
    if (!confirm('Are you sure you want to discard this draft?')) return
    setActionLoading(draftId)
    try {
      await api.discardDraft(draftId)
      setDrafts(drafts.filter(d => d.id !== draftId))
      setExpandedId(null)
    } catch (err) {
      alert(err.message)
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-slate-800">Pending Drafts</h1>
        <p className="text-sm text-slate-500 mt-0.5">Review, edit, and approve AI-generated reply suggestions.</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64 text-slate-400 text-sm">
          Loading drafts...
        </div>
      ) : drafts.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-100 p-12 text-center">
          <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center mx-auto mb-3">
            <FileText size={20} className="text-slate-400" />
          </div>
          <h3 className="text-sm font-medium text-slate-700">No pending drafts</h3>
          <p className="text-xs text-slate-400 mt-1">Runs with action required emails will generate reply drafts here.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {drafts.map((draft) => {
            const isExpanded = expandedId === draft.id
            const isLoading = actionLoading === draft.id

            return (
              <div 
                key={draft.id} 
                className="bg-white rounded-xl border border-slate-100 hover:border-slate-200 transition-all overflow-hidden shadow-sm"
              >
                {/* Header Summary */}
                <div 
                  onClick={() => handleExpand(draft)}
                  className="p-5 flex items-start justify-between cursor-pointer gap-4"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded-full">
                        Draft Reply
                      </span>
                      <span className="text-xs text-slate-400">To: {draft.recipient}</span>
                    </div>
                    <h3 className="text-sm font-semibold text-slate-800 truncate">
                      {draft.subject}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-1">
                      {draft.email_body || draft.body}
                    </p>
                  </div>
                  <div className="shrink-0 text-slate-400 hover:text-slate-600 self-center">
                    <Edit3 size={16} />
                  </div>
                </div>

                {/* Expanded Draft Editor */}
                {isExpanded && (
                  <div className="border-t border-slate-100 bg-slate-50/50 p-5 space-y-4">
                    {/* Original context */}
                    <div className="bg-white rounded-lg border border-slate-100 p-4 text-xs text-slate-500">
                      <p className="font-semibold text-slate-600 mb-1">Original Email Thread</p>
                      <p className="mb-1"><span className="font-medium text-slate-400">From:</span> {draft.email_sender}</p>
                      <p className="mb-2"><span className="font-medium text-slate-400">Subject:</span> {draft.email_subject}</p>
                      <div className="border-t border-slate-50 pt-2 whitespace-pre-wrap line-clamp-6 text-slate-600">
                        {draft.email_body}
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium px-1">
                      <ArrowRight size={12} className="text-indigo-500" />
                      Draft reply content
                    </div>

                    {/* Textarea Editor */}
                    <textarea
                      value={editedBody}
                      onChange={(e) => setEditedBody(e.target.value)}
                      rows={8}
                      className="w-full bg-white rounded-lg border border-slate-200 p-4 text-sm text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                      disabled={isLoading}
                    />

                    {/* Action buttons */}
                    <div className="flex items-center justify-end gap-3">
                      <button
                        onClick={() => handleDiscard(draft.id)}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
                        disabled={isLoading}
                      >
                        <Trash2 size={15} />
                        Discard
                      </button>
                      <button
                        onClick={() => handleSend(draft.id)}
                        className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 transition-colors shadow-sm"
                        disabled={isLoading}
                      >
                        <Send size={15} />
                        {isLoading ? 'Sending...' : 'Approve & Send'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
