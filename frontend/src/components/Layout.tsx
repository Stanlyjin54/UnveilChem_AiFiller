import React from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Button, Dropdown, Avatar, Space } from 'antd'
import {
  DashboardOutlined,
  FileTextOutlined,
  PictureOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  TeamOutlined,
  RobotOutlined,
  ClockCircleOutlined,
  TranslationOutlined,
  FileSearchOutlined,
  ApiOutlined
} from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import logo from '../assets/logo.svg'
import './Layout.css'



const { Header, Sider, Content } = Layout

const AppLayout: React.FC = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '解析仪表板',
    },
    {
      key: '/documents',
      icon: <FileTextOutlined />,
      label: '文档管理',
    },
    {
      key: '/images',
      icon: <PictureOutlined />,
      label: '图像分析',
    },
    {
      key: '/automation',
      icon: <RobotOutlined />,
      label: '自动化仪表板',
    },
    {
      key: '/automation-execution',
      icon: <ClockCircleOutlined />,
      label: '自动化执行',
    },
    {
      key: '/parameter-mapping',
      icon: <SettingOutlined />,
      label: '参数映射',
    },
    {
      key: '/agent',
      icon: <RobotOutlined />,
      label: '智能Agent',
    },
    {
      key: '/translation',
      icon: <TranslationOutlined />,
      label: '文档翻译',
    },
    {
      key: '/report',
      icon: <FileSearchOutlined />,
      label: '报告生成',
    },
    {
      key: '/llm-config',
      icon: <ApiOutlined />,
      label: 'LLM配置',
    },
    ...(user?.role === 'admin' ? [{
      key: '/admin',
      icon: <TeamOutlined />,
      label: '管理后台',
    }] : [])
  ]

  // 用户菜单已在Dropdown组件中直接定义，无需单独声明
  // const userMenuItems = [
  //   {
  //     key: 'profile',
  //     icon: <UserOutlined />,
  //     label: '个人资料',
  //   },
  //   {
  //     key: 'settings',
  //     icon: <SettingOutlined />,
  //     label: '设置',
  //   },
  //   {
  //     type: 'divider' as const,
  //   },
  //   {
  //     key: 'logout',
  //     icon: <LogoutOutlined />,
  //     label: '退出登录',
  //     onClick: logout,
  //   },
  // ]

  return (
    <Layout className="app-layout">
      <Header className="app-header">
        <div className="app-logo">
          <img src={logo} alt="UnveilChem" style={{ width: '24px', height: '24px', marginRight: '8px', verticalAlign: 'middle' }} />
          UnveilChem
        </div>
        
        <Space>
          <span style={{ color: 'white' }}>欢迎，{user?.username}</span>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'profile',
                  icon: <UserOutlined />,
                  label: '个人资料',
                  onClick: () => navigate('/profile')
                },
                {
                  key: 'settings',
                  icon: <SettingOutlined />,
                  label: '设置',
                  onClick: () => navigate('/settings')
                },
                {
                  type: 'divider' as const
                },
                {
                  key: 'logout',
                  icon: <LogoutOutlined />,
                  label: '退出登录',
                  onClick: logout
                }
              ]
            }}
            placement="bottomRight"
          >
            <Button type="text" style={{ color: 'white' }}>
              <Avatar size="small" icon={<UserOutlined />} />
            </Button>
          </Dropdown>
        </Space>
      </Header>
      
      <Layout>
        <Sider width={200} className="app-sider">
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            className="app-menu"
          />
        </Sider>
        
        <Layout className="app-content-layout">
          <Content className="app-content">
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default AppLayout