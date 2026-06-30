import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Inbox, BarChart2, Settings, Zap, FileText, CheckSquare, Calendar as CalendarIcon } from 'lucide-react'
import Digest from './pages/Digest'
import Detail from './pages/Detail'
import Stats from './pages/Stats'
import SettingsPage from './pages/Settings'
import Drafts from './pages/Drafts'
import Tasks from './pages/Tasks'
import Calendar from './pages/Calendar'
import RunButton from './components/RunButton'

function Layout({ children }) {
  const navItem = (to, Icon, label) => (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors
        ${isActive
          ? 'bg-indigo-50 text-indigo-700'
          : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'}`
      }
    >
      <Icon size={16} />
      {label}
    </NavLink>
  )

  return (
    <div className="flex h-screen bg-slate-50 font-sans">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r border-slate-200 bg-white flex flex-col">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center">
              <Zap size={14} className="text-white" />
            </div>
            <span className="font-semibold text-slate-800 text-sm">Email Agent</span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 flex flex-col gap-1">
          {navItem('/', Inbox, 'Digest')}
          {navItem('/drafts', FileText, 'Drafts')}
          {navItem('/tasks', CheckSquare, 'Tasks')}
          {navItem('/calendar', CalendarIcon, 'Calendar')}
          {navItem('/stats', BarChart2, 'Stats')}
          {navItem('/settings', Settings, 'Settings')}
        </nav>

        {/* Run button */}
        <div className="px-3 py-4 border-t border-slate-100">
          <RunButton />
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Digest />} />
          <Route path="/email/:id" element={<Detail />} />
          <Route path="/drafts" element={<Drafts />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/calendar" element={<Calendar />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}