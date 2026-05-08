import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Leaf, Eye, EyeOff, AlertCircle } from 'lucide-react'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const user = await login(email, password)
      navigate(user.role === 'admin' ? '/admin' : '/dashboard')
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed')
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left: Hero */}
      <div className="hidden lg:flex flex-1 relative overflow-hidden items-center justify-center"
           style={{ background: 'linear-gradient(135deg, #0a2e12 0%, #14532d 30%, #166534 60%, #15803d 100%)' }}>
        <div className="absolute inset-0 opacity-10"
             style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cpath d=\'M30 0 L60 30 L30 60 L0 30Z\' fill=\'none\' stroke=\'%2322c55e\' stroke-width=\'0.5\'/%3E%3C/svg%3E")', backgroundSize: '60px 60px' }} />
        <div className="relative z-10 text-center p-12 max-w-lg">
          <div className="w-24 h-24 mx-auto mb-8 rounded-3xl gradient-primary flex items-center justify-center shadow-2xl shadow-primary-500/30 animate-float">
            <Leaf className="w-14 h-14 text-white" />
          </div>
          <h1 className="text-5xl font-extrabold text-white mb-4">CropGuard AI</h1>
          <p className="text-primary-200 text-lg leading-relaxed">AI-Powered Crop Disease Detection & Yield Prediction System</p>
          <div className="mt-10 grid grid-cols-3 gap-4">
            {[['97.2%', 'Accuracy'], ['38', 'Disease Classes'], ['0.91', 'R² Score']].map(([v, l]) => (
              <div key={l} className="glass rounded-xl p-4">
                <div className="text-2xl font-bold text-primary-400">{v}</div>
                <div className="text-xs text-primary-300/60 mt-1">{l}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right: Login Form */}
      <div className="flex-1 flex items-center justify-center p-8" style={{ background: '#0f1320' }}>
        <div className="w-full max-w-md fade-in">
          <div className="lg:hidden flex items-center gap-3 mb-10 justify-center">
            <div className="w-12 h-12 rounded-xl gradient-primary flex items-center justify-center">
              <Leaf className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">CropGuard AI</h1>
          </div>

          <h2 className="text-3xl font-bold text-white mb-2">Welcome back</h2>
          <p className="text-gray-500 mb-8">Sign in to access your dashboard</p>

          {error && (
            <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 mb-6">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-600 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-all"
                placeholder="you@example.com" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Password</label>
              <div className="relative">
                <input type={showPass ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-600 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-all pr-12"
                  placeholder="••••••••" required />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                  {showPass ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading}
              className="w-full py-3 rounded-xl gradient-primary text-white font-semibold text-lg shadow-lg shadow-primary-500/25 hover:shadow-primary-500/40 transition-all duration-300 disabled:opacity-50">
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-8 p-4 rounded-xl bg-white/3 border border-white/5">
            <p className="text-xs text-gray-500 mb-2">Demo Accounts:</p>
            <div className="space-y-1 text-xs text-gray-400">
              <p>👨‍🌾 farmer@cropguard.ai / farmer123</p>
              <p>👮 officer@cropguard.ai / officer123</p>
              <p>🔑 admin@cropguard.ai / admin123</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
