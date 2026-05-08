import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({ baseURL: API_BASE })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && !error.config._retry) {
        error.config._retry = true
        try {
          const { data } = await axios.post(`${API_BASE}/auth/refresh`, { refresh_token: refreshToken })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          error.config.headers.Authorization = `Bearer ${data.access_token}`
          return api(error.config)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  setup: (data) => api.post('/auth/setup', data),
}

export const diseaseAPI = {
  predict: (formData) => api.post('/disease/predict', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  history: (page = 1) => api.get(`/disease/history?page=${page}`),
  gradcam: (id) => api.get(`/disease/gradcam/${id}`, { responseType: 'blob' }),
}

export const yieldAPI = {
  predict: (data) => api.post('/yield/predict', data),
  analytics: () => api.get('/yield/analytics'),
  features: () => api.get('/yield/features'),
}

export const adminAPI = {
  dashboard: () => api.get('/admin/dashboard'),
  users: (params) => api.get('/admin/users', { params }),
  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
  auditLogs: (params) => api.get('/admin/audit-logs', { params }),
}

export default api
