export default function ProgressBar({ value = 0, label, color = 'brand' }) {
  const colorMap = {
    brand:  'bg-brand-500',
    green:  'bg-green-500',
    yellow: 'bg-yellow-500',
    red:    'bg-red-500',
  }
  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-1">
          <span className="text-xs text-gray-400">{label}</span>
          <span className="text-xs text-gray-400">{value}%</span>
        </div>
      )}
      <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
        <div
          className={`${colorMap[color] || colorMap.brand} h-2 rounded-full transition-all duration-300`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}
