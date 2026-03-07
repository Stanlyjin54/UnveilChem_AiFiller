import React from 'react'
import { Layout, Menu, Avatar, Dropdown, Space } from 'antd'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { 
  DashboardOutlined, 
  UserOutlined, 
  FileTextOutlined,
  BarChartOutlined,
  SettingOutlined, 
  LogoutOutlined,
  DownOutlined
} from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'



const { Header, Sider, Content } = Layout

const AdminLayout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/users',
      icon: <UserOutlined />,
      label: '用户管理',
    },
    {
      key: '/documents',
      icon: <FileTextOutlined />,
      label: '文档管理',
    },
    {
      key: '/analyses',
      icon: <BarChartOutlined />,
      label: '分析管理',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ]

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={250} theme="dark">
        <div style={{ 
          height: '64px', 
          display: 'flex', 
          alignItems: 'center', 
          padding: '0 16px',
          color: 'white',
          fontSize: '18px',
          fontWeight: 'bold',
          borderBottom: '1px solid #434343'
        }}>
          <span>🔬 unveilchem</span>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header style={{ 
          padding: '0 24px', 
          background: '#fff', 
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
              🧪 unveilchem - 管理后台
            </div>
          </div>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar size="small" icon={<UserOutlined />} />
              <span>{user?.username}</span>
              <DownOutlined />
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: '24px' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default AdminLayout