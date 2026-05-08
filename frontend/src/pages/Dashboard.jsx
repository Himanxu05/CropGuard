import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { diseaseAPI } from '../services/api'
import { Bug, Upload, Clock, TrendingUp, Leaf, Zap } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [recentDiagnoses, setRecentDiagnoses] = useState([])

  useEffect(() => {
    diseaseAPI.history(1).then(r => setRecentDiagnoses(r.data.diagnoses?.slice(0, 5) || [])).catch(() => {})
  }, [])

  const StatCard = ({ icon: Icon, label, value, color, onClick }) => (
    <div onClick={onClick} className={`stat-card cursor-pointer group ${onClick ? 'hover:scale-[1.02]' : ''}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400 mb-1">{label}</p>
          <p className="text-3xl font-bold text-white">{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  )

  return (
    <div className="fade-in space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">Welcome, {user?.username} 👋</h1>
        <p className="text-gray-400 mt-1">Here's your CropGuard AI overview</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard icon={Bug} label="Disease Scans" value={recentDiagnoses.length} color="bg-red-500/20" />
        <StatCard icon={TrendingUp} label="Yield Predictions" value="—" color="bg-blue-500/20" />
        <StatCard icon={Zap} label="Model Accuracy" value="97.2%" color="bg-primary-500/20" />
        <StatCard icon={Leaf} label="Disease Classes" value="38" color="bg-accent-500/20" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Disease Scan */}
        <div className="glass rounded-2xl p-6 glow-green" onClick={() => navigate('/disease-detect')} style={{ cursor: 'pointer' }}>
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <Upload className="w-5 h-5 text-primary-400" /> Quick Disease Scan
          </h2>
          <div className="border-2 border-dashed border-primary-500/30 rounded-xl p-10 text-center hover:border-primary-500/60 transition-all">
            <Bug className="w-12 h-12 text-primary-500/50 mx-auto mb-3" />
            <p className="text-gray-400">Click to scan a leaf image</p>
            <p className="text-xs text-gray-600 mt-1">Supports JPEG, PNG up to 10MB</p>
          </div>
        </div>

        {/* Recent Diagnoses */}
        <div className="glass rounded-2xl p-6">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-accent-400" /> Recent Diagnoses
          </h2>
          {recentDiagnoses.length > 0 ? (
            <div className="space-y-3">
              {recentDiagnoses.map((d) => (
                <div key={d.id} className="flex items-center justify-between p-3 rounded-xl bg-white/3 hover:bg-white/5 transition-all">
                  <div>
                    <p className="text-sm font-medium text-white">{d.predicted_class?.replace(/_/g, ' ')}</p>
                    <p className="text-xs text-gray-500">{new Date(d.timestamp).toLocaleDateString()}</p>
                  </div>
                  <span className={`text-sm font-semibold ${d.confidence > 0.9 ? 'text-primary-400' : d.confidence > 0.7 ? 'text-accent-400' : 'text-red-400'}`}>
                    {(d.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Leaf className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p>No diagnoses yet. Upload a leaf image to get started!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
