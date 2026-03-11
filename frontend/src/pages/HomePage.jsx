import { useState, useEffect } from 'react'
import DropZone from '../components/DropZone'
import ProgressBar from '../components/ProgressBar'
import StatusBadge from '../components/StatusBadge'
import { useFileUpload } from '../hooks/useFileUpload'
import { filesApi } from '../services/api'

const DEFAULT_OPERATIONS = {
  copy:         'Copy (no conversion)',
  'compress-img': 'Compress Image',
  'img-to-pdf': 'Image → PDF',
  'pdf-to-txt': 'PDF → Text',
  zip:          'Zip File',
}

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export default function HomePage() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [operation, setOperation]       = useState('copy')
  const [operations, setOperations]     = useState(DEFAULT_OPERATIONS)

  const { upload, reset, status, uploadProgress, record, error } = useFileUpload()

  // Fetch supported operations from backend
  useEffect(() => {
    filesApi.operations()
      .then(({ data }) => {
        if (data?.operations) setOperations(data.operations)
      })
      .catch(() => {/* use defaults */})
  }, [])

  const handleFile = (file) => {
    setSelectedFile(file)
    reset()
  }

  const handleUpload = () => {
    if (!selectedFile) return
    upload(selectedFile, operation)
  }

  const handleReset = () => {
    setSelectedFile(null)
    reset()
  }

  const isIdle       = status === 'idle'
  const isUploading  = status === 'uploading'
  const isProcessing = status === 'processing'
  const isDone       = status === 'done'
  const isError      = status === 'error'
  const isBusy       = isUploading || isProcessing

  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      {/* Hero */}
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold text-white mb-3">
          Convert & Process Files
        </h1>
        <p className="text-gray-400 text-lg">
          Upload your file, choose an operation, and download the result in seconds.
        </p>
      </div>

      <div className="card space-y-6">
        {/* Drop zone */}
        <DropZone onFile={handleFile} disabled={isBusy} />

        {/* Selected file info */}
        {selectedFile && (
          <div className="flex items-center justify-between bg-gray-800 rounded-xl px-4 py-3 text-sm">
            <div className="flex items-center gap-3 min-w-0">
              <svg className="w-5 h-5 text-brand-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="text-gray-200 font-medium truncate">{selectedFile.name}</span>
            </div>
            <span className="text-gray-500 shrink-0 ml-3">{formatBytes(selectedFile.size)}</span>
          </div>
        )}

        {/* Operation selector */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">
            Processing Operation
          </label>
          <select
            value={operation}
            onChange={(e) => setOperation(e.target.value)}
            disabled={isBusy}
            className="w-full bg-gray-800 border border-gray-700 text-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:opacity-50"
          >
            {Object.entries(operations).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
        </div>

        {/* Upload progress */}
        {isUploading && (
          <ProgressBar value={uploadProgress} label="Uploading…" />
        )}

        {/* Processing indicator */}
        {isProcessing && (
          <div className="flex items-center gap-3 text-sm text-blue-400">
            <svg className="w-5 h-5 animate-spin-slow" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Processing your file… this may take a moment.
          </div>
        )}

        {/* Done state */}
        {isDone && record && (
          <div className="bg-green-950/40 border border-green-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center gap-2 text-green-400 font-semibold">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              File processed successfully!
            </div>
            <a
              href={filesApi.downloadUrl(record.id)}
              download
              className="btn-primary text-sm"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download Result
            </a>
          </div>
        )}

        {/* Error state */}
        {isError && (
          <div className="bg-red-950/40 border border-red-800 rounded-xl p-4">
            <p className="text-red-400 text-sm font-medium">
              ⚠ {error || 'Something went wrong. Please try again.'}
            </p>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isBusy}
            className="btn-primary flex-1 justify-center"
          >
            {isBusy ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {isUploading ? 'Uploading…' : 'Processing…'}
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Upload & Process
              </>
            )}
          </button>
          {(selectedFile || isDone || isError) && (
            <button onClick={handleReset} className="btn-secondary">
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Feature highlights */}
      <div className="grid grid-cols-3 gap-4 mt-8">
        {[
          { icon: '⚡', title: 'Fast', desc: 'Background queue processing' },
          { icon: '🔒', title: 'Secure', desc: 'Files auto-deleted after 1 hour' },
          { icon: '📦', title: 'Flexible', desc: 'Images, PDFs, archives & more' },
        ].map((f) => (
          <div key={f.title} className="card text-center py-4 px-3">
            <div className="text-2xl mb-2">{f.icon}</div>
            <p className="text-white font-semibold text-sm">{f.title}</p>
            <p className="text-gray-500 text-xs mt-1">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
