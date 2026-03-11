const STATUS = {
  pending:    { label: 'Pending',    cls: 'bg-yellow-900/50 text-yellow-300 border border-yellow-800' },
  processing: { label: 'Processing', cls: 'bg-blue-900/50 text-blue-300 border border-blue-800 animate-pulse' },
  done:       { label: 'Done',       cls: 'bg-green-900/50 text-green-300 border border-green-800' },
  error:      { label: 'Error',      cls: 'bg-red-900/50 text-red-300 border border-red-800' },
  uploading:  { label: 'Uploading',  cls: 'bg-indigo-900/50 text-indigo-300 border border-indigo-800 animate-pulse' },
}

export default function StatusBadge({ status }) {
  const cfg = STATUS[status] || { label: status, cls: 'bg-gray-800 text-gray-400' }
  return (
    <span className={`badge text-xs px-2.5 py-1 rounded-full font-medium ${cfg.cls}`}>
      {cfg.label}
    </span>
  )
}
