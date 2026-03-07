import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Typography } from 'antd'
import { 
  UserOutlined, 
  FileTextOutlined, 
  RocketOutlined,
  TeamOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import { api } from '../services/api'

const { Title } = Typography

interface DashboardStats {
  total_users: number
  active_users: number
  total_documents: number
  total_images: number
  admin_users: number
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    total_users: 0,
    active_users: 0,
    total_documents: 0,
    total_images: 0,
    admin_users: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await api.get('/admin/statistics')
      setStats(response.data.users)
    } catch (error) {
      console.error('获取统计信息失败:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* UnveilChem Logo标题区域 */}
      <div style={{ 
        textAlign: 'center', 
        marginBottom: '32px',
        padding: '24px 0',
        background: 'linear-gradient(135deg, #1890ff 0%, #52c41a 100%)',
        borderRadius: '12px',
        color: 'white'
      }}>
        <div style={{ 
          fontSize: '48px', 
          fontWeight: 'bold',
          marginBottom: '8px',
          textShadow: '2px 2px 4px rgba(0,0,0,0.3)'
        }}>
          🔬 UnveilChem
        </div>
        <div style={{ 
          fontSize: '18px',
          opacity: 0.9,
          letterSpacing: '1px'
        }}>
          管理后台仪表板
        </div>
      </div>

      <Title level={2}>
        <RocketOutlined style={{ marginRight: 8 }} />
        管理仪表板
      </Title>
      
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总用户数"
              value={stats.total_users}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={stats.active_users}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="管理员数量"
              value={stats.admin_users}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#faad14' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="文档总数"
              value={stats.total_documents}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#f5222d' }}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="系统状态" size="small">
            <div style={{ padding: '12px 0' }}>
              <p>✅ 后端服务: 正常运行</p>
              <p>✅ 数据库连接: 正常</p>
              <p>✅ API接口: 正常</p>
              <p>✅ 用户认证: 正常</p>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="快速操作" size="small">
            <div style={{ padding: '12px 0' }}>
              <p>• 查看用户列表</p>
              <p>• 管理用户权限</p>
              <p>• 查看系统日志</p>
              <p>• 系统配置管理</p>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard