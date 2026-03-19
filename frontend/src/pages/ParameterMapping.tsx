import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Input, Select, Space, Typography, message, Modal, Form, Tag, Switch, Checkbox } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SaveOutlined, UndoOutlined, DownloadOutlined, UploadOutlined, FileTextOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography
const { Option } = Select
const { Item } = Form

interface ParameterMapping {
  id: string
  standard_parameter: string
  software_specific_parameter: string
  software_name: string
  adapter_type: string
  description: string
  enabled: boolean
  created_at: string
  updated_at: string
}

interface SoftwareInfo {
  name: string
  adapter_type: string
  supported_parameters: string[]
}

interface MappingTemplate {
  id: string
  name: string
  software_name: string
  adapter_type: string
  mappings: {
    standard_parameter: string
    software_specific_parameter: string
    description: string
  }[]
  description: string
}

const ParameterMapping: React.FC = () => {
  const [mappings, setMappings] = useState<ParameterMapping[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [templateModalVisible, setTemplateModalVisible] = useState(false)
  const [editingMapping, setEditingMapping] = useState<ParameterMapping | null>(null)
  const [form] = Form.useForm()
  const [softwareList, setSoftwareList] = useState<SoftwareInfo[]>([])
  const [filterSoftware, setFilterSoftware] = useState('')
  const [filterEnabled, setFilterEnabled] = useState<boolean | undefined>(undefined)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState<MappingTemplate | null>(null)
  const [selectedTemplateMappings, setSelectedTemplateMappings] = useState<string[]>([])

  // 预定义映射模板
  const mappingTemplates: MappingTemplate[] = [
    {
      id: '1',
      name: 'Aspen Plus 常用参数映射',
      software_name: 'Aspen Plus',
      adapter_type: 'aspen_plus',
      description: 'Aspen Plus 常用热力学参数映射模板',
      mappings: [
        { standard_parameter: 'temperature', software_specific_parameter: 'T', description: '温度参数映射' },
        { standard_parameter: 'pressure', software_specific_parameter: 'P', description: '压力参数映射' },
        { standard_parameter: 'flow_rate', software_specific_parameter: 'FLOW', description: '流量参数映射' },
        { standard_parameter: 'concentration', software_specific_parameter: 'CONC', description: '浓度参数映射' },
        { standard_parameter: 'volume', software_specific_parameter: 'VOL', description: '体积参数映射' },
        { standard_parameter: 'mass', software_specific_parameter: 'MASS', description: '质量参数映射' }
      ]
    },
    {
      id: '2',
      name: 'DWSIM 常用参数映射',
      software_name: 'DWSIM',
      adapter_type: 'dwsim',
      description: 'DWSIM 常用热力学参数映射模板',
      mappings: [
        { standard_parameter: 'temperature', software_specific_parameter: 'Temperature', description: '温度参数映射' },
        { standard_parameter: 'pressure', software_specific_parameter: 'Pressure', description: '压力参数映射' },
        { standard_parameter: 'flow_rate', software_specific_parameter: 'MolarFlow', description: '流量参数映射' },
        { standard_parameter: 'concentration', software_specific_parameter: 'Concentration', description: '浓度参数映射' },
        { standard_parameter: 'volume', software_specific_parameter: 'Volume', description: '体积参数映射' },
        { standard_parameter: 'mass', software_specific_parameter: 'Mass', description: '质量参数映射' }
      ]
    },
    {
      id: '3',
      name: 'ChemCAD 常用参数映射',
      software_name: 'ChemCAD',
      adapter_type: 'chemcad',
      description: 'ChemCAD 常用热力学参数映射模板',
      mappings: [
        { standard_parameter: 'temperature', software_specific_parameter: 'TEMP', description: '温度参数映射' },
        { standard_parameter: 'pressure', software_specific_parameter: 'PRES', description: '压力参数映射' },
        { standard_parameter: 'flow_rate', software_specific_parameter: 'FLOW', description: '流量参数映射' },
        { standard_parameter: 'concentration', software_specific_parameter: 'CONC', description: '浓度参数映射' },
        { standard_parameter: 'volume', software_specific_parameter: 'VOL', description: '体积参数映射' },
        { standard_parameter: 'mass', software_specific_parameter: 'MASS', description: '质量参数映射' }
      ]
    }
  ]

  // 获取映射列表
  const fetchMappings = async () => {
    setLoading(true)
    try {
      const response = await api.get('/automation/parameter-mappings')
      setMappings(response.data.mappings || [])
    } catch (error: any) {
      message.error(error.unifiedMessage || '获取映射列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取支持的软件列表
  const fetchSoftwareList = async () => {
    try {
      const response = await api.get('/automation/supported-software')
      if (response.data.supported_software) {
        // 模拟软件支持的参数列表
        const softwareInfo: SoftwareInfo[] = response.data.supported_software.map((software: string) => ({
          name: software,
          adapter_type: software,
          supported_parameters: ['temperature', 'pressure', 'flow_rate', 'concentration', 'volume', 'mass']
        }))
        setSoftwareList(softwareInfo)
      }
    } catch (error: any) {
      message.error(error.unifiedMessage || '获取软件列表失败')
    }
  }

  // 组件挂载时获取数据
  useEffect(() => {
    fetchMappings()
    fetchSoftwareList()
  }, [])

  // 过滤映射
  const filteredMappings = mappings.filter(mapping => {
    const matchesSoftware = !filterSoftware || mapping.software_name === filterSoftware
    const matchesEnabled = filterEnabled === undefined || mapping.enabled === filterEnabled
    const matchesSearch = !searchKeyword || 
      mapping.standard_parameter.toLowerCase().includes(searchKeyword.toLowerCase()) ||
      mapping.software_specific_parameter.toLowerCase().includes(searchKeyword.toLowerCase()) ||
      mapping.description.toLowerCase().includes(searchKeyword.toLowerCase())
    return matchesSoftware && matchesEnabled && matchesSearch
  })

  // 打开编辑模态框
  const openEditModal = (mapping?: ParameterMapping) => {
    if (mapping) {
      setEditingMapping(mapping)
      form.setFieldsValue(mapping)
    } else {
      setEditingMapping(null)
      form.resetFields()
    }
    setModalVisible(true)
  }

  // 保存映射
  const saveMapping = async (values: any) => {
    try {
      if (editingMapping) {
        // 更新现有映射
        await api.put(`/automation/parameter-mappings/${editingMapping.id}`, values)
        message.success('映射更新成功')
      } else {
        // 创建新映射
        await api.post('/automation/parameter-mappings', values)
        message.success('映射创建成功')
      }
      setModalVisible(false)
      fetchMappings()
    } catch (error: any) {
      message.error(error.unifiedMessage || '保存映射失败')
    }
  }

  // 删除映射
  const deleteMapping = async (id: string) => {
    try {
      await api.delete(`/automation/parameter-mappings/${id}`)
      message.success('映射删除成功')
      fetchMappings()
    } catch (error: any) {
      message.error(error.unifiedMessage || '删除映射失败')
    }
  }

  // 切换映射启用状态
  const toggleMappingEnabled = async (id: string, enabled: boolean) => {
    try {
      await api.patch(`/automation/parameter-mappings/${id}/toggle`, { enabled })
      message.success(`映射已${enabled ? '启用' : '禁用'}`)
      fetchMappings()
    } catch (error: any) {
      message.error(error.unifiedMessage || '切换状态失败')
    }
  }

  // 导出映射配置
  const exportMappings = () => {
    const dataStr = JSON.stringify(mappings, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `parameter_mappings_${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
    message.success('映射配置已导出')
  }

  // 导入映射配置
  const handleImport = (file: File) => {
    const reader = new FileReader()
    reader.onload = async (e) => {
      try {
        const importedMappings = JSON.parse(e.target?.result as string)
        if (Array.isArray(importedMappings)) {
          // 批量导入映射
          await api.post('/automation/parameter-mappings/batch', { mappings: importedMappings })
          message.success(`成功导入 ${importedMappings.length} 个映射配置`)
          fetchMappings()
        } else {
          message.error('导入文件格式错误')
        }
      } catch (error) {
        message.error('导入失败：文件格式错误')
      }
    }
    reader.readAsText(file)
    return false
  }

  // 打开模板选择模态框
  const openTemplateModal = () => {
    setTemplateModalVisible(true)
    setSelectedTemplate(null)
    setSelectedTemplateMappings([])
  }

  // 选择模板
  const handleTemplateSelect = (template: MappingTemplate) => {
    setSelectedTemplate(template)
    setSelectedTemplateMappings(template.mappings.map(m => m.standard_parameter))
  }

  // 切换模板映射项选择
  const toggleTemplateMapping = (param: string) => {
    setSelectedTemplateMappings(prev => {
      if (prev.includes(param)) {
        return prev.filter(p => p !== param)
      } else {
        return [...prev, param]
      }
    })
  }

  // 应用模板
  const applyTemplate = async () => {
    if (!selectedTemplate) return

    try {
      const mappingsToApply = selectedTemplate.mappings.filter(m => 
        selectedTemplateMappings.includes(m.standard_parameter)
      )

      if (mappingsToApply.length === 0) {
        message.warning('请至少选择一个映射项')
        return
      }

      // 转换为API所需格式
      const formattedMappings = mappingsToApply.map(m => ({
        standard_parameter: m.standard_parameter,
        software_specific_parameter: m.software_specific_parameter,
        software_name: selectedTemplate.software_name,
        adapter_type: selectedTemplate.adapter_type,
        description: m.description,
        enabled: true
      }))

      // 批量创建映射
      await api.post('/automation/parameter-mappings/batch', { mappings: formattedMappings })
      message.success(`成功应用 ${mappingsToApply.length} 个映射项`)
      setTemplateModalVisible(false)
      fetchMappings()
    } catch (error: any) {
      message.error(error.unifiedMessage || '应用模板失败')
    }
  }

  // 表格列定义
  const columns = [
    {
      title: '标准参数',
      dataIndex: 'standard_parameter',
      key: 'standard_parameter',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '软件特定参数',
      dataIndex: 'software_specific_parameter',
      key: 'software_specific_parameter',
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: '目标软件',
      dataIndex: 'software_name',
      key: 'software_name',
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '适配器类型',
      dataIndex: 'adapter_type',
      key: 'adapter_type',
      render: (text: string) => <Tag color="green">{text}</Tag>
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean, record: ParameterMapping) => (
        <Switch
          checked={enabled}
          onChange={(checked) => toggleMappingEnabled(record.id, checked)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ParameterMapping) => (
        <Space size="middle">
          <Button type="primary" icon={<EditOutlined />} onClick={() => openEditModal(record)}>
            编辑
          </Button>
          <Button danger icon={<DeleteOutlined />} onClick={() => deleteMapping(record.id)}>
            删除
          </Button>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <PlusOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
        <Title level={2}>参数映射配置</Title>
      </div>
      <Text type="secondary">管理标准参数到不同化学软件特定参数的映射关系</Text>

      {/* 筛选栏 */}
      <Card style={{ marginTop: 24, marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <Text strong>搜索：</Text>
            <Input
              placeholder="搜索标准参数、软件参数或描述"
              style={{ width: 250, marginLeft: 8 }}
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
            />
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
              {softwareList.map(software => (
                <Option key={software.name} value={software.name}>{software.name}</Option>
              ))}
            </Select>
          </div>
          <div>
            <Text strong>状态筛选：</Text>
            <Select
              value={filterEnabled}
              onChange={setFilterEnabled}
              style={{ width: 150, marginLeft: 8 }}
              placeholder="全部状态"
            >
              <Option value={undefined}>全部</Option>
              <Option value={true}>启用</Option>
              <Option value={false}>禁用</Option>
            </Select>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <Button icon={<FileTextOutlined />} onClick={openTemplateModal}>
              应用模板
            </Button>
            <Button icon={<UploadOutlined />} onClick={() => document.getElementById('import-file')?.click()}>
              导入配置
            </Button>
            <input
              type="file"
              id="import-file"
              accept=".json"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files && handleImport(e.target.files[0])}
            />
            <Button icon={<DownloadOutlined />} onClick={exportMappings}>
              导出配置
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => openEditModal()}>
              添加映射
            </Button>
          </div>
        </div>
      </Card>

      {/* 映射列表 */}
      <Card style={{ marginTop: 24 }}>
        <Table
          columns={columns}
          dataSource={filteredMappings}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          loading={loading}
          bordered
        />
      </Card>

      {/* 映射编辑模态框 */}
      <Modal
        title={editingMapping ? '编辑参数映射' : '添加参数映射'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={saveMapping}
        >
          <Item
            name="standard_parameter"
            label="标准参数名称"
            rules={[{ required: true, message: '请输入标准参数名称' }]}
          >
            <Input placeholder="例如：temperature" />
          </Item>

          <Item
            name="software_name"
            label="目标软件"
            rules={[{ required: true, message: '请选择目标软件' }]}
          >
            <Select placeholder="选择软件">
              {softwareList.map(software => (
                <Option key={software.name} value={software.name}>{software.name}</Option>
              ))}
            </Select>
          </Item>

          <Item
            name="adapter_type"
            label="适配器类型"
            rules={[{ required: true, message: '请选择适配器类型' }]}
          >
            <Select placeholder="选择适配器类型">
              {softwareList.map(software => (
                <Option key={software.adapter_type} value={software.adapter_type}>{software.adapter_type}</Option>
              ))}
            </Select>
          </Item>

          <Item
            name="software_specific_parameter"
            label="软件特定参数"
            rules={[{ required: true, message: '请输入软件特定参数' }]}
          >
            <Input placeholder="例如：T1" />
          </Item>

          <Item
            name="description"
            label="描述"
          >
            <Input.TextArea placeholder="参数映射的描述信息" rows={3} />
          </Item>

          <Item
            name="enabled"
            label="启用状态"
            valuePropName="checked"
          >
            <Switch defaultChecked />
          </Item>

          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 24 }}>
            <Button icon={<UndoOutlined />} onClick={() => setModalVisible(false)}>
              取消
            </Button>
            <Button type="primary" icon={<SaveOutlined />} htmlType="submit">
              保存
            </Button>
          </div>
        </Form>
      </Modal>

      {/* 模板选择模态框 */}
      <Modal
        title="应用参数映射模板"
        open={templateModalVisible}
        onCancel={() => setTemplateModalVisible(false)}
        footer={null}
        width={800}
      >
        <div style={{ display: 'flex', gap: 24 }}>
          {/* 模板列表 */}
          <div style={{ flex: 1, borderRight: '1px solid #f0f0f0', paddingRight: 16 }}>
            <Text strong>选择模板：</Text>
            <div style={{ marginTop: 16, maxHeight: 400, overflowY: 'auto' }}>
              {mappingTemplates.map(template => (
                <Card
                  key={template.id}
                  title={template.name}
                  size="small"
                  style={{ marginBottom: 16, cursor: 'pointer', border: selectedTemplate?.id === template.id ? '2px solid #1890ff' : '1px solid #f0f0f0' }}
                  onClick={() => handleTemplateSelect(template)}
                >
                  <div>
                    <Text type="secondary">软件：</Text>
                    <Tag color="blue">{template.software_name}</Tag>
                  </div>
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary">适配器：</Text>
                    <Tag color="green">{template.adapter_type}</Tag>
                  </div>
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary">描述：</Text>
                    <Text ellipsis>{template.description}</Text>
                  </div>
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary">映射项数量：</Text>
                    <Text>{template.mappings.length}</Text>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* 模板映射项选择 */}
          <div style={{ flex: 1, paddingLeft: 16 }}>
            <Text strong>选择映射项：</Text>
            {selectedTemplate ? (
              <div style={{ marginTop: 16, maxHeight: 400, overflowY: 'auto' }}>
                <Checkbox.Group
                  value={selectedTemplateMappings}
                  onChange={(values) => setSelectedTemplateMappings(values as string[])}
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {selectedTemplate.mappings.map(mapping => (
                      <Card key={mapping.standard_parameter} size="small">
                        <Checkbox value={mapping.standard_parameter} onChange={() => toggleTemplateMapping(mapping.standard_parameter)}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <div style={{ fontWeight: 'bold' }}>{mapping.standard_parameter}</div>
                              <div style={{ color: '#666', marginTop: 4 }}>{mapping.description}</div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                              <div style={{ color: '#1890ff' }}>{mapping.software_specific_parameter}</div>
                              <div style={{ fontSize: '12px', color: '#999', marginTop: 2 }}>软件参数</div>
                            </div>
                          </div>
                        </Checkbox>
                      </Card>
                    ))}
                  </Space>
                </Checkbox.Group>
              </div>
            ) : (
              <div style={{ marginTop: 16, padding: 24, textAlign: 'center', color: '#999', background: '#fafafa', borderRadius: 4 }}>
                <Text>请先选择一个模板</Text>
              </div>
            )}

            {/* 操作按钮 */}
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 24 }}>
              <Button onClick={() => setTemplateModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" onClick={applyTemplate} disabled={!selectedTemplate || selectedTemplateMappings.length === 0}>
                应用模板
              </Button>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default ParameterMapping