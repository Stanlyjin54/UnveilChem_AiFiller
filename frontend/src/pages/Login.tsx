import React, { useState, useEffect } from 'react'
import { Form, Input, Button, Card } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const { login, user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (user) {
      navigate('/dashboard')
    }
  }, [user, navigate])

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    const success = await login(values.username, values.password)
    setLoading(false)
    if (success) {
      navigate('/dashboard')
    }
  }

  return (
    <div className="login-container">
      <Card className="login-form">
        <div className="login-title">
          <UserOutlined style={{ marginRight: 8 }} />
          登录 UnveilChem
        </div>
        
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          layout="vertical"
        >
          <Form.Item
            label="用户名/手机号/邮箱"
            name="username"
            rules={[
              { required: true, message: '请输入用户名、手机号或邮箱' }
            ]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="请输入用户名、手机号或邮箱" 
              size="large"
            />
          </Form.Item>

          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入密码"
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
              登录
            </Button>
          </Form.Item>
        </Form>

        <div className="register-link">
          还没有账号？ <Link to="/register">立即注册</Link>
        </div>
      </Card>
    </div>
  )
}

export default Login