import { useState, useCallback, useRef } from 'react'
import { filesApi } from '../services/api'

const POLL_INTERVAL_MS = 2000
const POLL_MAX_ATTEMPTS = 90  // 3 minutes

export function useFileUpload() {
  const [uploadProgress, setUploadProgress]   = useState(0)
  const [status, setStatus]                   = useState('idle')   // idle|uploading|processing|done|error
  const [record, setRecord]                   = useState(null)
  const [error, setError]                     = useState(null)
  const pollRef                               = useRef(null)
  const attemptRef                            = useRef(0)

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  const startPolling = useCallback((recordId) => {
    attemptRef.current = 0
    stopPolling()
    pollRef.current = setInterval(async () => {
      attemptRef.current += 1
      if (attemptRef.current > POLL_MAX_ATTEMPTS) {
        stopPolling()
        setStatus('error')
        setError('Processing timed out. Please try again.')
        return
      }

      try {
        const { data } = await filesApi.pollJob(recordId)
        setRecord(data.record)

        if (data.record?.status === 'done') {
          stopPolling()
          setStatus('done')
        } else if (data.record?.status === 'error') {
          stopPolling()
          setStatus('error')
          setError(data.record.error_msg || 'Processing failed.')
        } else {
          setStatus('processing')
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }, POLL_INTERVAL_MS)
  }, [])

  const upload = useCallback(async (file, operation) => {
    stopPolling()
    setStatus('uploading')
    setUploadProgress(0)
    setError(null)
    setRecord(null)

    try {
      const { data } = await filesApi.upload(file, operation, setUploadProgress)
      setRecord(data)
      setStatus('processing')
      startPolling(data.id)
    } catch (err) {
      setStatus('error')
      setError(err.message || 'Upload failed.')
    }
  }, [startPolling])

  const reset = useCallback(() => {
    stopPolling()
    setStatus('idle')
    setUploadProgress(0)
    setRecord(null)
    setError(null)
  }, [])

  return { upload, reset, status, uploadProgress, record, error }
}
