import { useState, useEffect } from 'react'
import { adminAPI } from '../services/api'
import { FileText, Filter, ChevronLeft, ChevronRight } from 'lucide-react'

const statusColor = {
  200: 'bg-primary-500/20 text-primary-400', 201: 'bg-primary-500/20 text-primary-400',
  400: 'bg-accent-500/20 text-accent-400', 401: 'bg-red-500/20 text-red-400',
  403: 'bg-red-500/20 text-red-400', 500: 'bg-red-500/20 text-red-400',
}

export default function AuditLogs() {
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [actionFilter, setActionFilter] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    adminAPI.auditLogs({ page, per_page: 30, action: actionFilter || undefined })
      .then(r => { setLogs(r.data.logs); setTotal(r.data.total) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [page, actionFilter])

  return (
    <div className="fade-in space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <FileText className="w-8 h-8 text-accent-400" /> Audit Logs
        </h1>
        <p className="text-gray-400 mt-1">{total} total log entries</p>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
          <input value={actionFilter} onChange={e => { setActionFilter(e.target.value); setPage(1) }}
            placeholder="Filter by action..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-600 outline-none" />
        </div>
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                {['Timestamp','User','Action','Endpoint','Method','Status','IP Address'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/3">
              {logs.map((l, i) => (
                <tr key={i} className="hover:bg-white/3 transition-colors text-sm">
                  <td className="px-4 py-3 text-gray-400 whitespace-nowrap">
                    {l.timestamp ? new Date(l.timestamp).toLocaleString() : '—'}
                  </td>
                  <td className="px-4 py-3 text-white">{l.username || '—'}</td>
                  <td className="px-4 py-3 text-gray-300">{l.action}</td>
                  <td className="px-4 py-3 text-gray-500 font-mono text-xs">{l.endpoint}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-mono ${
                      l.method === 'GET' ? 'text-blue-400' : l.method === 'POST' ? 'text-primary-400' : 'text-accent-400'
                    }`}>{l.method}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor[l.status_code] || 'bg-gray-500/20 text-gray-400'}`}>
                      {l.status_code}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 font-mono text-xs">{l.ip_address}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-12 text-center text-gray-500">No audit logs found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">Page {page} • {total} total entries</p>
        <div className="flex gap-2">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}
            className="p-2 rounded-lg glass text-gray-400 disabled:opacity-30"><ChevronLeft className="w-5 h-5" /></button>
          <button onClick={() => setPage(p => p + 1)} disabled={logs.length < 30}
            className="p-2 rounded-lg glass text-gray-400 disabled:opacity-30"><ChevronRight className="w-5 h-5" /></button>
        </div>
      </div>
    </div>
  )
}
