import React, { useState, useEffect } from 'react'
import { Card, Form, Input, Button, message, Progress, Descriptions, Tag } from 'antd'
import { UserOutlined, MailOutlined, PhoneOutlined, InfoCircleOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import api from '../services/api'

const Profile: React.FC = () => {
  const { user } = useAuth()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) {
      form.setFieldsValue({
        username: user.username,
        fullName: user.full_name,
        email: user.email,
        phone: user.phone
      })
    }
  }, [user, form])

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      await api.put('/auth/profile', values)
      message.success('个人资料更新成功')
    } catch (error) {
      message.error('更新失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="profile-page">
      <Card title="账户信息" className="profile-card" style={{ marginBottom: 20 }}>
        <Descriptions column={1} bordered>
          <Descriptions.Item label="当前版本">
            <Tag color={user?.version === 'basic' ? 'blue' : user?.version === 'pro' ? 'green' : 'red'}>
              {user?.version === 'basic' ? '基础版' : user?.version === 'pro' ? '专业版' : '企业版'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="配额使用情况">
            <div style={{ marginBottom: 10 }}>
              <Progress 
                percent={user ? Math.round((user.used_quota / user.monthly_quota) * 100) : 0} 
                status="active" 
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#666' }}>
              <span>已使用: {user?.used_quota} 次</span>
              <span>总配额: {user?.monthly_quota === 0 ? '无限' : user?.monthly_quota} 次</span>
            </div>
          </Descriptions.Item>
          <Descriptions.Item label="配额重置时间">
            {user?.last_reset ? new Date(user.last_reset).toLocaleString() : '-'}
          </Descriptions.Item>
        </Descriptions>
        <div style={{ marginTop: 16, padding: 12, backgroundColor: '#f0f2f5', borderRadius: 4 }}>
          <div style={{ display: 'flex', alignItems: 'center', color: '#666' }}>
            <InfoCircleOutlined style={{ marginRight: 8 }} />
            <span>
              基础版: 100次/月 | 专业版: 500次/月 | 企业版: 无限次
            </span>
          </div>
        </div>
      </Card>
      
      <Card title="个人资料" className="profile-card">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input prefix={<UserOutlined />} disabled />
          </Form.Item>

          <Form.Item
            name="fullName"
            label="姓名"
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>

          <Form.Item
            name="email"
            label="邮箱"
            rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}
          >
            <Input prefix={<MailOutlined />} placeholder="请输入邮箱" />
          </Form.Item>

          <Form.Item
            name="phone"
            label="手机号"
          >
            <Input prefix={<PhoneOutlined />} placeholder="请输入手机号" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              更新资料
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Profile