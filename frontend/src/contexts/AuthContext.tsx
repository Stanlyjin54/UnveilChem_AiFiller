import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { message } from 'antd'
import api from '../services/api'

interface User {
  id: number
  username: string
  email: string
  phone?: string
  full_name?: string
  role: 'user' | 'admin'
  is_active: boolean
  // 新增版本和配额字段
  version: string
  monthly_quota: number
  used_quota: number
  last_reset: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<boolean>
  register: (username: string, email: string | undefined, password: string, phone?: string) => Promise<boolean>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      api.defaults.headers.Authorization = `Bearer ${token}`
      fetchCurrentUser()
    } else {
      setLoading(false)
    }
  }, [token])

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/auth/me')
      console.log('获取用户信息成功:', response.data)
      // 确保user对象包含所有必要字段
      setUser({
        ...response.data,
        full_name: response.data.full_name || '',
        phone: response.data.phone || ''
      })
    } catch (error: any) {
      console.error('获取用户信息失败:', error)
      console.error('错误详情:', error.response?.data)
      localStorage.removeItem('token')
      setToken(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await api.post('/auth/login', { username, password })
      console.log('登录响应:', response.data)
      const { access_token, user: userData } = response.data
      
      localStorage.setItem('token', access_token)
      setToken(access_token)
      setUser(userData)
      api.defaults.headers.Authorization = `Bearer ${access_token}`
      
      message.success('登录成功')
      return true
    } catch (error: any) {
      console.error('登录失败:', error)
      console.error('错误详情:', error.response?.data)
      message.error(error.unifiedMessage || '登录失败')
      return false
    }
  }

  const register = async (username: string, email: string | undefined, password: string, phone?: string): Promise<boolean> => {
    try {
      await api.post('/auth/register', { username, email, password, phone })
      message.success('注册成功，请登录')
      return true
    } catch (error: any) {
      message.error(error.unifiedMessage || '注册失败')
      return false
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
    delete api.defaults.headers.Authorization
    message.success('已退出登录')
  }

  const value = {
    user,
    token,
    login,
    register,
    logout,
    loading
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}