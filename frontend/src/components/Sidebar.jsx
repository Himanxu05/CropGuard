import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Home, Bug, TrendingUp, Shield, Users, FileText, LogOut, Leaf } from 'lucide-react'

const navItems = {
  farmer: [
    { to: '/dashboard', icon: Home, label: 'Dashboard' },
    { to: '/disease-detect', icon: Bug, label: 'Disease Detection' },
  ],
  officer: [
    { to: '/dashboard', icon: Home, label: 'Dashboard' },
    { to: '/disease-detect', icon: Bug, label: 'Disease Detection' },
    { to: '/yield-predict', icon: TrendingUp, label: 'Yield Prediction' },
  ],
  admin: [
    { to: '/dashboard', icon: Home, label: 'Dashboard' },
    { to: '/disease-detect', icon: Bug, label: 'Disease Detection' },
    { to: '/yield-predict', icon: TrendingUp, label: 'Yield Prediction' },
    { to: '/admin', icon: Shield, label: 'Admin Panel' },
    { to: '/admin/users', icon: Users, label: 'User Management' },
    { to: '/admin/audit-logs', icon: FileText, label: 'Audit Logs' },
  ],
}

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const items = navItems[user?.role] || navItems.farmer

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <aside className="fixed left-0 top-0 w-64 h-screen glass-strong flex flex-col z-50">
      <div className="p-6 flex items-center gap-3 border-b border-white/5">
        <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center">
          <Leaf className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold bg-gradient-to-r from-primary-400 to-primary-300 bg-clip-text text-transparent">CropGuard</h1>
          <p className="text-[10px] text-gray-500 uppercase tracking-widest">AI Platform</p>
        </div>
      </div>

      <div className="p-4 mx-4 mt-4 rounded-xl bg-primary-900/20 border border-primary-800/30">
        <p className="text-sm font-medium text-primary-300">{user?.username}</p>
        <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
      </div>

      <nav className="flex-1 p-4 space-y-1 mt-2">
        {items.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} end className={({ isActive }) =>
            `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
              isActive
                ? 'gradient-primary text-white shadow-lg shadow-primary-500/20'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`
          }>
            <Icon className="w-5 h-5" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-white/5">
        <button onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 w-full transition-all">
          <LogOut className="w-5 h-5" /> Sign Out
        </button>
      </div>
    </aside>
  )
}
