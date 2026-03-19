import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 1800000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 辅助函数：将错误详情转换为字符串
const formatErrorDetail = (detail: any): string => {
  if (!detail) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ')
  }
  if (typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail)
  }
  return String(detail)
}

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    
    // 统一错误信息处理
    let errorMessage = '操作失败，请稍后重试'
    const detail = error.response?.data?.detail
    if (detail) {
      errorMessage = formatErrorDetail(detail)
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message) {
      errorMessage = error.message
    }
    
    // 将统一的错误信息添加到error对象中
    error.unifiedMessage = errorMessage
    
    return Promise.reject(error)
  }
)

export default api
