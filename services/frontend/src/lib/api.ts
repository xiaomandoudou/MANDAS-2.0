import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8081'

if (!import.meta.env.VITE_API_URL && import.meta.env.PROD) {
  console.error('VITE_API_URL not configured for production build');
}

export const api = axios.create({
  baseURL: `${API_BASE_URL}/mandas/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)


export interface Task {
  id: string
  user_id: string
  status: string
  prompt: string
  plan?: any[]
  result?: any
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  prompt: string
  config?: Record<string, any>
}

export interface Document {
  id: string
  file_name: string
  file_size: number
  mime_type: string
  status: string
  created_at: string
}

export const taskApi = {
  create: (data: TaskCreate) => api.post('/tasks', data),
  get: (id: string) => api.get<Task>(`/tasks/${id}`),
  list: (params?: { page?: number; limit?: number; status_filter?: string }) =>
    api.get('/tasks', { params }),
  getPlan: (id: string, includeResult: boolean = false) => 
    api.get(`/tasks/${id}/plan`, { params: { include_result: includeResult } }),
  regeneratePlan: (id: string) => 
    api.post(`/tasks/${id}/plan/regenerate`),
}

export const documentApi = {
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  list: () => api.get<Document[]>('/documents'),
  delete: (id: string) => api.delete(`/documents/${id}`),
}

export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  register: (username: string, email: string, password: string) =>
    api.post('/auth/register', { username, email, password }),
}
