import React, { useState, useEffect } from 'react'
import { 
  Table, 
  Card, 
  Typography, 
  Button, 
  Space, 
  Tag, 
  message, 
  Statistic,
  Row,
  Col,
  Switch,
  Popconfirm,
  Progress, 
  Modal, 
  Select 
} from 'antd'
import { 
  TeamOutlined, 
  UserAddOutlined, 
  EditOutlined, 
  DeleteOutlined,
  FileTextOutlined,
  PictureOutlined,
  RocketOutlined
} from '@ant-design/icons'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

const { Title, Text } = Typography

interface User {
  id: number
  username: string
  email: string
  role: 'user' | 'admin'
  is_active: boolean
  created_at: string
  document_count: number
  image_count: number
  // 新增版本和配额字段
  version: string
  monthly_quota: number
  used_quota: number
  last_reset: string
}

const AdminPanel: React.FC = () => {
  const { user } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    total_users: 0,
    total_documents: 0,
    total_images: 0,
    active_users: 0
  })
  // 版本更新相关状态
  const [versionModalVisible, setVersionModalVisible] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [newVersion, setNewVersion] = useState<string>('basic')
  const [versionLoading, setVersionLoading] = useState(false)

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchUsers()
      fetchStats()
    }
  }, [user])

  const fetchUsers = async () => {
    try {
      const response = await api.get('/admin/users')
      setUsers(response.data)
    } catch (error: any) {
      message.error('获取用户列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await api.get('/admin/stats')
      setStats(response.data)
    } catch (error: any) {
      message.error('获取统计信息失败')
    }
  }

  const handleToggleActive = async (userId: number, currentStatus: boolean) => {
    try {
      await api.patch(`/admin/users/${userId}/status`, {
        is_active: !currentStatus
      })
      message.success(`用户已${!currentStatus ? '激活' : '禁用'}`)
      fetchUsers()
    } catch (error: any) {
      message.error('操作失败')
    }
  }

  const handleDeleteUser = async (userId: number) => {
    try {
      await api.delete(`/admin/users/${userId}`)
      message.success('用户删除成功')
      fetchUsers()
    } catch (error: any) {
      message.error('删除失败')
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

  // 打开版本更新模态框
  const handleOpenVersionModal = (user: User) => {
    setSelectedUser(user)
    setNewVersion(user.version)
    setVersionModalVisible(true)
  }

  // 关闭版本更新模态框
  const handleCloseVersionModal = () => {
    setVersionModalVisible(false)
    setSelectedUser(null)
    setNewVersion('basic')
  }

  // 提交版本更新
  const handleUpdateVersion = async () => {
    if (!selectedUser) return
    
    setVersionLoading(true)
    try {
      await api.put(`/admin/users/${selectedUser.id}/version`, { version: newVersion })
      message.success(`用户 ${selectedUser.username} 版本已更新为 ${newVersion === 'basic' ? '基础版' : newVersion === 'pro' ? '专业版' : '企业版'}`)
      fetchUsers()
      handleCloseVersionModal()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '版本更新失败')
    } finally {
      setVersionLoading(false)
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
          <Text strong>{text}</Text>
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
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (version: string) => (
        <Tag color={version === 'basic' ? 'blue' : version === 'pro' ? 'green' : 'red'}>
          {version === 'basic' ? '基础版' : version === 'pro' ? '专业版' : '企业版'}
        </Tag>
      ),
    },
    {
      title: '配额',
      dataIndex: 'used_quota',
      key: 'quota',
      render: (_: any, record: User) => (
        <div>
          <div style={{ fontSize: 12, color: '#666' }}>
            {record.used_quota}/{record.monthly_quota === 0 ? '无限' : record.monthly_quota}
          </div>
          <Progress 
            percent={record.monthly_quota === 0 ? 0 : Math.round((record.used_quota / record.monthly_quota) * 100)} 
            size="small" 
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean, record: User) => (
        <Switch
          checked={isActive}
          onChange={() => handleToggleActive(record.id, isActive)}
          checkedChildren="激活"
          unCheckedChildren="禁用"
        />
      ),
    },
    {
      title: '文档数量',
      dataIndex: 'document_count',
      key: 'document_count',
      render: (count: number) => (
        <Tag icon={<FileTextOutlined />} color="blue">
          {count}
        </Tag>
      ),
    },
    {
      title: '图片数量',
      dataIndex: 'image_count',
      key: 'image_count',
      render: (count: number) => (
        <Tag icon={<PictureOutlined />} color="green">
          {count}
        </Tag>
      ),
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
          <Button 
            type="link" 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => handleOpenVersionModal(record)}
          >
            更新版本
          </Button>
          {record.role === 'user' ? (
            <Button 
              type="link" 
              size="small" 
              icon={<EditOutlined />}
              onClick={() => handlePromoteToAdmin(record.id, record.username)}
            >
              提升为管理员
            </Button>
          ) : (
            <Button 
              type="link" 
              size="small" 
              icon={<EditOutlined />}
              onClick={() => handleDemoteFromAdmin(record.id, record.username)}
              disabled={record.id === user?.id}  // 不能降级自己
            >
              降级为普通用户
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
              disabled={record.id === user?.id}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  if (user?.role !== 'admin') {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Title level={3} type="danger">权限不足</Title>
          <Text type="secondary">您没有访问管理后台的权限</Text>
        </div>
      </Card>
    )
  }

  return (
    <div>
      <Title level={2}>
        <TeamOutlined style={{ marginRight: 8 }} />
        管理后台
      </Title>

      {/* 统计信息 */}
      <Row gutter={16} className="admin-stats">
        <Col span={6}>
          <Card>
            <Statistic
              title="总用户数"
              value={stats.total_users}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={stats.active_users}
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="文档总数"
              value={stats.total_documents}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="图片总数"
              value={stats.total_images}
              prefix={<PictureOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 用户管理 */}
      <Card 
        title="用户管理" 
        extra={
          <Button type="primary" icon={<UserAddOutlined />}>
            添加用户
          </Button>
        }
      >
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
        open={versionModalVisible}
        onOk={handleUpdateVersion}
        onCancel={handleCloseVersionModal}
        confirmLoading={versionLoading}
        okText="确定"
        cancelText="取消"
      >
        {selectedUser && (
          <div>
            <p>用户名: {selectedUser.username}</p>
            <p>当前版本: 
              <Tag color={selectedUser.version === 'basic' ? 'blue' : selectedUser.version === 'pro' ? 'green' : 'red'}>
                {selectedUser.version === 'basic' ? '基础版' : selectedUser.version === 'pro' ? '专业版' : '企业版'}
              </Tag>
            </p>
            <div style={{ marginTop: 16 }}>
              <label style={{ display: 'block', marginBottom: 8 }}>选择新版本:</label>
              <Select
                value={newVersion}
                onChange={setNewVersion}
                style={{ width: '100%' }}
              >
                <Select.Option value="basic">基础版</Select.Option>
                <Select.Option value="pro">专业版</Select.Option>
                <Select.Option value="enterprise">企业版</Select.Option>
              </Select>
            </div>
            <div style={{ marginTop: 16, padding: 12, backgroundColor: '#f0f2f5', borderRadius: 4 }}>
              <h4 style={{ margin: 0, marginBottom: 8 }}>版本功能对比:</h4>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                <li><strong>基础版</strong>: 100次/月，基础PDF解析，基础OCR识别</li>
                <li><strong>专业版</strong>: 500次/月，包含基础版所有功能，Pix2Text复杂PDF解析，PaddleOCR高精度识别，自动化功能</li>
                <li><strong>企业版</strong>: 无限次/月，包含专业版所有功能，高级统一解析器，优先处理</li>
              </ul>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default AdminPanel