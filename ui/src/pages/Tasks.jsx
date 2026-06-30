import { useState, useEffect } from 'react'
import { CheckSquare, Calendar, ShieldAlert, Check } from 'lucide-react'
import { api } from '../api'

export default function Tasks() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // all, todo, done
  const [actionLoading, setActionLoading] = useState(null)

  useEffect(() => {
    fetchTasks()
  }, [])

  const fetchTasks = () => {
    setLoading(true)
    api.getTasks()
      .then(setTasks)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  const handleToggle = async (taskId, currentStatus) => {
    const nextStatus = currentStatus === 'todo' ? 'done' : 'todo'
    setActionLoading(taskId)
    try {
      await api.toggleTask(taskId, nextStatus)
      setTasks(tasks.map(t => t.id === taskId ? { ...t, status: nextStatus } : t))
    } catch (err) {
      alert(err.message)
    } finally {
      setActionLoading(null)
    }
  }

  const filteredTasks = tasks.filter(t => {
    if (filter === 'todo') return t.status === 'todo'
    if (filter === 'done') return t.status === 'done'
    return true
  })

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high':
        return 'text-red-700 bg-red-50 border-red-100'
      case 'medium':
        return 'text-amber-700 bg-amber-50 border-amber-100'
      case 'low':
        return 'text-indigo-700 bg-indigo-50 border-indigo-100'
      default:
        return 'text-slate-700 bg-slate-50 border-slate-100'
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-800">Task Manager</h1>
          <p className="text-sm text-slate-500 mt-0.5">Parsed checklist of tasks and action items from your emails.</p>
        </div>

        {/* Filters */}
        <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200/50">
          {['all', 'todo', 'done'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded-md text-xs font-semibold uppercase tracking-wider transition-all
                ${filter === f 
                  ? 'bg-white text-slate-800 shadow-sm' 
                  : 'text-slate-400 hover:text-slate-700'}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64 text-slate-400 text-sm">
          Loading tasks...
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-100 p-12 text-center shadow-sm">
          <div className="w-12 h-12 rounded-full bg-slate-50 flex items-center justify-center mx-auto mb-3">
            <CheckSquare size={20} className="text-slate-400" />
          </div>
          <h3 className="text-sm font-medium text-slate-700">No tasks found</h3>
          <p className="text-xs text-slate-400 mt-1">There are no tasks matching your selected filter.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-100 divide-y divide-slate-100 overflow-hidden shadow-sm">
          {filteredTasks.map((task) => {
            const isDone = task.status === 'done'
            const isLoading = actionLoading === task.id

            return (
              <div 
                key={task.id} 
                className={`p-5 flex items-start gap-4 transition-colors hover:bg-slate-50/50 ${isDone ? 'bg-slate-50/20' : ''}`}
              >
                {/* Checkbox */}
                <button
                  onClick={() => handleToggle(task.id, task.status)}
                  className={`w-5 h-5 rounded border flex items-center justify-center shrink-0 transition-colors mt-0.5
                    ${isDone 
                      ? 'bg-indigo-600 border-indigo-600 text-white' 
                      : 'border-slate-300 hover:border-indigo-500 bg-white'}`}
                  disabled={isLoading}
                >
                  {isDone && <Check size={12} strokeWidth={3} />}
                </button>

                {/* Task Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <h3 className={`text-sm font-semibold text-slate-800 ${isDone ? 'line-through text-slate-400' : ''}`}>
                      {task.title}
                    </h3>
                    <span className={`text-[10px] font-bold uppercase border px-2 py-0.5 rounded-full ${getPriorityColor(task.priority)}`}>
                      {task.priority}
                    </span>
                  </div>
                  {task.description && (
                    <p className={`text-xs mt-1 text-slate-500 leading-relaxed ${isDone ? 'text-slate-400/70' : ''}`}>
                      {task.description}
                    </p>
                  )}
                  
                  {/* Footer Meta */}
                  <div className="flex items-center gap-4 mt-3">
                    {task.deadline && (
                      <div className="flex items-center gap-1 text-[11px] font-medium text-slate-400">
                        <Calendar size={12} className="text-slate-400" />
                        Deadline: {new Date(task.deadline).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
