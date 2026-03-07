import React, { useState, useEffect } from 'react'
import { Table, Card, Button, Space, Tag, message, Popconfirm, Switch, Modal, Radio } from 'antd'
import { UserOutlined, DeleteOutlined, KeyOutlined } from '@ant-design/icons'
import { api } from '../services/api'

interface User {
  id: number
  username: string
  email: string
  role: 'user' | 'admin'
  is_active: boolean
  created_at: string
  document_count: number
  image_count: number
  version: string
  monthly_quota: number
  used_quota: number
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      const response = await api.get('/admin/users')
      setUsers(response.data)
    } catch (error) {
      message.error('获取用户列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleToggleActive = async (userId: number, currentStatus: boolean) => {
    try {
      if (currentStatus) {
        await api.put(`/admin/users/${userId}/deactivate`)
        message.success('用户已禁用')
      } else {
        await api.put(`/admin/users/${userId}/activate`)
        message.success('用户已激活')
      }
      fetchUsers()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handlePromoteToAdmin = async (userId: number, username: string) => {
    try {
      await api.post(`/admin/users/${userId}/promote`)
      message.success(`用户 ${username} 已成功提升为管理员`)
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '提升失败')
    }
  }

  const handleDemoteFromAdmin = async (userId: number, username: string) => {
    try {
      await api.post(`/admin/users/${userId}/demote`)
      message.success(`用户 ${username} 已降级为普通用户`)
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '降级失败')
    }
  }

  const [isModalVisible, setIsModalVisible] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [newVersion, setNewVersion] = useState('basic')

  const handleDeleteUser = async (userId: number) => {
    try {
      await api.delete(`/admin/users/${userId}`)
      message.success('用户删除成功')
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  const showUpdateVersionModal = (user: User) => {
    setSelectedUser(user)
    setNewVersion(user.version)
    setIsModalVisible(true)
  }

  const handleUpdateVersion = async () => {
    if (!selectedUser) return

    try {
      await api.put(`/admin/users/${selectedUser.id}/version`, {
        version: newVersion
      })
      message.success('版本更新成功')
      setIsModalVisible(false)
      fetchUsers()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '版本更新失败')
    }
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: User) => (
        <Space>
          <span style={{ fontWeight: 'bold' }}>{text}</span>
          {record.role === 'admin' && <Tag color="red">管理员</Tag>}
        </Space>
      ),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? '激活' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (version: string) => (
        <Tag color={
          version === 'basic' ? 'default' : 
          version === 'pro' ? 'blue' : 'red'
        }>
          {version === 'basic' ? '基础版' : 
           version === 'pro' ? '专业版' : '企业版'}
        </Tag>
      ),
    },
    {
      title: '配额',
      dataIndex: ['used_quota', 'monthly_quota'],
      key: 'quota',
      render: (_, record: User) => (
        <span>
          {record.used_quota} / {record.monthly_quota}
        </span>
      ),
    },
    {
      title: '文档数量',
      dataIndex: 'document_count',
      key: 'document_count',
      render: (count: number) => <Tag color="blue">{count}</Tag>,
    },
    {
      title: '图片数量',
      dataIndex: 'image_count',
      key: 'image_count',
      render: (count: number) => <Tag color="green">{count}</Tag>,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: User) => (
        <Space size="small">
          <Switch
            checked={record.is_active}
            onChange={() => handleToggleActive(record.id, record.is_active)}
            checkedChildren="激活"
            unCheckedChildren="禁用"
          />
          <Button 
            type="link" 
            size="small"
            onClick={() => showUpdateVersionModal(record)}
          >
            更新版本
          </Button>
          {record.role === 'user' ? (
            <Button 
              type="link" 
              size="small" 
              icon={<KeyOutlined />}
              onClick={() => handlePromoteToAdmin(record.id, record.username)}
            >
              提升管理员
            </Button>
          ) : (
            <Button 
              type="link" 
              size="small" 
              danger
              onClick={() => handleDemoteFromAdmin(record.id, record.username)}
            >
              降级用户
            </Button>
          )}
          <Popconfirm
            title="确定删除这个用户吗？"
            description="此操作不可逆，将删除用户所有数据"
            onConfirm={() => handleDeleteUser(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="link" 
              size="small" 
              danger 
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>
          <UserOutlined style={{ marginRight: 8 }} />
          用户管理
        </h2>
      </div>
      
      <Card>
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      {/* 版本更新模态框 */}
      <Modal
        title="更新用户版本"
        open={isModalVisible}
        onOk={handleUpdateVersion}
        onCancel={() => setIsModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        {selectedUser && (
          <div>
            <p style={{ marginBottom: 16 }}>
              用户名: <strong>{selectedUser.username}</strong>
            </p>
            <p style={{ marginBottom: 16 }}>
              当前版本: 
              <Tag color={
                selectedUser.version === 'basic' ? 'default' : 
                selectedUser.version === 'pro' ? 'blue' : 'red'
              }>
                {selectedUser.version === 'basic' ? '基础版' : 
                 selectedUser.version === 'pro' ? '专业版' : '企业版'}
              </Tag>
            </p>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 8 }}>
                选择新版本:
              </label>
              <Radio.Group 
                value={newVersion} 
                onChange={(e) => setNewVersion(e.target.value)}
                style={{ width: '100%' }}
              >
                <Radio value="basic" style={{ display: 'block', marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>基础版</span>
                    <Tag color="default">免费</Tag>
                  </div>
                  <div style={{ color: '#666', fontSize: '12px', marginTop: 4 }}>
                    100次/月 基础OCR功能
                  </div>
                </Radio>
                <Radio value="pro" style={{ display: 'block', marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>专业版</span>
                    <Tag color="blue">付费</Tag>
                  </div>
                  <div style={{ color: '#666', fontSize: '12px', marginTop: 4 }}>
                    1000次/月 包含Pix2Text和PaddleOCR高级功能
                  </div>
                </Radio>
                <Radio value="enterprise" style={{ display: 'block' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>企业版</span>
                    <Tag color="red">高级</Tag>
                  </div>
                  <div style={{ color: '#666', fontSize: '12px', marginTop: 4 }}>
                    无限次 包含所有高级解析功能
                  </div>
                </Radio>
              </Radio.Group>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default UserManagement