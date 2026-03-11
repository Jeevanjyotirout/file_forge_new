import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

const MAX_MB = 500

export default function DropZone({ onFile, disabled }) {
  const onDrop = useCallback(
    (accepted) => {
      if (accepted.length > 0) onFile(accepted[0])
    },
    [onFile]
  )

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    multiple: false,
    disabled,
    maxSize: MAX_MB * 1024 * 1024,
  })

  const borderClass = isDragReject
    ? 'border-red-500 bg-red-950/30'
    : isDragActive
    ? 'border-brand-500 bg-brand-950/30'
    : 'border-gray-700 hover:border-brand-600 hover:bg-gray-800/40'

  return (
    <div
      {...getRootProps()}
      className={`cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-200 p-12 text-center select-none ${borderClass} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-3">
        <svg
          className={`w-14 h-14 ${isDragActive ? 'text-brand-400' : 'text-gray-600'} transition-colors`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        {isDragActive ? (
          <p className="text-brand-400 font-semibold text-lg">Drop it here!</p>
        ) : (
          <>
            <p className="text-gray-300 font-semibold text-lg">
              Drag & drop your file here
            </p>
            <p className="text-gray-500 text-sm">
              or <span className="text-brand-400 underline underline-offset-2">click to browse</span>
            </p>
            <p className="text-gray-600 text-xs mt-1">
              Images, PDFs, documents, archives • Max {MAX_MB} MB
            </p>
          </>
        )}
        {isDragReject && (
          <p className="text-red-400 text-sm font-medium">
            File type not supported or too large
          </p>
        )}
      </div>
    </div>
  )
}
