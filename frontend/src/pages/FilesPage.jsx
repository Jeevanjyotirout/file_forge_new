import { useState, useEffect, useCallback } from 'react'
import StatusBadge from '../components/StatusBadge'
import { filesApi } from '../services/api'

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

function formatDate(iso) {
  if (!iso) return '–'
  return new Date(iso).toLocaleString()
}

export default function FilesPage() {
  const [records, setRecords]   = useState([])
  const [total, setTotal]       = useState(0)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(null)
  const [deleting, setDeleting] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await filesApi.list(0, 100)
      setRecords(data.records || [])
      setTotal(data.total || 0)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
    const interval = setInterval(load, 5000)
    return () => clearInterval(interval)
  }, [load])

  const handleDelete = async (id) => {
    setDeleting(id)
    try {
      await filesApi.delete(id)
      setRecords((prev) => prev.filter((r) => r.id !== id))
    } catch (err) {
      alert(`Delete failed: ${err.message}`)
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">My Files</h1>
          <p className="text-gray-500 text-sm mt-0.5">{total} total records</p>
        </div>
        <button onClick={load} className="btn-secondary text-sm gap-1.5">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {loading && records.length === 0 && (
        <div className="text-center py-16 text-gray-600">
          <svg className="w-8 h-8 animate-spin mx-auto mb-3" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Loading files…
        </div>
      )}

      {error && (
        <div className="card border-red-800 bg-red-950/30 text-red-400 text-sm">
          Failed to load files: {error}
        </div>
      )}

      {!loading && records.length === 0 && !error && (
        <div className="card text-center py-16">
          <p className="text-gray-500">No files yet. Upload one from the home page!</p>
        </div>
      )}

      {records.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-900/50">
                <th className="text-left px-5 py-3 text-gray-400 font-medium">File</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium">Operation</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium">Size</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium">Status</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium">Created</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {records.map((rec, idx) => (
                <tr
                  key={rec.id}
                  className={`border-b border-gray-800/60 hover:bg-gray-800/30 transition-colors ${
                    idx === records.length - 1 ? 'border-none' : ''
                  }`}
                >
                  <td className="px-5 py-3.5 max-w-[200px]">
                    <span className="text-gray-200 truncate block" title={rec.original_name}>
                      {rec.original_name}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="text-gray-400">{rec.operation || '–'}</span>
                  </td>
                  <td className="px-4 py-3.5 text-gray-400">
                    {formatBytes(rec.size_bytes)}
                  </td>
                  <td className="px-4 py-3.5">
                    <StatusBadge status={rec.status} />
                  </td>
                  <td className="px-4 py-3.5 text-gray-500 text-xs">
                    {formatDate(rec.created_at)}
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-2 justify-end">
                      {rec.status === 'done' && (
                        <a
                          href={filesApi.downloadUrl(rec.id)}
                          download
                          className="btn-secondary text-xs py-1 px-3"
                        >
                          ↓ Download
                        </a>
                      )}
                      <button
                        onClick={() => handleDelete(rec.id)}
                        disabled={deleting === rec.id}
                        className="text-gray-600 hover:text-red-400 transition-colors disabled:opacity-40"
                        title="Delete"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
