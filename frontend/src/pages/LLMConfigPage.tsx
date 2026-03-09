import React, { useState, useEffect } from 'react'
import { 
  Card, 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  Select, 
  InputNumber, 
  message, 
  Tag, 
  Space, 
  Popconfirm,
  Divider,
  Alert
} from 'antd'
import { 
  PlusOutlined, 
  DeleteOutlined, 
  EditOutlined, 
  CheckCircleOutlined, 
  StopOutlined,
  ApiOutlined,
  KeyOutlined
} from '@ant-design/icons'
import { llmConfigAPI, LLMFactory, LLMModel, LLMConfig } from '../services/llmConfigApi'

const LLMConfigPage: React.FC = () => {
  const [factories, setFactories] = useState<LLMFactory[]>([])
  const [models, setModels] = useState<LLMModel[]>([])
  const [configs, setConfigs] = useState<LLMConfig[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingConfig, setEditingConfig] = useState<LLMConfig | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadFactories()
    loadConfigs()
  }, [])

  const loadFactories = async () => {
    try {
      const response = await llmConfigAPI.getFactories()
      setFactories(response.data.data || [])
    } catch (error) {
      message.error('加载LLM厂商失败')
    }
  }

  const loadConfigs = async () => {
    setLoading(true)
    try {
      const response = await llmConfigAPI.getMyConfigs()
      setConfigs(response.data.data || [])
    } catch (error) {
      message.error('加载配置失败')
    } finally {
      setLoading(false)
    }
  }

  const loadModels = async (factory: string) => {
    try {
      const response = await llmConfigAPI.getFactoryModels(factory)
      setModels(response.data.data || [])
    } catch (error) {
      message.error('加载模型列表失败')
    }
  }

  const handleFactoryChange = (value: string) => {
    loadModels(value)
    form.setFieldValue('llm_name', '')
    form.setFieldValue('model_type', '')
  }

  const handleModelChange = (value: string) => {
    const selectedModel = models.find(m => m.name === value)
    if (selectedModel) {
      form.setFieldValue('model_type', selectedModel.model_type)
    }
  }

  const handleAdd = () => {
    setEditingConfig(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: LLMConfig) => {
    setEditingConfig(record)
    form.setFieldsValue({
      llm_factory: record.llm_factory,
      llm_name: record.llm_name,
      model_type: record.model_type,
      api_key: '',
      api_base: record.api_base || '',
      api_version: record.api_version || '',
      max_tokens: record.max_tokens,
      temperature: record.temperature
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await llmConfigAPI.deleteConfig(id)
      message.success('配置已删除')
      loadConfigs()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleToggle = async (id: number) => {
    try {
      const response = await llmConfigAPI.toggleConfig(id)
      message.success(response.data.message)
      loadConfigs()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      
      if (editingConfig) {
        await llmConfigAPI.updateConfig(editingConfig.id, values)
        message.success('配置已更新')
      } else {
        await llmConfigAPI.createConfig(values)
        message.success('配置已创建')
      }
      
      setModalVisible(false)
      loadConfigs()
    } catch (error: any) {
      const errorDetail = error.response?.data?.detail
      const errorMessage = typeof errorDetail === 'string' ? errorDetail : '操作失败'
      message.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={status === '1' ? 'green' : 'default'}>
          {status === '1' ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '厂商',
      dataIndex: 'llm_factory',
      key: 'llm_factory',
      width: 120,
      render: (factory: string) => <Tag color="blue">{factory}</Tag>
    },
    {
      title: '模型',
      dataIndex: 'llm_name',
      key: 'llm_name',
      width: 200
    },
    {
      title: '类型',
      dataIndex: 'model_type',
      key: 'model_type',
      width: 100,
      render: (type: string) => (
        <Tag color={type === 'chat' ? 'purple' : 'cyan'}>{type}</Tag>
      )
    },
    {
      title: 'API地址',
      dataIndex: 'api_base',
      key: 'api_base',
      width: 150,
      ellipsis: true,
      render: (base: string) => base || '-'
    },
    {
      title: '最大Token',
      dataIndex: 'max_tokens',
      key: 'max_tokens',
      width: 100,
      align: 'center' as const
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: LLMConfig) => (
        <Space size="small">
          <Button 
            type="text" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
          />
          <Button 
            type="text" 
            icon={record.status === '1' ? <StopOutlined /> : <CheckCircleOutlined />} 
            onClick={() => handleToggle(record.id)}
            danger={record.status === '1'}
          />
          <Popconfirm
            title="确认删除此配置?"
            onConfirm={() => handleDelete(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div className="llm-config-page">
      <Card
        title={
          <Space>
            <ApiOutlined />
            <span>LLM 配置</span>
          </Space>
        }
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            添加配置
          </Button>
        }
      >
        <Alert
          message="配置说明"
          description="在此添加和管理您的LLM API配置。配置后，智能Agent、翻译、报告生成等功能将使用您配置的LLM。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        
        <Table
          columns={columns}
          dataSource={configs}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暂无配置，请点击添加按钮创建' }}
        />
      </Card>

      <Modal
        title={editingConfig ? '编辑LLM配置' : '添加LLM配置'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        confirmLoading={loading}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            max_tokens: 4096,
            temperature: 0.7,
            model_type: 'chat'
          }}
        >
          <Form.Item
            name="llm_factory"
            label="LLM厂商"
            rules={[{ required: true, message: '请选择LLM厂商' }]}
          >
            <Select 
              placeholder="选择LLM厂商"
              onChange={handleFactoryChange}
              options={factories.map(f => ({
                label: f.display_name,
                value: f.name
              }))}
            />
          </Form.Item>

          <Form.Item
            name="llm_name"
            label="模型"
            rules={[{ required: true, message: '请选择模型' }]}
          >
            <Select 
              placeholder="选择模型"
              onChange={handleModelChange}
              options={models.map(m => ({
                label: `${m.name} (${m.model_type}, ${m.max_tokens} tokens)`,
                value: m.name
              }))}
            />
          </Form.Item>

          <Form.Item
            name="model_type"
            label="模型类型"
            rules={[{ required: true, message: '请选择模型类型' }]}
          >
            <Select 
              placeholder="模型类型"
              options={[
                { label: 'Chat (对话)', value: 'chat' },
                { label: 'Embedding (嵌入)', value: 'embedding' },
                { label: 'Rerank (重排序)', value: 'rerank' }
              ]}
            />
          </Form.Item>

          <Divider><KeyOutlined /> API密钥</Divider>

          <Form.Item
            name="api_key"
            label="API Key"
            extra={editingConfig ? '留空则保持原有密钥' : '本地部署的 Ollama 和 LocalAI 不需要填写'}
          >
            <Input.Password 
              placeholder="输入API Key" 
            />
          </Form.Item>

          <Form.Item
            name="api_base"
            label="API Base URL (可选)"
            extra="对于OpenAI兼容接口或本地部署需要填写"
          >
            <Input 
              placeholder="如: https://api.openai.com/v1 或 http://localhost:11434" 
            />
          </Form.Item>

          <Form.Item
            name="api_version"
            label="API Version (可选)"
            extra="Azure OpenAI需要填写，如: 2024-02-15-preview"
          >
            <Input placeholder="API版本" />
          </Form.Item>

          <Divider>高级配置</Divider>

          <Form.Item
            name="max_tokens"
            label="最大Token数"
          >
            <InputNumber 
              min={100} 
              max={200000} 
              step={100}
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item
            name="temperature"
            label="Temperature (温度)"
          >
            <InputNumber 
              min={0} 
              max={2} 
              step={0.1}
              precision={1}
              style={{ width: '100%' }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default LLMConfigPage
