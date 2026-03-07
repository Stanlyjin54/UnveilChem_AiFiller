import React, { useState, useEffect } from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, MailOutlined, LockOutlined, PhoneOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const Register: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const { register, user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (user) {
      navigate('/dashboard')
    }
  }, [user, navigate])

  const onFinish = async (values: {
    username: string
    phone?: string
    email?: string
    password: string
    confirmPassword: string
  }) => {
    if (values.password !== values.confirmPassword) {
      message.error('两次输入的密码不一致')
      return
    }

    // 验证至少提供手机号或邮箱之一
    if (!values.phone && !values.email) {
      message.error('请提供手机号或邮箱进行验证')
      return
    }

    setLoading(true)
    const success = await register(values.username, values.email, values.password, values.phone)
    setLoading(false)
    if (success) {
      navigate('/login')
    }
  }

  return (
    <div className="login-container">
      <Card className="login-form">
        <div className="login-title">
          <UserOutlined style={{ marginRight: 8 }} />
          注册 UnveilChem
        </div>
        
        <Form
          name="register"
          onFinish={onFinish}
          autoComplete="off"
          layout="vertical"
        >
          <Form.Item
            label="用户名"
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
              { max: 20, message: '用户名最多20个字符' }
            ]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="请输入用户名" 
              size="large"
            />
          </Form.Item>

          <Form.Item
            label="手机号"
            name="phone"
            rules={[
              { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号' }
            ]}
          >
            <Input 
              prefix={<PhoneOutlined />} 
              placeholder="请输入手机号（优先使用）" 
              size="large"
            />
          </Form.Item>

          <Form.Item
            label="邮箱"
            name="email"
            rules={[
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input 
              prefix={<MailOutlined />} 
              placeholder="请输入邮箱地址（可选）" 
              size="large"
            />
          </Form.Item>

          <Form.Item
            label="密码"
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入密码"
              size="large"
            />
          </Form.Item>

          <Form.Item
            label="确认密码"
            name="confirmPassword"
            rules={[
              { required: true, message: '请确认密码' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请再次输入密码"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              size="large"
              block
            >
              注册
            </Button>
          </Form.Item>
        </Form>

        <div className="register-link">
          已有账号？ <Link to="/login">立即登录</Link>
        </div>
      </Card>
    </div>
  )
}

export default Register