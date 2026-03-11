import axios from 'axios'

// In Docker/Nginx the frontend talks to /api (proxied to backend)
// In dev Vite proxies /api to http://backend:8000
const API_BASE = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: { 'Accept': 'application/json' },
})

// Request logging in dev
api.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.debug(`[API] → ${config.method?.toUpperCase()} ${config.url}`)
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response error normalisation
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      'Unknown error'
    console.error(`[API] ✗ ${msg}`)
    return Promise.reject(new Error(msg))
  }
)

// ── File API calls ────────────────────────────────────────────────────────────

export const filesApi = {
  /** Upload a file with an operation. */
  upload(file, operation = 'copy', onProgress) {
    const form = new FormData()
    form.append('file', file)
    form.append('operation', operation)
    return api.post('/files/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress
        ? (evt) => onProgress(Math.round((evt.loaded * 100) / (evt.total || 1)))
        : undefined,
    })
  },

  /** List file records */
  list(skip = 0, limit = 50) {
    return api.get('/files/', { params: { skip, limit } })
  },

  /** Get a single record */
  getOne(recordId) {
    return api.get(`/files/${recordId}`)
  },

  /** Poll a job status by record id */
  pollJob(recordId) {
    return api.get(`/jobs/by-record/${recordId}`)
  },

  /** Get download URL */
  downloadUrl(recordId) {
    return `${API_BASE}/files/${recordId}/download`
  },

  /** Delete a record */
  delete(recordId) {
    return api.delete(`/files/${recordId}`)
  },

  /** Get supported operations */
  operations() {
    return api.get('/files/meta/operations')
  },
}

export const healthApi = {
  ping() {
    return api.get('/health/ping')
  },
  status() {
    return api.get('/health')
  },
}

export default api
