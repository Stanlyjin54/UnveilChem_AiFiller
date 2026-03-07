import React, { useState } from 'react'
import { Upload, Button, Card, List, Typography, message, Spin, Tag, Space, Image } from 'antd'
import { UploadOutlined, PictureOutlined, DownloadOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import api from '../services/api'

const { Title, Text } = Typography

interface ImageAnalysisResult {
  chemical_structures: Array<{
    name: string
    formula: string
    confidence: number
    bounding_box: [number, number, number, number]
  }>
  process_elements: Array<{
    type: string
    description: string
    confidence: number
    bounding_box: [number, number, number, number]
  }>
  extracted_text: string
  image_preview_url: string
}

const ImageAnalyzer: React.FC = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [analyzing, setAnalyzing] = useState(false)
  const [results, setResults] = useState<ImageAnalysisResult | null>(null)
  const [previewImage, setPreviewImage] = useState<string>('')

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择图片')
      return
    }

    const formData = new FormData()
    formData.append('file', fileList[0] as any)

    setAnalyzing(true)
    try {
      const response = await api.post('/images/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      setResults(response.data)
      message.success('图片分析完成')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '分析失败')
    } finally {
      setAnalyzing(false)
    }
  }

  const uploadProps = {
    onRemove: (file: UploadFile) => {
      const index = fileList.indexOf(file)
      const newFileList = fileList.slice()
      newFileList.splice(index, 1)
      setFileList(newFileList)
      setResults(null)
    },
    beforeUpload: (file: File) => {
      const isImage = file.type.startsWith('image/')
      const isSupported = [
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
        'image/bmp'
      ].includes(file.type)

      if (!isImage || !isSupported) {
        message.error('请上传支持的图片格式（JPG、PNG、GIF、BMP）')
        return false
      }

      // 预览图片
      const reader = new FileReader()
      reader.onload = (e) => {
        setPreviewImage(e.target?.result as string)
      }
      reader.readAsDataURL(file)

      // 将File转换为UploadFile类型
      const uploadFile: UploadFile = {
        uid: `${Date.now()}`,
        name: file.name,
        size: file.size,
        type: file.type,
        originFileObj: file as any
      }

      setFileList([uploadFile])
      setResults(null)
      return false
    },
    fileList,
  }

  return (
    <div>
      <Title level={2}>图片解析</Title>
      <Text type="secondary">上传化工图片，识别化学结构和工艺流程图元素</Text>

      <Card style={{ marginTop: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Upload.Dragger {...uploadProps}>
            <p className="ant-upload-drag-icon">
              <PictureOutlined style={{ fontSize: 48, color: '#52c41a' }} />
            </p>
            <p className="ant-upload-text">点击或拖拽图片到此区域上传</p>
            <p className="ant-upload-hint">
              支持 JPG、PNG、GIF、BMP 格式的化工图片
            </p>
          </Upload.Dragger>

          {previewImage && (
            <div style={{ textAlign: 'center' }}>
              <Image
                src={previewImage}
                alt="预览图片"
                style={{ maxWidth: '300px', maxHeight: '200px', borderRadius: '8px' }}
                preview={false}
              />
            </div>
          )}

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
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>正在分析图片，请稍候...</div>
          </div>
        </Card>
      )}

      {results && !analyzing && (
        <div style={{ marginTop: 24 }}>
          <Card 
            title="分析结果" 
            extra={
              <Space>
                {results.image_preview_url && (
                  <Image
                    src={results.image_preview_url}
                    alt="分析结果预览"
                    width={100}
                    height={60}
                    style={{ borderRadius: '4px' }}
                  />
                )}
              </Space>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              {/* 化学结构识别 */}
              {results.chemical_structures.length > 0 && (
                <div>
                  <Title level={4}>化学结构识别</Title>
                  <List
                    grid={{ gutter: 16, column: 2 }}
                    dataSource={results.chemical_structures}
                    renderItem={(item) => (
                      <List.Item>
                        <Card size="small">
                          <Text strong>{item.name}</Text>
                          <br />
                          <Text code style={{ fontSize: '16px', color: '#1890ff' }}>
                            {item.formula}
                          </Text>
                          <br />
                          <Tag color="green">化学结构</Tag>
                          <Text type="secondary">置信度: {(item.confidence * 100).toFixed(1)}%</Text>
                        </Card>
                      </List.Item>
                    )}
                  />
                </div>
              )}

              {/* 工艺元素识别 */}
              {results.process_elements.length > 0 && (
                <div>
                  <Title level={4}>工艺元素识别</Title>
                  <List
                    grid={{ gutter: 16, column: 3 }}
                    dataSource={results.process_elements}
                    renderItem={(item) => (
                      <List.Item>
                        <Card size="small">
                          <Text strong>{item.type}</Text>
                          <br />
                          <Text type="secondary">{item.description}</Text>
                          <br />
                          <Tag color="orange">工艺元素</Tag>
                          <Text type="secondary">置信度: {(item.confidence * 100).toFixed(1)}%</Text>
                        </Card>
                      </List.Item>
                    )}
                  />
                </div>
              )}

              {/* 提取文本 */}
              {results.extracted_text && (
                <div>
                  <Title level={4}>提取文本</Title>
                  <Card>
                    <Text style={{ whiteSpace: 'pre-wrap' }}>{results.extracted_text}</Text>
                  </Card>
                </div>
              )}

              <Space>
                <Button type="primary" icon={<DownloadOutlined />}>
                  导出分析结果
                </Button>
                <Button>
                  重新分析
                </Button>
              </Space>
            </Space>
          </Card>
        </div>
      )}
    </div>
  )
}

export default ImageAnalyzer