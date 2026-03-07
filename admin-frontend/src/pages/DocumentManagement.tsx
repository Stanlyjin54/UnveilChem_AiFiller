import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Space, Tag, message, Modal, Input, Select, Row, Col, Statistic, DatePicker } from 'antd'
import { DeleteOutlined, EyeOutlined, SearchOutlined, ReloadOutlined } from '@ant-design/icons'
import api from '../services/api'
import moment from 'moment'

interface Document {
  id: string
  title: string
  filename: string
  file_type: string
  file_size: number
  upload_date: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  user_id: string
  user_email: string
  extracted_text?: string
  ai_summary?: string
}

const { RangePicker } = DatePicker
const { Option } = Select

const DocumentManagement: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [dateRange, setDateRange] = useState<any>(null)
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    processing: 0,
    completed: 0
  })

  const fetchDocuments = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (searchText) params.append('search', searchText)
      if (statusFilter) params.append('status', statusFilter)
      if (dateRange && dateRange.length === 2) {
        params.append('start_date', dateRange[0].format('YYYY-MM-DD'))
        params.append('end_date', dateRange[1].format('YYYY-MM-DD'))
      }

      const response = await api.get(`/admin/documents?${params}`)
      setDocuments(response.data.documents)
      setStats(response.data.stats)
    } catch (error) {
      message.error('获取文档列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [searchText, statusFilter, dateRange])

  const handleDelete = async (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个文档吗？此操作不可恢复。',
      onOk: async () => {
        try {
          await api.delete(`/admin/documents/${id}`)
          message.success('文档删除成功')
          fetchDocuments()
        } catch (error) {
          message.error('删除文档失败')
        }
      }
    })
  }

  const handleView = (document: Document) => {
    Modal.info({
      title: '文档详情',
      width: 800,
      content: (
        <div>
          <p><strong>标题：</strong>{document.title}</p>
          <p><strong>文件名：</strong>{document.filename}</p>
          <p><strong>文件类型：</strong>{document.file_type}</p>
          <p><strong>文件大小：</strong>{(document.file_size / 1024 / 1024).toFixed(2)} MB</p>
          <p><strong>上传时间：</strong>{moment(document.upload_date).format('YYYY-MM-DD HH:mm:ss')}</p>
          <p><strong>状态：</strong>
            <Tag color={
              document.status === 'completed' ? 'success' :
              document.status === 'processing' ? 'processing' :
              document.status === 'failed' ? 'error' : 'default'
            }>
              {document.status}
            </Tag>
          </p>
          <p><strong>上传用户：</strong>{document.user_email}</p>
          {document.ai_summary && (
            <div>
              <p><strong>AI摘要：</strong></p>
              <p style={{ backgroundColor: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
                {document.ai_summary}
              </p>
            </div>
          )}
        </div>
      )
    })
  }

  const handleReprocess = async (id: string) => {
    try {
      await api.post(`/admin/documents/${id}/reprocess`)
      message.success('文档重新处理中')
      fetchDocuments()
    } catch (error) {
      message.error('重新处理失败')
    }
  }

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      ellipsis: true
    },
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      width: 200,
      ellipsis: true
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      key: 'file_type',
      width: 100,
      render: (text: string) => <Tag color="blue">{text.toUpperCase()}</Tag>
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => `${(size / 1024 / 1024).toFixed(2)} MB`
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
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
      title: '上传用户',
      dataIndex: 'user_email',
      key: 'user_email',
      width: 180
    },
    {
      title: '上传时间',
      dataIndex: 'upload_date',
      key: 'upload_date',
      width: 180,
      render: (date: string) => moment(date).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: Document) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
          >
            查看
          </Button>
          {record.status === 'failed' && (
            <Button
              type="text"
              icon={<ReloadOutlined />}
              onClick={() => handleReprocess(record.id)}
            >
              重试
            </Button>
          )}
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      )
    }
  ]

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="总文档数" value={stats.total} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="待处理" value={stats.pending} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="处理中" value={stats.processing} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="已完成" value={stats.completed} />
          </Card>
        </Col>
      </Row>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Input
            placeholder="搜索文档标题或文件名"
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
          <RangePicker
            value={dateRange}
            onChange={setDateRange}
            style={{ width: 250 }}
          />
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={fetchDocuments}
          >
            刷新
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={documents}
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

export default DocumentManagement