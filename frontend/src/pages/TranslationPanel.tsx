import React, { useState } from 'react'
import { Card, Input, Button, Select, Spin, Space, Divider, Alert, Typography, Upload, message } from 'antd'
import { TranslationOutlined, UploadOutlined, SwapOutlined, ClearOutlined, DownloadOutlined, CopyOutlined } from '@ant-design/icons'
import { translationAPI, TranslateRequest } from '../services/agentApi'

const { TextArea } = Input
const { Text } = Typography

const { Dragger } = Upload

const languages = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: '英文' },
  { value: 'ja', label: '日文' },
  { value: 'ko', label: '韩文' },
  { value: 'fr', label: '法文' },
  { value: 'de', label: '德文' },
  { value: 'es', label: '西班牙文' },
  { value: 'ru', label: '俄文' }
]

const styles = [
  { value: 'professional', label: '专业文档' },
  { value: 'technical', label: '技术文档' },
  { value: 'casual', label: '日常口语' }
]

const TranslationPanel: React.FC = () => {
  const [sourceText, setSourceText] = useState('')
  const [translatedText, setTranslatedText] = useState('')
  const [sourceLang, setSourceLang] = useState('auto')
  const [targetLang, setTargetLang] = useState('zh')
  const [style, setStyle] = useState('professional')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)

  const handleTranslate = async () => {
    if (!sourceText.trim()) {
      message.warning('请输入需要翻译的内容')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const request: TranslateRequest = {
        text: sourceText,
        source_lang: sourceLang,
        target_lang: targetLang,
        style: style
      }

      const result = await translationAPI.translate(request)
      setTranslatedText(result.translated_text)

      if (result.cached) {
        message.info('结果来自缓存')
      }
    } catch (err: any) {
      setError(err.unifiedMessage || '翻译失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const handleDocumentUpload = async (file: File) => {
    setUploading(true)
    setError(null)

    try {
      const result = await translationAPI.translateDocument(file, targetLang, style)
      setSourceText(`[文档内容: ${file.name}]`)
      setTranslatedText(result.translated_content)
      message.success('文档翻译完成')
    } catch (err: any) {
      setError(err.unifiedMessage || '文档翻译失败')
    } finally {
      setUploading(false)
    }

    return false
  }

  const handleSwap = () => {
    if (sourceLang !== 'auto') {
      setSourceLang(targetLang)
      setTargetLang(sourceLang)
      setSourceText(translatedText)
      setTranslatedText(sourceText)
    }
  }

  const handleClear = () => {
    setSourceText('')
    setTranslatedText('')
    setError(null)
  }

  const handleCopy = () => {
    if (translatedText) {
      navigator.clipboard.writeText(translatedText)
      message.success('已复制到剪贴板')
    }
  }

  const handleDownload = () => {
    if (translatedText) {
      const blob = new Blob([translatedText], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `translation_${targetLang}.txt`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  return (
    <div className="translation-panel" style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <TranslationOutlined />
            <span>文档翻译</span>
          </Space>
        }
      >
        <div className="translation-controls" style={{ marginBottom: 16 }}>
          <Space>
            <Select
              value={sourceLang}
              onChange={setSourceLang}
              style={{ width: 120 }}
              options={[{ value: 'auto', label: '自动检测' }, ...languages]}
            />
            <Button icon={<SwapOutlined />} onClick={handleSwap} />
            <Select
              value={targetLang}
              onChange={setTargetLang}
              style={{ width: 120 }}
              options={languages}
            />
            <Select
              value={style}
              onChange={setStyle}
              style={{ width: 120 }}
              options={styles}
            />
          </Space>
        </div>

        <div className="translation-container" style={{ display: 'flex', gap: 16 }}>
          <div className="source-section" style={{ flex: 1 }}>
            <Text strong>原文</Text>
            <TextArea
              rows={12}
              value={sourceText}
              onChange={(e) => setSourceText(e.target.value)}
              placeholder="输入需要翻译的文本，或拖拽文件到下方上传..."
              style={{ marginTop: 8 }}
            />
          </div>

          <div className="target-section" style={{ flex: 1 }}>
            <Text strong>译文</Text>
            <TextArea
              rows={12}
              value={translatedText}
              readOnly
              placeholder="翻译结果将显示在这里..."
              style={{ marginTop: 8 }}
            />
          </div>
        </div>

        <Divider />

        <div className="translation-actions">
          <Space>
            <Button
              type="primary"
              icon={<TranslationOutlined />}
              onClick={handleTranslate}
              loading={loading}
              size="large"
            >
              翻译
            </Button>
            <Button icon={<ClearOutlined />} onClick={handleClear}>
              清除
            </Button>
            <Button icon={<CopyOutlined />} onClick={handleCopy} disabled={!translatedText}>
              复制
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleDownload} disabled={!translatedText}>
              下载
            </Button>
          </Space>
        </div>

        {error && (
          <Alert
            message="翻译错误"
            description={error}
            type="error"
            showIcon
            style={{ marginTop: 16 }}
            closable
          />
        )}
      </Card>

      <Card
        title={<Space><UploadOutlined />文档上传翻译</Space>}
        style={{ marginTop: 16 }}
      >
        <Dragger
          accept=".pdf,.doc,.docx,.txt,.md"
          beforeUpload={handleDocumentUpload}
          showUploadList={false}
          disabled={uploading}
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域进行翻译</p>
          <p className="ant-upload-hint">
            支持 PDF、Word、TXT、Markdown 等格式
          </p>
        </Dragger>
        {uploading && (
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Spin />
            <div><Text type="secondary">正在翻译文档...</Text></div>
          </div>
        )}
      </Card>

      <Card
        title={<Space><TranslationOutlined />翻译说明</Space>}
        style={{ marginTop: 16 }}
      >
        <ul>
          <li><Text>支持多种语言互译：中文、英文、日文、韩文、法文、德文、西班牙文、俄文</Text></li>
          <li><Text>翻译风格：专业文档（适合化工领域）、技术文档、日常口语</Text></li>
          <li><Text>支持文档上传翻译，自动提取文档内容进行翻译</Text></li>
          <li><Text>翻译结果会自动缓存，相同内容再次翻译会更快</Text></li>
        </ul>
      </Card>
    </div>
  )
}

export default TranslationPanel
