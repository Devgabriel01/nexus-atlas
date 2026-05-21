import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('nexus_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('nexus_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

// Auth
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, username: string, password: string, full_name?: string) =>
    api.post('/auth/register', { email, username, password, full_name }),
}

// Scans
export const scanApi = {
  create: (data: ScanCreatePayload) => api.post('/scan/', data),
  list: (skip = 0, limit = 20) => api.get('/scan/', { params: { skip, limit } }),
  get: (id: string) => api.get(`/scan/${id}`),
  getStatus: (id: string) => api.get(`/scan/${id}/status`),
  delete: (id: string) => api.delete(`/scan/${id}`),
}

// Anomalies
export const anomalyApi = {
  list: (params?: Record<string, string | number>) =>
    api.get('/anomalies/', { params }),
  get: (id: string) => api.get(`/anomalies/${id}`),
}

// Reports
export const reportApi = {
  create: (data: { scan_id: string; title: string; summary?: string }) =>
    api.post('/reports/', data),
  list: () => api.get('/reports/'),
  downloadPdf: (id: string) => api.get(`/reports/${id}/download/pdf`, { responseType: 'blob' }),
  downloadJson: (id: string) => api.get(`/reports/${id}/download/json`, { responseType: 'blob' }),
}

// Exploration
export const explorationApi = {
  getSuggestedRegions: (category?: string) =>
    api.get('/exploration/suggested-regions', { params: category ? { category } : {} }),
  getHeatmapData: () => api.get('/exploration/heatmap-data'),
  getStats: () => api.get('/exploration/stats'),
}

// Analysis
export const analyzeApi = {
  coordinates: (lat: number, lon: number, radius_km = 10) =>
    api.post('/analyze/coordinates', { latitude: lat, longitude: lon, radius_km }),
  ndvi: (bounds: NDVIBounds) => api.post('/analyze/ndvi', bounds),
}

// History
export const historyApi = {
  list: (skip = 0, limit = 30) => api.get('/history/', { params: { skip, limit } }),
}

// Types
export interface ScanCreatePayload {
  name: string
  description?: string
  lat_min: number
  lat_max: number
  lon_min: number
  lon_max: number
  scan_type?: string
  date_start?: string
  date_end?: string
}

export interface NDVIBounds {
  lat_min: number
  lat_max: number
  lon_min: number
  lon_max: number
  date_start?: string
  date_end?: string
}
