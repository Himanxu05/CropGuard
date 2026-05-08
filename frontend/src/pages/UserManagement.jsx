import { useState, useEffect } from 'react'
import { adminAPI } from '../services/api'
import { Users, Search, Edit3, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'

const roleBadge = { farmer: 'bg-primary-500/20 text-primary-400', officer: 'bg-blue-500/20 text-blue-400', admin: 'bg-red-500/20 text-red-400' }

export default function UserManagement() {
  const [users, setUsers] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [loading, setLoading] = useState(true)

  const fetchUsers = () => {
    setLoading(true)
    adminAPI.users({ page, per_page: 15, search, role: roleFilter || undefined })
      .then(r => { setUsers(r.data.users); setTotal(r.data.total) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchUsers() }, [page, roleFilter])

  const handleSearch = (e) => { e.preventDefault(); setPage(1); fetchUsers() }

  const handleDelete = async (id, name) => {
    if (!confirm(`Deactivate ${name}?`)) return
    await adminAPI.deleteUser(id)
    fetchUsers()
  }

  const handleRoleChange = async (id, newRole) => {
    await adminAPI.updateUser(id, { role: newRole })
    fetchUsers()
  }

  return (
    <div className="fade-in space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Users className="w-8 h-8 text-blue-400" /> User Management
          </h1>
          <p className="text-gray-400 mt-1">{total} registered users</p>
        </div>
      </div>

      <div className="flex gap-4">
        <form onSubmit={handleSearch} className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by name or email..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-600 outline-none" />
        </form>
        <select value={roleFilter} onChange={e => { setRoleFilter(e.target.value); setPage(1) }}
          className="px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white outline-none">
          <option value="">All Roles</option>
          <option value="farmer">Farmer</option>
          <option value="officer">Officer</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              {['Name','Email','Role','Status','Last Login','Actions'].map(h => (
                <th key={h} className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/3">
            {users.map(u => (
              <tr key={u.id} className="hover:bg-white/3 transition-colors">
                <td className="px-6 py-4 text-sm font-medium text-white">{u.username}</td>
                <td className="px-6 py-4 text-sm text-gray-400">{u.email}</td>
                <td className="px-6 py-4">
                  <select value={u.role} onChange={e => handleRoleChange(u.id, e.target.value)}
                    className={`px-3 py-1 rounded-full text-xs font-medium cursor-pointer outline-none ${roleBadge[u.role]} bg-transparent border-0`}>
                    <option value="farmer">Farmer</option>
                    <option value="officer">Officer</option>
                    <option value="admin">Admin</option>
                  </select>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    u.status === 'active' ? 'bg-primary-500/20 text-primary-400' : 'bg-gray-500/20 text-gray-400'
                  }`}>{u.status}</span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {u.last_login ? new Date(u.last_login).toLocaleDateString() : 'Never'}
                </td>
                <td className="px-6 py-4">
                  <button onClick={() => handleDelete(u.id, u.username)}
                    className="p-2 rounded-lg hover:bg-red-500/10 text-red-400 transition-all">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">Showing {users.length} of {total} users</p>
        <div className="flex gap-2">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}
            className="p-2 rounded-lg glass text-gray-400 disabled:opacity-30"><ChevronLeft className="w-5 h-5" /></button>
          <span className="px-4 py-2 rounded-lg glass text-white text-sm">{page}</span>
          <button onClick={() => setPage(p => p + 1)} disabled={users.length < 15}
            className="p-2 rounded-lg glass text-gray-400 disabled:opacity-30"><ChevronRight className="w-5 h-5" /></button>
        </div>
      </div>
    </div>
  )
}
