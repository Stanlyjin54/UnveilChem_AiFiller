import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Tag, Space, Typography, message, Spin, Select } from 'antd'
import { RobotOutlined, CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined, CloseOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography
const { Option } = Select

interface AutomationTask {
  task_id: string
  name: string
  status: string
  target_software: string
  created_time: string
  retry_count: number
  error_message?: string
}

const AutomationExecution: React.FC = () => {
  const [tasks, setTasks] = useState<AutomationTask[]>([])
  const [loading, setLoading] = useState(false)
  const [filterStatus, setFilterStatus] = useState('')
  const [supportedSoftware, setSupportedSoftware] = useState<string[]>([])
  const [filterSoftware, setFilterSoftware] = useState('')

  // 状态颜色映射
  const statusColors: Record<string, string> = {
    'running': 'blue',
    'completed': 'green',
    'failed': 'red',
    'pending': 'orange',
    'cancelled': 'gray'
  }

  // 状态图标映射
  const statusIcons: Record<string, React.ReactNode> = {
    'running': <ClockCircleOutlined />,
    'completed': <CheckCircleOutlined />,
    'failed': <CloseCircleOutlined />,
    'pending': <ClockCircleOutlined />,
    'cancelled': <CloseOutlined />
  }

  // 获取任务列表
  const fetchTasks = async () => {
    setLoading(true)
    try {
      const response = await api.get('/automation/all-tasks')
      if (response.data) {
        setTasks(response.data)
        setLastRefreshTime(new Date())
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取支持的软件列表
  const fetchSupportedSoftware = async () => {
    try {
      const response = await api.get('/automation/supported-software')
      if (response.data) {
        setSupportedSoftware(response.data.supported_software)
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取支持的软件列表失败')
    }
  }

  // 取消任务
  const handleCancelTask = async (taskId: string) => {
    try {
      await api.post(`/automation/cancel-task/${taskId}`)
      message.success('任务已取消')
      // 刷新任务列表
      fetchTasks()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '取消任务失败')
    }
  }

  // 添加最后刷新时间状态
  const [lastRefreshTime, setLastRefreshTime] = useState<Date | null>(null)

  // 组件挂载时获取数据
  useEffect(() => {
    fetchTasks()
    fetchSupportedSoftware()
    // 缩短刷新间隔，从5秒改为2秒
    const interval = setInterval(() => {
      fetchTasks()
      setLastRefreshTime(new Date())
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  // 过滤任务
  const filteredTasks = tasks.filter(task => {
    const matchesStatus = !filterStatus || task.status === filterStatus
    const matchesSoftware = !filterSoftware || task.target_software === filterSoftware
    return matchesStatus && matchesSoftware
  })

  // 表格列定义
  const columns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true
    },
    {
      title: '目标软件',
      dataIndex: 'target_software',
      key: 'target_software',
      render: (text: string) => (
        <Tag color="blue">{text}</Tag>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={statusColors[status] || 'default'} icon={statusIcons[status]}>
          {status}
        </Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_time',
      key: 'created_time',
      render: (time: string) => new Date(time).toLocaleString()
    },
    {
      title: '重试次数',
      dataIndex: 'retry_count',
      key: 'retry_count'
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      ellipsis: true,
      render: (error: string | undefined) => error || '-'
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: AutomationTask) => (
        <Space size="middle">
          {record.status === 'running' && (
            <Button 
              type="default" 
              danger 
              icon={<CloseOutlined />} 
              onClick={() => handleCancelTask(record.task_id)}
            >
              取消
            </Button>
          )}
          {record.status === 'failed' && (
            <Button type="primary" icon={<ClockCircleOutlined />}>
              重试
            </Button>
          )}
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <RobotOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
        <Title level={2}>自动化执行</Title>
      </div>
      <Text type="secondary">查看和管理自动化任务的执行状态</Text>

      {/* 筛选栏 */}
      <Card style={{ marginTop: 24, marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <div>
            <Text strong>状态筛选：</Text>
            <Select 
              value={filterStatus} 
              onChange={setFilterStatus}
              style={{ width: 150, marginLeft: 8 }}
              placeholder="全部状态"
            >
              <Option value="">全部</Option>
              <Option value="pending">待执行</Option>
              <Option value="running">运行中</Option>
              <Option value="completed">已完成</Option>
              <Option value="failed">失败</Option>
              <Option value="cancelled">已取消</Option>
            </Select>
          </div>
          <div>
            <Text strong>软件筛选：</Text>
            <Select 
              value={filterSoftware} 
              onChange={setFilterSoftware}
              style={{ width: 150, marginLeft: 8 }}
              placeholder="全部软件"
            >
              <Option value="">全部</Option>
              {supportedSoftware.map(software => (
                <Option key={software} value={software}>{software}</Option>
              ))}
            </Select>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 16 }}>
            <Button 
              type="primary" 
              onClick={fetchTasks}
              loading={loading}
            >
              刷新任务列表
            </Button>
            {lastRefreshTime && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                最后刷新: {lastRefreshTime.toLocaleTimeString()}
              </Text>
            )}
          </div>
        </div>
      </Card>

      {/* 任务列表 */}
      <Card style={{ marginTop: 24 }}>
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={filteredTasks}
            rowKey="task_id"
            pagination={{ pageSize: 10 }}
            bordered
          />
        </Spin>
      </Card>

      {/* 统计信息 */}
      <Card style={{ marginTop: 24 }}>
        <Title level={4}>任务统计</Title>
        <div style={{ display: 'flex', gap: 24, marginTop: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Tag color="green" icon={<CheckCircleOutlined />}>
              已完成
            </Tag>
            <Text strong>{tasks.filter(t => t.status === 'completed').length}</Text>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Tag color="red" icon={<CloseCircleOutlined />}>
              失败
            </Tag>
            <Text strong>{tasks.filter(t => t.status === 'failed').length}</Text>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Tag color="blue" icon={<ClockCircleOutlined />}>
              运行中
            </Tag>
            <Text strong>{tasks.filter(t => t.status === 'running').length}</Text>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Tag color="orange" icon={<ClockCircleOutlined />}>
              待执行
            </Tag>
            <Text strong>{tasks.filter(t => t.status === 'pending').length}</Text>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Tag color="gray" icon={<CloseOutlined />}>
              已取消
            </Tag>
            <Text strong>{tasks.filter(t => t.status === 'cancelled').length}</Text>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default AutomationExecution
