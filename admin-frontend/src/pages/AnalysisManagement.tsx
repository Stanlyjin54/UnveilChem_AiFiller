import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Space, Tag, message, Modal, Input, Select, Row, Col, Statistic, DatePicker, Descriptions } from 'antd'
import { EyeOutlined, SearchOutlined, ReloadOutlined, BarChartOutlined } from '@ant-design/icons'
import api from '../services/api'
import moment from 'moment'

interface Analysis {
  id: string
  document_id: string
  document_title: string
  analysis_type: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  result: any
  created_at: string
  completed_at?: string
  error_message?: string
}

const { RangePicker } = DatePicker
const { Option } = Select

const AnalysisManagement: React.FC = () => {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [dateRange, setDateRange] = useState<any>(null)
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    processing: 0,
    completed: 0,
    failed: 0
  })

  const fetchAnalyses = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (searchText) params.append('search', searchText)
      if (statusFilter) params.append('status', statusFilter)
      if (typeFilter) params.append('type', typeFilter)
      if (dateRange && dateRange.length === 2) {
        params.append('start_date', dateRange[0].format('YYYY-MM-DD'))
        params.append('end_date', dateRange[1].format('YYYY-MM-DD'))
      }

      const response = await api.get(`/admin/analyses?${params}`)
      setAnalyses(response.data.analyses)
      setStats(response.data.stats)
    } catch (error) {
      message.error('获取分析列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalyses()
  }, [searchText, statusFilter, typeFilter, dateRange])

  const handleView = (analysis: Analysis) => {
    Modal.info({
      title: '分析详情',
      width: 800,
      content: (
        <div>
          <Descriptions bordered column={2}>
            <Descriptions.Item label="文档标题">{analysis.document_title}</Descriptions.Item>
            <Descriptions.Item label="分析类型">
              <Tag color="blue">{analysis.analysis_type.toUpperCase()}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={
                analysis.status === 'completed' ? 'success' :
                analysis.status === 'processing' ? 'processing' :
                analysis.status === 'failed' ? 'error' : 'default'
              }>
                {analysis.status.toUpperCase()}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {moment(analysis.created_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
            {analysis.completed_at && (
              <Descriptions.Item label="完成时间">
                {moment(analysis.completed_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            )}
            {analysis.error_message && (
              <Descriptions.Item label="错误信息" span={2}>
                <span style={{ color: 'red' }}>{analysis.error_message}</span>
              </Descriptions.Item>
            )}
          </Descriptions>

          {analysis.result && (
            <div style={{ marginTop: 16 }}>
              <h4>分析结果：</h4>
              <pre style={{ 
                backgroundColor: '#f5f5f5', 
                padding: '12px', 
                borderRadius: '4px',
                maxHeight: '300px',
                overflow: 'auto'
              }}>
                {JSON.stringify(analysis.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )
    })
  }

  const columns = [
    {
      title: '文档标题',
      dataIndex: 'document_title',
      key: 'document_title',
      width: 200,
      ellipsis: true
    },
    {
      title: '分析类型',
      dataIndex: 'analysis_type',
      key: 'analysis_type',
      width: 120,
      render: (text: string) => <Tag color="blue">{text.toUpperCase()}</Tag>
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={
          status === 'completed' ? 'success' :
          status === 'processing' ? 'processing' :
          status === 'failed' ? 'error' : 'default'
        }>
          {status.toUpperCase()}
        </Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => moment(date).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: '完成时间',
      dataIndex: 'completed_at',
      key: 'completed_at',
      width: 180,
      render: (date: string) => date ? moment(date).format('YYYY-MM-DD HH:mm:ss') : '-'
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: Analysis) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
          >
            查看
          </Button>
        </Space>
      )
    }
  ]

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card>
            <Statistic title="总分析数" value={stats.total} prefix={<BarChartOutlined />} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="待处理" value={stats.pending} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="处理中" value={stats.processing} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="已完成" value={stats.completed} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="失败" value={stats.failed} />
          </Card>
        </Col>
      </Row>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Input
            placeholder="搜索文档标题"
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 250 }}
          />
          <Select
            placeholder="选择状态"
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 150 }}
            allowClear
          >
            <Option value="">全部状态</Option>
            <Option value="pending">待处理</Option>
            <Option value="processing">处理中</Option>
            <Option value="completed">已完成</Option>
            <Option value="failed">失败</Option>
          </Select>
          <Select
            placeholder="选择类型"
            value={typeFilter}
            onChange={setTypeFilter}
            style={{ width: 150 }}
            allowClear
          >
            <Option value="">全部类型</Option>
            <Option value="text_extraction">文本提取</Option>
            <Option value="content_analysis">内容分析</Option>
            <Option value="summary_generation">摘要生成</Option>
            <Option value="keyword_extraction">关键词提取</Option>
          </Select>
          <RangePicker
            value={dateRange}
            onChange={setDateRange}
            style={{ width: 250 }}
          />
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={fetchAnalyses}
          >
            刷新
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={analyses}
          loading={loading}
          rowKey="id"
          scroll={{ x: 1200 }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>
    </div>
  )
}

export default AnalysisManagement