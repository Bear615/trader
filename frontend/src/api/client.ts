import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Inject admin key on every request if stored
api.interceptors.request.use((cfg) => {
  const key = sessionStorage.getItem('adminKey')
  if (key) cfg.headers['X-Admin-Key'] = key
  return cfg
})

export default api
