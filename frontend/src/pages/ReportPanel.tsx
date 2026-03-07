import React, { useState, useEffect } from 'react'
import { Card, Input, Button, Select, Space, Divider, Alert, Typography, Tabs, Table, message, Modal, Form } from 'antd'
import { FileTextOutlined, PlusOutlined, DownloadOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons'
import { reportAPI, ReportRequest } from '../services/agentApi'

const { Text } = Typography
const { TabPane } = Tabs

interface ReportTemplate {
  id: string
  name: string
  type: string
  description: string
}

interface Parameter {
  key: string
  value: string
  unit?: string
}

const ReportPanel: React.FC = () => {
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [templates, setTemplates] = useState<ReportTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string>('parameter_summary')
  const [reportContent, setReportContent] = useState<string>('')
  const [reportTitle, setReportTitle] = useState('参数汇总报告')
  const [reportFormat, setReportFormat] = useState('markdown')
  const [parameters, setParameters] = useState<Parameter[]>([])
  const [modalVisible, setModalVisible] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadTemplates()
  }, [])

  const loadTemplates = async () => {
    try {
      const data = await reportAPI.getTemplates()
      setTemplates(data)
    } catch (err: any) {
      setError(err.unifiedMessage || '加载模板失败')
    }
  }

  const handleGenerateReport = async () => {
    if (parameters.length === 0) {
      message.warning('请先添加参数数据')
      return
    }

    setGenerating(true)
    setError(null)

    try {
      const request: ReportRequest = {
        report_type: selectedTemplate,
        source_data: { parameters: parameters.map(p => ({ name: p.key, value: p.value, unit: p.unit })) },
        title: reportTitle,
        format: reportFormat
      }

      const result = await reportAPI.generate(request)
      setReportContent(result.content)
      message.success('报告生成成功')
    } catch (err: any) {
      setError(err.unifiedMessage || '报告生成失败')
    } finally {
      setGenerating(false)
    }
  }

  const handleAddParameter = () => {
    form.validateFields().then(values => {
      setParameters([...parameters, { key: values.paramName, value: values.paramValue, unit: values.paramUnit }])
      form.resetFields()
      setModalVisible(false)
    })
  }

  const handleDeleteParameter = (key: string) => {
    setParameters(parameters.filter(p => p.key !== key))
  }

  const handleDownload = () => {
    if (reportContent) {
      const blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${reportTitle}.${reportFormat === 'markdown' ? 'md' : reportFormat}`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  const paramColumns = [
    { title: '参数名', dataIndex: 'key', key: 'key' },
    { title: '参数值', dataIndex: 'value', key: 'value' },
    { title: '单位', dataIndex: 'unit', key: 'unit' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Parameter) => (
        <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleDeleteParameter(record.key)}>
          删除
        </Button>
      )
    }
  ]

  return (
    <div className="report-panel" style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <FileTextOutlined />
            <span>报告生成</span>
          </Space>
        }
      >
        <Tabs defaultActiveKey="parameter">
          <TabPane tab="参数汇总报告" key="parameter">
            <div className="report-config" style={{ marginBottom: 24 }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space>
                  <Text>报告标题：</Text>
                  <Input
                    value={reportTitle}
                    onChange={(e) => setReportTitle(e.target.value)}
                    style={{ width: 300 }}
                    placeholder="输入报告标题"
                  />
                </Space>
                <Space>
                  <Text>报告类型：</Text>
                  <Select
                    value={selectedTemplate}
                    onChange={setSelectedTemplate}
                    style={{ width: 200 }}
                    options={templates.map(t => ({ value: t.type, label: t.name }))}
                  />
                </Space>
                <Space>
                  <Text>输出格式：</Text>
                  <Select
                    value={reportFormat}
                    onChange={setReportFormat}
                    style={{ width: 120 }}
                    options={[
                      { value: 'markdown', label: 'Markdown' },
                      { value: 'html', label: 'HTML' },
                      { value: 'pdf', label: 'PDF' },
                      { value: 'word', label: 'Word' }
                    ]}
                  />
                </Space>
              </Space>
            </div>

            <Divider>参数数据</Divider>

            <div style={{ marginBottom: 16 }}>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
                添加参数
              </Button>
            </div>

            <Table
              dataSource={parameters}
              columns={paramColumns}
              pagination={false}
              locale={{ emptyText: '请添加参数数据' }}
            />

            <Divider />

            <Space>
              <Button
                type="primary"
                icon={<FileTextOutlined />}
                onClick={handleGenerateReport}
                loading={generating}
                size="large"
              >
                生成报告
              </Button>
            </Space>

            {error && (
              <Alert
                message="错误"
                description={error}
                type="error"
                showIcon
                style={{ marginTop: 16 }}
                closable
              />
            )}
          </TabPane>

          <TabPane tab="数据对比报告" key="comparison">
            <Card type="inner" title="数据对比">
              <Alert
                message="功能开发中"
                description="数据对比报告功能即将推出，请先使用参数汇总报告功能。"
                type="info"
                showIcon
              />
            </Card>
          </TabPane>

          <TabPane tab="模拟结果报告" key="simulation">
            <Card type="inner" title="模拟结果报告">
              <Alert
                message="功能开发中"
                description="模拟结果报告功能即将推出，请先使用参数汇总报告功能。"
                type="info"
                showIcon
              />
            </Card>
          </TabPane>
        </Tabs>
      </Card>

      {reportContent && (
        <Card
          title={<Space><EyeOutlined />报告预览</Space>}
          extra={
            <Space>
              <Button icon={<DownloadOutlined />} onClick={handleDownload}>
                下载报告
              </Button>
            </Space>
          }
          style={{ marginTop: 16 }}
        >
          <pre style={{ background: '#f5f5f5', padding: 16, borderRadius: 4, maxHeight: 500, overflow: 'auto' }}>
            {reportContent}
          </pre>
        </Card>
      )}

      <Modal
        title="添加参数"
        open={modalVisible}
        onOk={handleAddParameter}
        onCancel={() => setModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="paramName" label="参数名" rules={[{ required: true, message: '请输入参数名' }]}>
            <Input placeholder="例如：温度" />
          </Form.Item>
          <Form.Item name="paramValue" label="参数值" rules={[{ required: true, message: '请输入参数值' }]}>
            <Input placeholder="例如：100" />
          </Form.Item>
          <Form.Item name="paramUnit" label="单位">
            <Input placeholder="例如：℃" />
          </Form.Item>
        </Form>
      </Modal>

      <Card
        title={<Space><FileTextOutlined />报告说明</Space>}
        style={{ marginTop: 16 }}
      >
        <ul>
          <li><Text>参数汇总报告：将提取的参数整理成结构化的报告文档</Text></li>
          <li><Text>支持多种输出格式：Markdown、HTML、PDF、Word</Text></li>
          <li><Text>报告内容由AI智能生成，自动整理参数信息</Text></li>
          <li><Text>可以下载报告文件保存到本地</Text></li>
        </ul>
      </Card>
    </div>
  )
}

export default ReportPanel
