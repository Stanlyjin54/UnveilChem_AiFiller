import React from 'react'
import { Card, Row, Col, Statistic, Button, Tag, Table } from 'antd'
import { 
  FileTextOutlined, 
  PictureOutlined, 
  TeamOutlined, 
  RocketOutlined,
  ArrowRightOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import logo from '../assets/logo.svg'



const Dashboard: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()

  const featureCards = [
    {
      title: '文档解析',
      description: '上传化工文档，自动提取工艺参数和化学信息',
      icon: <FileTextOutlined className="feature-icon" />,
      path: '/documents',
      color: '#1890ff'
    },
    {
      title: '图片解析',
      description: '上传化工图片，识别化学结构和工艺流程图',
      icon: <PictureOutlined className="feature-icon" />,
      path: '/images',
      color: '#52c41a'
    },
    {
      title: '管理后台',
      description: '用户管理和系统统计（仅管理员可用）',
      icon: <TeamOutlined className="feature-icon" />,
      path: '/admin',
      color: '#faad14',
      adminOnly: true
    }
  ]

  const filteredFeatures = featureCards.filter(feature => 
    !feature.adminOnly || user?.role === 'admin'
  )

  // 版本功能对比数据
  const versionFeatures = [
    { key: '1', feature: '基础PDF解析', basic: true, pro: true, enterprise: true },
    { key: '2', feature: '基础OCR识别', basic: true, pro: true, enterprise: true },
    { key: '3', feature: 'Pix2Text复杂PDF解析', basic: false, pro: true, enterprise: true },
    { key: '4', feature: 'PaddleOCR高精度识别', basic: false, pro: true, enterprise: true },
    { key: '5', feature: '高级统一解析器', basic: false, pro: false, enterprise: true },
    { key: '6', feature: '月使用配额', basic: '100次', pro: '500次', enterprise: '无限' },
    { key: '7', feature: '优先处理', basic: false, pro: false, enterprise: true },
    { key: '8', feature: '自动化功能', basic: false, pro: true, enterprise: true },
  ];

  // 表格列配置
  const columns = [
    {
      title: '功能',
      dataIndex: 'feature',
      key: 'feature',
    },
    {
      title: '基础版',
      dataIndex: 'basic',
      key: 'basic',
      render: (value: any) => {
        if (typeof value === 'boolean') {
          return value ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
        }
        return value;
      },
    },
    {
      title: '专业版',
      dataIndex: 'pro',
      key: 'pro',
      render: (value: any) => {
        if (typeof value === 'boolean') {
          return value ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
        }
        return value;
      },
    },
    {
      title: '企业版',
      dataIndex: 'enterprise',
      key: 'enterprise',
      render: (value: any) => {
        if (typeof value === 'boolean') {
          return value ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
        }
        return value;
      },
    },
  ];

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
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '48px', 
          fontWeight: 'bold',
          marginBottom: '8px',
          textShadow: '2px 2px 4px rgba(0,0,0,0.3)'
        }}>
          <img src={logo} alt="UnveilChem" style={{ width: '48px', height: '48px', marginRight: '16px', verticalAlign: 'middle' }} />
          UnveilChem
        </div>
        <div style={{ 
          fontSize: '18px',
          opacity: 0.9,
          letterSpacing: '1px'
        }}>
          智能化工软件自动化平台
        </div>
      </div>

      {/* 欢迎卡片 */}
      <Card className="welcome-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div className="welcome-title">
              从一束火花，点燃一个智能的世界{user?.username}！
            </div>
            <div className="welcome-subtitle">
            智能化工软件自动化助手已就绪,开始您的软件自动化之旅 !
          </div>
            <div style={{ marginTop: 12 }}>
              <Tag color={user?.version === 'basic' ? 'blue' : user?.version === 'pro' ? 'green' : 'red'} style={{ fontSize: 14 }}>
                当前版本: {user?.version === 'basic' ? '基础版' : user?.version === 'pro' ? '专业版' : '企业版'}
              </Tag>
            </div>
          </div>
          <RocketOutlined style={{ fontSize: '48px', opacity: 0.8 }} />
        </div>
      </Card>

      {/* 统计信息 */}
      <Row gutter={[24, 24]} className="admin-stats">
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ textAlign: 'center', height: '200px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <Statistic
              title="今日解析"
              value={12}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff', fontSize: '24px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ textAlign: 'center', height: '200px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <Statistic
              title="图片识别"
              value={8}
              prefix={<PictureOutlined />}
              valueStyle={{ color: '#52c41a', fontSize: '24px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ textAlign: 'center', height: '200px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <Statistic
              title="化学实体"
              value={45}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#faad14', fontSize: '24px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ textAlign: 'center', height: '200px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <Statistic
              title="工艺参数"
              value={23}
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#f5222d', fontSize: '24px' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 版本功能对比 */}
      <Card title="版本功能对比" style={{ marginTop: 24 }}>
        <Table 
          columns={columns} 
          dataSource={versionFeatures} 
          pagination={false} 
          size="small"
          bordered
        />
      </Card>

      {/* 功能卡片 */}
      <div className="feature-cards">
        {filteredFeatures.map((feature, index) => (
          <Card 
            key={index} 
            className="feature-card"
            hoverable
            onClick={() => navigate(feature.path)}
          >
            <div style={{ color: feature.color }}>
              {feature.icon}
            </div>
            <div className="feature-title">{feature.title}</div>
            <div className="feature-description">{feature.description}</div>
            <Button 
              type="primary" 
              style={{ marginTop: '16px', background: feature.color }}
              icon={<ArrowRightOutlined />}
            >
              开始使用
            </Button>
          </Card>
        ))}
      </div>

      {/* 快速操作 */}
      <Card title="快速操作" style={{ marginTop: '24px' }}>
        <Row gutter={16}>
          <Col span={8}>
            <Button 
              type="primary" 
              icon={<FileTextOutlined />} 
              size="large" 
              block
              onClick={() => navigate('/documents')}
            >
              上传文档
            </Button>
          </Col>
          <Col span={8}>
            <Button 
              type="default" 
              icon={<PictureOutlined />} 
              size="large" 
              block
              onClick={() => navigate('/images')}
            >
              上传图片
            </Button>
          </Col>
          {user?.role === 'admin' && (
            <Col span={8}>
              <Button 
                type="dashed" 
                icon={<TeamOutlined />} 
                size="large" 
                block
                onClick={() => navigate('/admin')}
              >
                系统管理
              </Button>
            </Col>
          )}
        </Row>
      </Card>
    </div>
  )
}

export default Dashboard