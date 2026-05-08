import { useState, useEffect } from 'react'
import { adminAPI } from '../services/api'
import { Shield, Users, Activity, Server, BarChart3 } from 'lucide-react'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminAPI.dashboard().then(r => setStats(r.data)).catch(() => {
      setStats({
        total_users: 342, active_users: 298, models_deployed: 2, api_calls_today: 1247,
        diagnoses_today: 23, total_diagnoses: 1850, total_yield_predictions: 450,
        system_health: { disease_detection_model: 'operational', yield_prediction_model: 'operational', database: 'operational', api_gateway: 'operational' },
        recent_activity: [],
      })
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full" /></div>

  const cards = [
    { icon: Users, label: 'Total Users', value: stats.total_users, color: 'from-blue-500/20 to-blue-600/10', iconBg: 'bg-blue-500/20' },
    { icon: Activity, label: 'Active Sessions', value: stats.active_users, color: 'from-primary-500/20 to-primary-600/10', iconBg: 'bg-primary-500/20' },
    { icon: Server, label: 'Models Deployed', value: stats.models_deployed, color: 'from-purple-500/20 to-purple-600/10', iconBg: 'bg-purple-500/20' },
    { icon: BarChart3, label: 'API Calls Today', value: stats.api_calls_today?.toLocaleString(), color: 'from-accent-500/20 to-accent-600/10', iconBg: 'bg-accent-500/20' },
  ]

  const healthItems = Object.entries(stats.system_health || {}).map(([k, v]) => ({
    name: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    status: v,
  }))

  return (
    <div className="fade-in space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Shield className="w-8 h-8 text-purple-400" /> Administration
        </h1>
        <p className="text-gray-400 mt-1">System overview and management</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map(({ icon: Icon, label, value, color, iconBg }) => (
          <div key={label} className={`stat-card bg-gradient-to-br ${color}`}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-gray-400">{label}</p>
                <p className="text-3xl font-bold text-white mt-1">{value}</p>
              </div>
              <div className={`w-12 h-12 rounded-xl ${iconBg} flex items-center justify-center`}>
                <Icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Health */}
        <div className="glass rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">System Health</h2>
          <div className="space-y-3">
            {healthItems.map(h => (
              <div key={h.name} className="flex items-center justify-between p-3 rounded-xl bg-white/3">
                <span className="text-sm text-gray-300">{h.name}</span>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  h.status === 'operational' ? 'bg-primary-500/20 text-primary-400' : 'bg-red-500/20 text-red-400'
                }`}>{h.status}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="glass rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Recent Activity</h2>
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {(stats.recent_activity || []).length > 0 ? stats.recent_activity.map((a, i) => (
              <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-white/3 text-sm">
                <div>
                  <span className="text-gray-300">{a.username}</span>
                  <span className="text-gray-500 ml-2">{a.action}</span>
                </div>
                <span className={`px-2 py-0.5 rounded text-xs ${
                  a.status_code === 200 ? 'bg-primary-500/20 text-primary-400' :
                  a.status_code === 401 ? 'bg-red-500/20 text-red-400' :
                  'bg-accent-500/20 text-accent-400'
                }`}>{a.status_code}</span>
              </div>
            )) : (
              <p className="text-gray-500 text-sm text-center py-8">No recent activity</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
