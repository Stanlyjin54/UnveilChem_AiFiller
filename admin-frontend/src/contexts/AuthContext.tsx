import React, { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../services/api'

interface User {
  id: number
  username: string
  email: string
  role: 'admin'
  is_active: boolean
  created_at: string
}

interface AuthContextType {
  user: User | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 检查本地存储的token
    const token = localStorage.getItem('admin_token')
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      // 验证token有效性
      checkAuth()
    } else {
      setLoading(false)
    }
  }, [])

  const checkAuth = async () => {
    try {
      const response = await api.get('/auth/me')
      setUser(response.data)
    } catch (error) {
      localStorage.removeItem('admin_token')
      delete api.defaults.headers.common['Authorization']
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    try {
      const response = await api.post('/auth/login', { username, password })
      const { access_token, user: userData } = response.data
      
      localStorage.setItem('admin_token', access_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      setUser(userData)
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('admin_token')
    delete api.defaults.headers.common['Authorization']
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}