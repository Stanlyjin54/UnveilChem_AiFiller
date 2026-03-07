import React, { useState, useEffect } from 'react'
import { Upload, Button, Card, List, Typography, message, Spin, Tag, Space, Input, Popconfirm, Modal } from 'antd'
import { UploadOutlined, FileTextOutlined, DownloadOutlined, RobotOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import api from '../services/api'

const { Title, Text } = Typography

interface AnalysisResult {
  chemical_entities: Array<{
    text: string
    type: string
    confidence: number
    position?: { start: number; end: number }
  }>
  process_parameters: Array<{
    name: string
    value: string
    unit: string
    confidence: number
    position?: { start: number; end: number }
    original_text?: string
  }>
  extracted_text: string
  file_type: string
}

interface TranslationResult {
  success: boolean
  original_text: string
  translated_text: string
  source_lang: string
  target_lang: string
}

const DocumentAnalyzer: React.FC = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [analyzing, setAnalyzing] = useState(false)
  const [results, setResults] = useState<AnalysisResult | null>(null)
  const [highlightedRanges, setHighlightedRanges] = useState<Array<{start: number, end: number, type: 'chemical' | 'parameter'}>>([])
  const [selectedParameter, setSelectedParameter] = useState<string | null>(null)
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null)
  const [editingParameters, setEditingParameters] = useState<boolean>(false)
  const [editableParameters, setEditableParameters] = useState<any[]>([])
  const [editingEntities, setEditingEntities] = useState<boolean>(false)
  const [editableEntities, setEditableEntities] = useState<any[]>([])
  // 自动保存相关状态
  const [autoSaving, setAutoSaving] = useState(false)
  const [lastSavedTime, setLastSavedTime] = useState<Date | null>(null)
  
  // 翻译相关状态
  const [translating, setTranslating] = useState(false)
  const [translationResult, setTranslationResult] = useState<TranslationResult | null>(null)
  const [sourceLang, setSourceLang] = useState('en')
  const [targetLang, setTargetLang] = useState('zh')
  
  // 报告生成相关状态
  const [generatingReport, setGeneratingReport] = useState(false)
  const [reportTemplates, setReportTemplates] = useState<string[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState('')
  const [selectedFormat, setSelectedFormat] = useState('pdf')
  const [templatePreview, setTemplatePreview] = useState<string>('')
  const [previewLoading, setPreviewLoading] = useState(false)
  const [reportContent, setReportContent] = useState<{
    include_chemical_entities: boolean
    include_process_parameters: boolean
    include_extracted_text: boolean
    include_translation: boolean
  }>({
    include_chemical_entities: true,
    include_process_parameters: true,
    include_extracted_text: true,
    include_translation: false
  })
  
  // 自动化执行相关状态
  const [supportedSoftware, setSupportedSoftware] = useState<string[]>([])
  const [selectedSoftware, setSelectedSoftware] = useState('')
  const [automating, setAutomating] = useState(false)
  const [automationTaskId, setAutomationTaskId] = useState('')
  const [automationStatus, setAutomationStatus] = useState('')
  // 软件推荐相关状态
  const [recommendedSoftware, setRecommendedSoftware] = useState<string | null>(null)
  
  // 组件挂载时获取报告模板列表和支持的软件列表
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await api.get('/documents/report-templates')
        if (response.data.success) {
          setReportTemplates(response.data.templates)
          if (response.data.templates.length > 0) {
            setSelectedTemplate(response.data.templates[0])
            // 获取第一个模板的预览
            fetchTemplatePreview(response.data.templates[0])
          }
        }
      } catch (error: any) {
        message.error(error.unifiedMessage || '获取模板列表失败')
      }
    }

    // 获取模板预览
    const fetchTemplatePreview = async (templateName: string) => {
      if (!templateName) return

      setPreviewLoading(true)
      try {
        const response = await api.get(`/documents/report-templates/${templateName}/preview`)
        if (response.data.success) {
          setTemplatePreview(response.data.preview_content)
        }
      } catch (error: any) {
        message.error(error.unifiedMessage || '获取模板预览失败')
        setTemplatePreview('')
      } finally {
        setPreviewLoading(false)
      }
    }
    
    const fetchSupportedSoftware = async () => {
      try {
        const response = await api.get('/automation/supported-software')
        if (response.data) {
          setSupportedSoftware(response.data.supported_software)
          if (response.data.supported_software.length > 0) {
            setSelectedSoftware(response.data.supported_software[0])
          }
        }
      } catch (error: any) {
        message.error(error.unifiedMessage || '获取支持的软件列表失败')
      }
    }
    
    fetchTemplates()
    fetchSupportedSoftware()
  }, [])

  // 软件推荐逻辑
  useEffect(() => {
    if (!supportedSoftware.length || !results) {
      setRecommendedSoftware(null)
      return
    }
    
    // 基于简单规则推荐软件
    let recommended: string | null = null
    
    // 如果有工艺参数，优先推荐Aspen Plus
    if (results.process_parameters.length > 0 && supportedSoftware.includes('Aspen Plus')) {
      recommended = 'Aspen Plus'
    }
    // 如果有化学实体，优先推荐ChemDraw
    else if (results.chemical_entities.length > 0 && supportedSoftware.includes('ChemDraw')) {
      recommended = 'ChemDraw'
    }
    // 默认推荐DWSIM（如果可用）
    else if (supportedSoftware.includes('DWSIM')) {
      recommended = 'DWSIM'
    }
    // 否则推荐第一个可用软件
    else if (supportedSoftware.length > 0) {
      recommended = supportedSoftware[0]
    }
    
    setRecommendedSoftware(recommended)
  }, [supportedSoftware, results])

  const handleParameterClick = (parameter: any) => {
    setSelectedParameter(parameter.name)
    setSelectedEntity(null)
    
    if (parameter.original_text) {
      // 高亮显示原始文本
      highlightTextInDocument(parameter.original_text, 'parameter')
    } else if (parameter.position) {
      // 使用位置信息高亮
      highlightTextRange(parameter.position.start, parameter.position.end, 'parameter')
    } else {
      // 搜索文本中的参数值
      const searchText = `${parameter.value} ${parameter.unit}`
      highlightTextInDocument(searchText, 'parameter')
    }
    
    message.info(`已选择参数: ${parameter.name} = ${parameter.value} ${parameter.unit}`)
  }

  const handleChemicalEntityClick = (entity: any) => {
    setSelectedEntity(entity.text)
    setSelectedParameter(null)
    
    if (entity.position) {
      highlightTextRange(entity.position.start, entity.position.end, 'chemical')
    } else {
      highlightTextInDocument(entity.text, 'chemical')
    }
    
    message.info(`已选择化学实体: ${entity.text} (${entity.type})`)
  }

  const highlightTextInDocument = (searchText: string, type: 'chemical' | 'parameter', append: boolean = false) => {
    if (!results?.extracted_text) return
    
    const text = results.extracted_text
    const index = text.toLowerCase().indexOf(searchText.toLowerCase())
    
    if (index !== -1) {
      highlightTextRange(index, index + searchText.length, type, append)
    }
  }

  const highlightTextRange = (start: number, end: number, type: 'chemical' | 'parameter', append: boolean = false) => {
    if (!results?.extracted_text) return
    
    if (append) {
      // 添加到现有高亮范围
      setHighlightedRanges(prev => [...prev, { start, end, type }])
    } else {
      // 替换现有高亮范围
      setHighlightedRanges([{ start, end, type }])
    }
    
    // 滚动到高亮位置
    setTimeout(() => {
      const textElement = document.querySelector('.extracted-text-content')
      if (textElement) {
        textElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }, 100)
  }

  const clearHighlights = () => {
    setHighlightedRanges([])
    setSelectedParameter(null)
    setSelectedEntity(null)
  }

  // 批量高亮功能
  const handleBatchHighlight = (type: 'chemical' | 'parameter') => {
    if (!results) return
    
    // 清除现有高亮
    setHighlightedRanges([])
    
    if (type === 'parameter' && results.process_parameters.length > 0) {
      // 批量高亮所有参数
      results.process_parameters.forEach(parameter => {
        if (parameter.original_text) {
          highlightTextInDocument(parameter.original_text, 'parameter', true)
        } else if (parameter.position) {
          highlightTextRange(parameter.position.start, parameter.position.end, 'parameter', true)
        } else {
          const searchText = `${parameter.value} ${parameter.unit}`
          highlightTextInDocument(searchText, 'parameter', true)
        }
      })
      message.success(`已批量高亮 ${results.process_parameters.length} 个参数`)
    } else if (type === 'chemical' && results.chemical_entities.length > 0) {
      // 批量高亮所有化学实体
      results.chemical_entities.forEach(entity => {
        if (entity.position) {
          highlightTextRange(entity.position.start, entity.position.end, 'chemical', true)
        } else {
          highlightTextInDocument(entity.text, 'chemical', true)
        }
      })
      message.success(`已批量高亮 ${results.chemical_entities.length} 个化学实体`)
    }
  }

  const renderHighlightedText = () => {
    if (!results?.extracted_text) return null
    
    const text = results.extracted_text
    if (highlightedRanges.length === 0) {
      return <div className="extracted-text-content" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>{text}</div>
    }

    const elements: JSX.Element[] = []
    let lastEnd = 0

    highlightedRanges.forEach((range, index) => {
      // 添加高亮前的文本
      if (range.start > lastEnd) {
        elements.push(
          <span key={`text-${index}`}>{text.slice(lastEnd, range.start)}</span>
        )
      }
      
      // 添加高亮文本
      const backgroundColor = range.type === 'chemical' ? '#fff7e6' : '#e6f7ff'
      const borderColor = range.type === 'chemical' ? '#fa8c16' : '#1890ff'
      
      elements.push(
        <span
          key={`highlight-${index}`}
          style={{
            backgroundColor,
            border: `2px solid ${borderColor}`,
            borderRadius: '3px',
            padding: '2px 4px',
            fontWeight: 'bold'
          }}
        >
          {text.slice(range.start, range.end)}
        </span>
      )
      
      lastEnd = range.end
    })

    // 添加剩余文本
    if (lastEnd < text.length) {
      elements.push(
        <span key="text-final">{text.slice(lastEnd)}</span>
      )
    }

    return <div className="extracted-text-content" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>{elements}</div>
  }

  const startEditingParameters = () => {
    if (results?.process_parameters) {
      setEditableParameters(JSON.parse(JSON.stringify(results.process_parameters)))
      setEditingParameters(true)
    }
  }

  const saveParameterChanges = () => {
    if (results) {
      setResults({
        ...results,
        process_parameters: editableParameters
      })
      setEditingParameters(false)
      setLastSavedTime(new Date())
      message.success('参数修改已保存')
    }
  }

  const cancelParameterEdit = () => {
    setEditingParameters(false)
    setEditableParameters([])
  }

  const updateParameter = (index: number, field: string, value: any) => {
    const updated = [...editableParameters]
    updated[index] = { ...updated[index], [field]: value }
    setEditableParameters(updated)
  }

  // 自动保存参数修改
  useEffect(() => {
    if (!editingParameters || editableParameters.length === 0 || !results) return
    
    const timer = setTimeout(async () => {
      setAutoSaving(true)
      try {
        // 自动保存到results状态
        setResults(prev => {
          if (!prev) return prev
          return {
            ...prev,
            process_parameters: editableParameters
          }
        })
        setLastSavedTime(new Date())
      } finally {
        setAutoSaving(false)
      }
    }, 1500) // 1.5秒防抖
    
    return () => clearTimeout(timer)
  }, [editableParameters, editingParameters, results])

  // 自动保存化学实体修改
  useEffect(() => {
    if (!editingEntities || editableEntities.length === 0 || !results) return
    
    const timer = setTimeout(async () => {
      setAutoSaving(true)
      try {
        // 自动保存到results状态
        setResults(prev => {
          if (!prev) return prev
          return {
            ...prev,
            chemical_entities: editableEntities
          }
        })
        setLastSavedTime(new Date())
      } finally {
        setAutoSaving(false)
      }
    }, 1500) // 1.5秒防抖
    
    return () => clearTimeout(timer)
  }, [editableEntities, editingEntities, results])

  const addNewParameter = () => {
    const newParam = {
      name: '新参数',
      value: '',
      unit: '',
      confidence: 1.0,
      original_text: '',
      position: null
    }
    setEditableParameters([...editableParameters, newParam])
  }

  const deleteParameter = (index: number) => {
    const updated = editableParameters.filter((_, i) => i !== index)
    setEditableParameters(updated)
  }

  const startEditingEntities = () => {
    if (results?.chemical_entities) {
      setEditableEntities(JSON.parse(JSON.stringify(results.chemical_entities)))
      setEditingEntities(true)
    }
  }

  const saveEntityChanges = () => {
    if (results) {
      setResults({
        ...results,
        chemical_entities: editableEntities
      })
      setEditingEntities(false)
      message.success('化学实体修改已保存')
    }
  }

  const cancelEntityEdit = () => {
    setEditingEntities(false)
    setEditableEntities([])
  }

  const updateEntity = (index: number, field: string, value: any) => {
    const updated = [...editableEntities]
    updated[index] = { ...updated[index], [field]: value }
    setEditableEntities(updated)
  }

  const addNewEntity = () => {
    const newEntity = {
      text: '新实体',
      type: 'compound',
      confidence: 1.0,
      position: null
    }
    setEditableEntities([...editableEntities, newEntity])
  }

  const deleteEntity = (index: number) => {
    const updated = editableEntities.filter((_, i) => i !== index)
    setEditableEntities(updated)
  }

  const copyParametersToClipboard = () => {
    const parametersText = results?.process_parameters?.map(p => `${p.name}: ${p.value} ${p.unit}`).join('\n') || ''
    navigator.clipboard.writeText(parametersText)
    message.success('参数列表已复制到剪贴板')
  }

  const copyEntitiesToClipboard = () => {
    const entitiesText = results?.chemical_entities?.map(e => `${e.text} (${e.type})`).join('\n') || ''
    navigator.clipboard.writeText(entitiesText)
    message.success('化学实体列表已复制到剪贴板')
  }

  const exportResults = () => {
    if (!results) return
    
    const exportData = {
      chemical_entities: results.chemical_entities,
      process_parameters: results.process_parameters,
      extracted_text: results.extracted_text,
      file_type: results.file_type,
      export_time: new Date().toISOString()
    }
    
    const dataStr = JSON.stringify(exportData, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `document_analysis_${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
    
    message.success('分析结果已导出')
  }

  const handleTranslate = async () => {
    if (!results?.extracted_text) {
      message.warning('没有可翻译的文本')
      return
    }

    setTranslating(true)
    try {
      const response = await api.post('/documents/translate', {
        text: results.extracted_text,
        source_lang: sourceLang,
        target_lang: targetLang
      })
      setTranslationResult(response.data)
      message.success('文本翻译完成')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '翻译失败')
    } finally {
      setTranslating(false)
    }
  }

  const handleGenerateReport = async () => {
    if (!results) {
      message.warning('没有可用于生成报告的数据')
      return
    }

    if (!selectedTemplate) {
      message.warning('请选择报告模板')
      return
    }

    setGeneratingReport(true)
    try {
      const reportData = {
        chemical_entities: reportContent.include_chemical_entities ? results.chemical_entities : [],
        process_parameters: reportContent.include_process_parameters ? results.process_parameters : [],
        extracted_text: reportContent.include_extracted_text ? results.extracted_text : '',
        file_type: results.file_type,
        generated_at: new Date().toISOString(),
        translation_result: reportContent.include_translation ? translationResult : null
      }

      const response = await api.post('/documents/generate-report', {
        template_name: selectedTemplate,
        data: reportData,
        output_format: selectedFormat,
        content_options: reportContent
      })

      if (response.data.success) {
        // 创建下载链接
        const blob = new Blob([response.data.report_content], {
          type: selectedFormat === 'pdf' ? 'application/pdf' : 
                selectedFormat === 'word' ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' :
                'text/html'
        })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `report_${Date.now()}.${selectedFormat}`
        link.click()
        URL.revokeObjectURL(url)

        message.success('报告生成完成')
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '报告生成失败')
    } finally {
      setGeneratingReport(false)
    }
  }

  const handleAutomate = async () => {
    if (!results) {
      message.warning('没有可用于自动化执行的数据')
      return
    }

    if (!selectedSoftware) {
      message.warning('请选择目标软件')
      return
    }

    setAutomating(true)
    setAutomationStatus('开始自动化执行...')
    try {
      // 提取参数
      const parameters = {
        chemical_entities: results.chemical_entities,
        process_parameters: results.process_parameters,
        extracted_text: results.extracted_text,
        file_type: results.file_type
      }

      const response = await api.post('/automation/submit-task', {
        name: `自动化填写 - ${results.file_type}`,
        parameters: parameters,
        target_software: selectedSoftware,
        adapter_type: selectedSoftware,
        priority: 1
      })

      if (response.data.task_id) {
        setAutomationTaskId(response.data.task_id)
        setAutomationStatus(`自动化任务已提交，任务ID: ${response.data.task_id}`)
        message.success('自动化任务已提交')
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '自动化执行失败')
      setAutomationStatus('自动化执行失败')
    } finally {
      setAutomating(false)
    }
  }

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择文件')
      return
    }

    // 确认上传分析
    Modal.confirm({
      title: '确认开始分析',
      content: '开始分析后，系统将处理您的文档并提取化学实体和工艺参数。这可能需要几分钟时间，是否继续？',
      okText: '开始分析',
      cancelText: '取消',
      onOk: async () => {
        const formData = new FormData()
        // 使用原生File对象
        const fileObj = fileList[0].originFileObj as File
        formData.append('file', fileObj, fileObj.name)

        setAnalyzing(true)
        try {
          console.log('开始上传文件:', fileObj.name, fileObj.type)
          const response = await api.post('/documents/upload', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          })
          
          console.log('上传成功，响应:', response.data)
          setResults(response.data.analysis_result)
          message.success('文档分析完成')
        } catch (error: any) {
          console.error('上传失败:', error)
          if (error.response) {
            console.error('响应数据:', error.response.data)
            console.error('响应状态:', error.response.status)
            console.error('响应头:', error.response.headers)
            message.error(error.response?.data?.detail || '分析失败')
          } else if (error.request) {
            console.error('请求已发送但没有收到响应:', error.request)
            message.error('服务器无响应，请检查网络连接')
          } else {
            console.error('请求配置错误:', error.message)
            message.error('请求失败: ' + error.message)
          }
        } finally {
          setAnalyzing(false)
        }
      }
    })
  }

  const uploadProps = {
    onRemove: (file: UploadFile) => {
      const index = fileList.indexOf(file)
      const newFileList = fileList.slice()
      newFileList.splice(index, 1)
      setFileList(newFileList)
    },
    beforeUpload: (file: File) => {
      const isSupported = [
        // 文档格式
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain',
        // 图片格式
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/bmp',
        'image/tiff'
      ].includes(file.type)

      if (!isSupported) {
        message.error('不支持的文件格式')
        return false
      }

      // 将File转换为UploadFile类型
      const uploadFile: UploadFile = {
        uid: `${Date.now()}`,
        name: file.name,
        size: file.size,
        type: file.type,
        originFileObj: file as any
      }

      setFileList([...fileList, uploadFile])
      return false
    },
    fileList,
  }

  return (
    <div>
      <Title level={2}>文档解析</Title>
      <Text type="secondary">上传化工文档，自动提取工艺参数和化学信息</Text>

      <Card style={{ marginTop: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Upload.Dragger {...uploadProps}>
            <p className="ant-upload-drag-icon">
              <FileTextOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持 PDF、Word、Excel、TXT 格式的化工文档，以及 JPG、PNG、BMP、TIFF 格式的图片
            </p>
          </Upload.Dragger>

          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={handleUpload}
            loading={analyzing}
            disabled={fileList.length === 0}
            size="large"
          >
            开始分析
          </Button>
        </Space>
      </Card>

      {analyzing && (
        <Card style={{ marginTop: 24 }}>
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" tip="正在分析文档，这可能需要几分钟时间..." />
            <div style={{ marginTop: 16, color: '#666' }}>
              <div>📄 正在处理文档</div>
              <div>🔍 正在识别化学实体</div>
              <div>📊 正在提取工艺参数</div>
              <div>⏱️ 预计完成时间：根据文档大小而定</div>
            </div>
          </div>
        </Card>
      )}

      {results && !analyzing && (
        <div style={{ marginTop: 24 }}>
          <Card title="分析结果" extra={<Text type="secondary">文件类型: {results.file_type}</Text>}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              {/* 结果状态判断 */}
              {((results.chemical_entities && results.chemical_entities.length > 0) || 
                (results.process_parameters && results.process_parameters.length > 0) || 
                results.extracted_text) ? (
                <>
                  {/* 化学实体 */}
                  {(results.chemical_entities && results.chemical_entities.length > 0) ? (
                    <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <Title level={4}>化学实体识别</Title>
                    <Space>
                      {!editingEntities ? (
                        <>
                          <Button size="small" onClick={copyEntitiesToClipboard}>
                            复制列表
                          </Button>
                          <Button size="small" onClick={() => handleBatchHighlight('chemical')}>
                            批量高亮
                          </Button>
                          <Button size="small" type="primary" onClick={startEditingEntities}>
                            编辑
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button size="small" type="primary" onClick={addNewEntity}>
                            添加实体
                          </Button>
                          <Button size="small" onClick={cancelEntityEdit}>
                            取消
                          </Button>
                          <Button size="small" type="primary" onClick={saveEntityChanges}>
                            保存
                          </Button>
                        </>
                      )}
                    </Space>
                  </div>
                  <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
                    💡 {editingEntities ? '编辑模式下可修改实体信息，系统会自动保存' : '点击化学实体可在右侧文本中高亮显示对应位置'}
                    {editingEntities && (
                      <span style={{ marginLeft: 8 }}>
                        {autoSaving ? (
                          <Text type="warning">正在自动保存...</Text>
                        ) : lastSavedTime ? (
                          <Text type="success">最后保存: {lastSavedTime.toLocaleTimeString()}</Text>
                        ) : null}
                      </span>
                    )}
                  </Text>
                  <List
                    itemLayout="horizontal"
                    dataSource={editingEntities ? editableEntities : results.chemical_entities}
                    renderItem={(item, index) => (
                  <List.Item>
                    {editingEntities ? (
                      <Card size="small">
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <div style={{ display: 'flex', gap: 8 }}>
                            <Input
                              value={item.text}
                              onChange={(e) => updateEntity(index, 'text', e.target.value)}
                              placeholder="实体名称"
                              style={{ flex: 1 }}
                            />
                            <Input
                              value={item.type}
                              onChange={(e) => updateEntity(index, 'type', e.target.value)}
                              placeholder="类型"
                              style={{ width: 100 }}
                            />
                            <Popconfirm
                              title="确定要删除这个实体吗？"
                              onConfirm={() => deleteEntity(index)}
                              okText="确定"
                              cancelText="取消"
                            >
                              <Button size="small" danger>删除</Button>
                            </Popconfirm>
                          </div>
                          <div>
                            <Tag color="green">{Math.round(item.confidence * 100)}%</Tag>
                          </div>
                        </Space>
                      </Card>
                    ) : (
                      <Card 
                        size="small"
                        hoverable
                        onClick={() => handleChemicalEntityClick(item)}
                        style={{ 
                          cursor: 'pointer',
                          borderColor: selectedEntity === item.text ? '#52c41a' : undefined,
                          boxShadow: selectedEntity === item.text ? '0 0 0 2px rgba(82, 196, 26, 0.2)' : undefined
                        }}
                      >
                        <Text strong>{item.text}</Text>
                        <br />
                        <Text type="secondary">类型: {item.type}</Text>
                        <br />
                        <Tag color="green">{Math.round(item.confidence * 100)}%</Tag>
                      </Card>
                    )}
                  </List.Item>
                )}
                  />
                    </>
                  ) : (
                    <Card bordered={false} style={{ backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px' }}>
                        <div style={{ fontSize: '24px', color: '#52c41a' }}>📝</div>
                        <div>
                          <Title level={5} style={{ margin: 0 }}>未识别到化学实体</Title>
                          <Text type="secondary">系统未能从文档中识别出明确的化学实体。您可以尝试上传其他格式的文档，或手动添加化学实体。</Text>
                        </div>
                      </div>
                    </Card>
                  )}

              {/* 工艺参数 */}
              {(results.process_parameters && results.process_parameters.length > 0) ? (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <Title level={4}>工艺参数提取</Title>
                    <Space>
                      {!editingParameters ? (
                        <>
                          <Button size="small" onClick={copyParametersToClipboard}>
                            复制列表
                          </Button>
                          <Button size="small" onClick={() => handleBatchHighlight('parameter')}>
                            批量高亮
                          </Button>
                          <Button size="small" type="primary" onClick={startEditingParameters}>
                            编辑
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button size="small" type="primary" onClick={addNewParameter}>
                            添加参数
                          </Button>
                          <Button size="small" onClick={cancelParameterEdit}>
                            取消
                          </Button>
                          <Button size="small" type="primary" onClick={saveParameterChanges}>
                            保存
                          </Button>
                        </>
                      )}
                    </Space>
                  </div>
                  <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
                    💡 {editingParameters ? '编辑模式下可修改参数信息，系统会自动保存' : '点击工艺参数可在右侧文本中高亮显示对应位置'}
                    {editingParameters && (
                      <span style={{ marginLeft: 8 }}>
                        {autoSaving ? (
                          <Text type="warning">正在自动保存...</Text>
                        ) : lastSavedTime ? (
                          <Text type="success">最后保存: {lastSavedTime.toLocaleTimeString()}</Text>
                        ) : null}
                      </span>
                    )}
                  </Text>
                  <List
                    grid={{ gutter: 16, column: 2 }}
                    dataSource={editingParameters ? editableParameters : results.process_parameters}
                    renderItem={(item, index) => (
                    <List.Item>
                      {editingParameters ? (
                        <Card size="small">
                          <Space direction="vertical" style={{ width: '100%' }}>
                            <div style={{ display: 'flex', gap: 8 }}>
                              <Input
                                value={item.name}
                                onChange={(e) => updateParameter(index, 'name', e.target.value)}
                                placeholder="参数名称"
                                style={{ flex: 1 }}
                              />
                              <Input
                                value={item.value}
                                onChange={(e) => updateParameter(index, 'value', e.target.value)}
                                placeholder="数值"
                                style={{ width: 80 }}
                              />
                              <Input
                                value={item.unit}
                                onChange={(e) => updateParameter(index, 'unit', e.target.value)}
                                placeholder="单位"
                                style={{ width: 60 }}
                              />
                              <Popconfirm
                                title="确定要删除这个参数吗？"
                                onConfirm={() => deleteParameter(index)}
                                okText="确定"
                                cancelText="取消"
                              >
                                <Button size="small" danger>删除</Button>
                              </Popconfirm>
                            </div>
                            <div>
                              <Tag color="blue">{Math.round(item.confidence * 100)}%</Tag>
                            </div>
                          </Space>
                        </Card>
                      ) : (
                        <Card 
                          size="small"
                          hoverable
                          onClick={() => handleParameterClick(item)}
                          style={{ 
                            cursor: 'pointer',
                            borderColor: selectedParameter === item.name ? '#1890ff' : undefined,
                            boxShadow: selectedParameter === item.name ? '0 0 0 2px rgba(24, 144, 255, 0.2)' : undefined
                          }}
                        >
                          <Text strong>{item.name}</Text>
                          <br />
                          <Text style={{ fontSize: '18px', fontWeight: 'bold', color: '#1890ff' }}>
                            {item.value} {item.unit}
                          </Text>
                          <br />
                          <Text type="secondary">置信度: {(item.confidence * 100).toFixed(1)}%</Text>
                        </Card>
                      )}
                    </List.Item>
                  )}
                  />
                </>
                  ) : (
                    <Card bordered={false} style={{ backgroundColor: '#e6f7ff', border: '1px solid #91d5ff', borderRadius: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px' }}>
                        <div style={{ fontSize: '24px', color: '#1890ff' }}>📊</div>
                        <div>
                          <Title level={5} style={{ margin: 0 }}>未提取到工艺参数</Title>
                          <Text type="secondary">系统未能从文档中提取出明确的工艺参数。您可以尝试上传其他格式的文档，或手动添加工艺参数。</Text>
                        </div>
                      </div>
                    </Card>
                  )}

              {/* 提取文本 */}
              {results.extracted_text ? (
                <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                      <Title level={4}>提取文本</Title>
                      <Space>
                        <Button size="small" onClick={exportResults}>
                          导出结果
                        </Button>
                        {highlightedRanges.length > 0 && (
                          <Button onClick={clearHighlights} size="small">
                            清除高亮
                          </Button>
                        )}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <select 
                            value={sourceLang} 
                            onChange={(e) => setSourceLang(e.target.value)}
                            style={{ padding: '4px 8px', borderRadius: '4px', border: '1px solid #d9d9d9' }}
                          >
                            <option value="en">英语</option>
                            <option value="zh">中文</option>
                          </select>
                          <span style={{ color: '#999' }}>→</span>
                          <select 
                            value={targetLang} 
                            onChange={(e) => setTargetLang(e.target.value)}
                            style={{ padding: '4px 8px', borderRadius: '4px', border: '1px solid #d9d9d9' }}
                          >
                            <option value="zh">中文</option>
                            <option value="en">英语</option>
                          </select>
                          <Button 
                            size="small" 
                            type="primary" 
                            onClick={handleTranslate}
                            loading={translating}
                          >
                            翻译
                          </Button>
                        </div>
                      </Space>
                    </div>
                    <Card>
                      {renderHighlightedText()}
                    </Card>
                    {selectedParameter && (
                      <div style={{ marginTop: 16, padding: '12px', backgroundColor: '#e6f7ff', borderRadius: '6px' }}>
                        <Text type="secondary">当前选中参数：</Text>
                        <Text strong style={{ color: '#1890ff' }}>{selectedParameter}</Text>
                      </div>
                    )}
                    {selectedEntity && (
                      <div style={{ marginTop: 16, padding: '12px', backgroundColor: '#fff7e6', borderRadius: '6px' }}>
                        <Text type="secondary">当前选中化学实体：</Text>
                        <Text strong style={{ color: '#fa8c16' }}>{selectedEntity}</Text>
                      </div>
                    )}
                    
                    {/* 翻译结果显示 */}
                    {translationResult && translationResult.success && (
                      <Card style={{ marginTop: 24 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                          <Title level={4}>翻译结果</Title>
                          <Tag color={targetLang === 'zh' ? 'blue' : 'green'}>
                            {targetLang === 'zh' ? '中文' : 'English'}
                          </Tag>
                        </div>
                        <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', padding: '16px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                          {translationResult.translated_text}
                        </div>
                      </Card>
                    )}

                    {/* 报告生成区域 */}
                    <Card style={{ marginTop: 24 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                        <Title level={4}>报告生成</Title>
                      </div>
                      
                      {/* 报告内容选择器 */}
                      <div style={{ marginBottom: 24 }}>
                        <Text strong>报告内容：</Text>
                        <div style={{ marginTop: 12, display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                          <div>
                            <input
                              type="checkbox"
                              id="include_chemical_entities"
                              checked={reportContent.include_chemical_entities}
                              onChange={(e) => setReportContent(prev => ({ ...prev, include_chemical_entities: e.target.checked }))}
                              style={{ marginRight: 8 }}
                            />
                            <label htmlFor="include_chemical_entities">化学实体识别结果</label>
                          </div>
                          <div>
                            <input
                              type="checkbox"
                              id="include_process_parameters"
                              checked={reportContent.include_process_parameters}
                              onChange={(e) => setReportContent(prev => ({ ...prev, include_process_parameters: e.target.checked }))}
                              style={{ marginRight: 8 }}
                            />
                            <label htmlFor="include_process_parameters">工艺参数提取结果</label>
                          </div>
                          <div>
                            <input
                              type="checkbox"
                              id="include_extracted_text"
                              checked={reportContent.include_extracted_text}
                              onChange={(e) => setReportContent(prev => ({ ...prev, include_extracted_text: e.target.checked }))}
                              style={{ marginRight: 8 }}
                            />
                            <label htmlFor="include_extracted_text">提取文本</label>
                          </div>
                          <div>
                            <input
                              type="checkbox"
                              id="include_translation"
                              checked={reportContent.include_translation}
                              onChange={(e) => setReportContent(prev => ({ ...prev, include_translation: e.target.checked }))}
                              style={{ marginRight: 8 }}
                            />
                            <label htmlFor="include_translation">翻译结果</label>
                          </div>
                        </div>
                      </div>

                      {/* 模板选择和输出格式 */}
                      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', marginBottom: 24, flexWrap: 'wrap' }}>
                        <div style={{ flex: 1, minWidth: 300 }}>
                          <Text strong>选择模板：</Text>
                          <select 
                            value={selectedTemplate} 
                            onChange={(e) => {
                              setSelectedTemplate(e.target.value)
                              // 获取模板预览
                              const fetchTemplatePreview = async (templateName: string) => {
                                if (!templateName) return
                                setPreviewLoading(true)
                                try {
                                  const response = await api.get(`/documents/report-templates/${templateName}/preview`)
                                  if (response.data.success) {
                                    setTemplatePreview(response.data.preview_content)
                                  }
                                } catch (error: any) {
                                  message.error(error.response?.data?.detail || '获取模板预览失败')
                                  setTemplatePreview('')
                                } finally {
                                  setPreviewLoading(false)
                                }
                              }
                              fetchTemplatePreview(e.target.value)
                            }}
                            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9', width: '100%', marginTop: 8 }}
                          >
                            {reportTemplates.map((template) => (
                              <option key={template} value={template}>{template}</option>
                            ))}
                          </select>
                        </div>
                        <div style={{ width: 150 }}>
                          <Text strong>输出格式：</Text>
                          <select 
                            value={selectedFormat} 
                            onChange={(e) => setSelectedFormat(e.target.value)}
                            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9', width: '100%', marginTop: 8 }}
                          >
                            <option value="pdf">PDF</option>
                            <option value="word">Word</option>
                            <option value="html">HTML</option>
                          </select>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                          <Button 
                            type="primary" 
                            icon={<DownloadOutlined />}
                            onClick={handleGenerateReport}
                            loading={generatingReport}
                          >
                            生成报告
                          </Button>
                        </div>
                      </div>

                      {/* 模板预览 */}
                      <div style={{ marginTop: 24 }}>
                        <Text strong>模板预览：</Text>
                        <div style={{ marginTop: 12, padding: 16, backgroundColor: '#fafafa', borderRadius: 8, maxHeight: 300, overflowY: 'auto' }}>
                          {previewLoading ? (
                            <div style={{ textAlign: 'center', padding: '40px' }}>
                              <Spin size="small" />
                              <div style={{ marginTop: 8 }}>正在加载模板预览...</div>
                            </div>
                          ) : templatePreview ? (
                            <div dangerouslySetInnerHTML={{ __html: templatePreview }} />
                          ) : (
                            <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
                              暂无模板预览
                            </div>
                          )}
                        </div>
                      </div>

                      <Text type="secondary" style={{ marginTop: 16, display: 'block' }}>
                        💡 点击"生成报告"按钮，系统将根据当前分析结果生成报告文件。支持PDF、Word和HTML格式。
                      </Text>
                    </Card>

                    {/* 自动化执行区域 */}
                    <Card style={{ marginTop: 24 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                        <Title level={4}>自动化执行</Title>
                      </div>
                      <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 16 }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                            <Text strong>选择目标软件：</Text>
                            {recommendedSoftware && recommendedSoftware !== selectedSoftware && (
                              <Button 
                                type="link" 
                                size="small" 
                                onClick={() => setSelectedSoftware(recommendedSoftware)}
                                style={{ padding: 0, color: '#1890ff' }}
                              >
                                推荐: {recommendedSoftware}
                              </Button>
                            )}
                          </div>
                          <select 
                            value={selectedSoftware} 
                            onChange={(e) => setSelectedSoftware(e.target.value)}
                            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #d9d9d9', width: '100%' }}
                          >
                            {supportedSoftware.map((software) => (
                              <option 
                                key={software} 
                                value={software}
                                style={software === recommendedSoftware ? { backgroundColor: '#e6f7ff', borderColor: '#1890ff' } : {}}
                              >
                                {software} {software === recommendedSoftware && '(推荐)'}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <Button 
                            type="primary" 
                            icon={<RobotOutlined />}
                            onClick={handleAutomate}
                            loading={automating}
                            style={{ marginLeft: 16 }}
                          >
                            自动化填写
                          </Button>
                        </div>
                      </div>
                      {automationStatus && (
                        <div style={{ marginTop: 16, padding: '12px', backgroundColor: '#e6f7ff', borderRadius: '6px' }}>
                          <Text type="secondary">自动化状态：</Text>
                          <Text strong style={{ color: '#1890ff' }}>{automationStatus}</Text>
                          {automationTaskId && (
                            <div style={{ marginTop: 8 }}>
                              <Text type="secondary">任务ID：</Text>
                              <Text code>{automationTaskId}</Text>
                            </div>
                          )}
                        </div>
                      )}
                      <Text type="secondary" style={{ marginTop: 16, display: 'block' }}>
                        💡 点击"自动化填写"按钮，系统将根据当前分析结果自动填写到目标软件中。支持Aspen Plus、DWSIM等多种化工软件。
                      </Text>
                    </Card>
                </>
                  ) : (
                    <Card bordered={false} style={{ backgroundColor: '#fff7e6', border: '1px solid #ffd591', borderRadius: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px' }}>
                        <div style={{ fontSize: '24px', color: '#fa8c16' }}>📄</div>
                        <div>
                          <Title level={5} style={{ margin: 0 }}>未提取到文本内容</Title>
                          <Text type="secondary">系统未能从文档中提取出文本内容。您可以尝试上传其他格式的文档，或检查文档是否包含可提取的文本。</Text>
                        </div>
                      </div>
                    </Card>
                  )}
                </>
              ) : (
                <Card bordered={false} style={{ backgroundColor: '#f5f5f5', border: '1px solid #d9d9d9', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px' }}>
                    <div style={{ fontSize: '48px', color: '#999', marginBottom: 16 }}>📊</div>
                    <Title level={4} style={{ margin: 0, color: '#666' }}>未获取到分析结果</Title>
                    <Text type="secondary" style={{ marginTop: 16, textAlign: 'center', maxWidth: 500 }}>
                      系统已完成文档处理，但未能提取到任何化学实体、工艺参数或文本内容。
                      <br /><br />
                      建议：
                      <ul style={{ textAlign: 'left', marginTop: 8, marginBottom: 0 }}>
                        <li>检查文档格式是否正确</li>
                        <li>确保文档包含可识别的化学信息或工艺参数</li>
                        <li>尝试上传其他格式的文档</li>
                        <li>检查文档是否被加密或损坏</li>
                      </ul>
                    </Text>
                    <Button 
                      type="primary" 
                      style={{ marginTop: 24 }}
                      onClick={() => setFileList([])}
                    >
                      重新上传文档
                    </Button>
                  </div>
                </Card>
              )}
            </Space>
          </Card>
        </div>
      )}
    </div>
  )
}

export default DocumentAnalyzer