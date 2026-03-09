import React, { useState, useEffect, useRef } from 'react'
import { Card, Input, Button, Spin, Tag, Divider, Alert, Typography, Space, Progress, Tabs, List, Badge, Statistic, Row, Col, Empty, Timeline, Modal, Upload, message } from 'antd'
import { RobotOutlined, SendOutlined, SettingOutlined, FileSearchOutlined, CheckCircleOutlined, CloseCircleOutlined, ThunderboltOutlined, DatabaseOutlined, BookOutlined, HistoryOutlined, UploadOutlined, FileImageOutlined, FilePdfOutlined, FileTextOutlined as FileTextIcon } from '@ant-design/icons'
import { agentAPI, ProcessRequest } from '../services/agentApi'
import agentAutomationAPI, { AgentExecuteResult } from '../services/agentAutomation'

const { TextArea } = Input
const { Title, Text } = Typography

interface Message {
  id: string
  content: string
  type: 'user' | 'bot'
  timestamp: Date
  files?: Array<{
    name: string
    url: string
    type: string
  }>
  attachments?: Array<{
    name: string
    type: string
    size: number
  }>
}

const getFileIcon = (fileName: string) => {
  const ext = fileName.split('.').pop()?.toLowerCase() || ''
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) {
    return <FileImageOutlined />
  } else if (['pdf'].includes(ext)) {
    return <FilePdfOutlined />
  } else {
    return <FileTextIcon />
  }
}

const AgentPanel: React.FC = () => {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const [activeTab, setActiveTab] = useState('1')

  const [skills, setSkills] = useState<any[]>([])
  const [loadingSkills, setLoadingSkills] = useState(false)

  const [agentResult, setAgentResult] = useState<AgentExecuteResult | null>(null)
  const [agentLoading, setAgentLoading] = useState(false)
  const [agentError, setAgentError] = useState<string | null>(null)

  const [executionHistory, setExecutionHistory] = useState<any[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)

  const [memoryStats, setMemoryStats] = useState<any>(null)
  const [loadingMemory, setLoadingMemory] = useState(false)

  // 聊天消息列表
  const [messages, setMessages] = useState<Message[]>([])
  const [attachments, setAttachments] = useState<Array<{name: string, type: string, size: number}>>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 自动滚动到最新消息
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (activeTab === '2') {
      loadSkills()
    } else if (activeTab === '3') {
      loadExecutionHistory()
    } else if (activeTab === '4') {
      loadMemoryStats()
    }
  }, [activeTab])

  const loadSkills = async () => {
    setLoadingSkills(true)
    try {
      const result = await agentAutomationAPI.getSkills()
      if (result.success) {
        setSkills(result.data || [])
      }
    } catch (err) {
      console.error('加载Skills失败:', err)
    } finally {
      setLoadingSkills(false)
    }
  }

  const loadExecutionHistory = async () => {
    setLoadingHistory(true)
    try {
      const result = await agentAutomationAPI.getExecutionHistory(undefined, 10)
      if (result.success) {
        setExecutionHistory(result.data || [])
      }
    } catch (err) {
      console.error('加载执行历史失败:', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  const loadMemoryStats = async () => {
    setLoadingMemory(true)
    try {
      const result = await agentAutomationAPI.getMemoryStats()
      if (result.success) {
        setMemoryStats(result.data)
      }
    } catch (err) {
      console.error('加载记忆统计失败:', err)
    } finally {
      setLoadingMemory(false)
    }
  }

  const handleFileUpload = (file: any) => {
    const mockFile = {
      name: file.name,
      type: file.type,
      size: file.size
    }
    setAttachments(prev => [...prev, mockFile])
    message.success(`文件 ${file.name} 上传成功`)
    return false
  }

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async () => {
    if (!input.trim() && attachments.length === 0) return

    // 添加用户消息
    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      type: 'user',
      timestamp: new Date(),
      attachments
    }
    setMessages(prev => [...prev, userMessage])

    setLoading(true)

    try {
      const request: ProcessRequest = {
        user_input: input,
        attachments: attachments.map(a => a.name)
      }

      const result = await agentAPI.process(request)

      // 添加机器人回复
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: result.response_text || '已处理您的请求',
        type: 'bot',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, botMessage])
    } catch (err: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: err.unifiedMessage || '处理请求失败，请稍后重试',
        type: 'bot',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
      setInput('')
      setAttachments([])
    }
  }

  const handleAgentExecute = async () => {
    if (!input.trim()) return

    setAgentLoading(true)
    setAgentError(null)
    setAgentResult(null)

    try {
      const result = await agentAutomationAPI.executeAgent({
        request: input,
        max_iterations: 20
      })

      setAgentResult(result)
    } catch (err: any) {
      setAgentError(err.message || 'Agent执行失败，请稍后重试')
    } finally {
      setAgentLoading(false)
    }
  }

  const handleUnderstandTask = async () => {
    if (!input.trim()) return

    setAgentLoading(true)
    setAgentError(null)
    setAgentResult(null)

    try {
      const result = await agentAutomationAPI.understandTask(input, 10)

      if (result.success) {
        Modal.info({
          title: '任务理解结果',
          width: 600,
          content: (
            <div>
              <p><strong>任务类型：</strong>{result.data.task_type}</p>
              <p><strong>所需Skills：</strong>{result.data.required_skills?.join(', ')}</p>
              <p><strong>置信度：</strong>{(result.data.confidence * 100).toFixed(1)}%</p>
              <p><strong>预估时间：</strong>{result.data.estimated_time}秒</p>
              <p><strong>执行步骤：</strong></p>
              <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4, maxHeight: 300, overflow: 'auto' }}>
                {JSON.stringify(result.data.steps, null, 2)}
              </pre>
            </div>
          ),
          onOk() {}
        })
      }
    } catch (err: any) {
      setAgentError(err.message || '任务理解失败')
    } finally {
      setAgentLoading(false)
    }
  }

  const taskExamples = [
    { text: '用DWSIM模拟一个乙醇精馏塔', type: 'simulation' },
    { text: '打开Excel文件并读取数据', type: 'excel' },
    { text: '用Aspen Plus计算物性参数', type: 'aspen' },
    { text: '在AutoCAD中绘制设备图纸', type: 'cad' }
  ]

  const tabItems = [
    {
      key: '1',
      label: <span><RobotOutlined />智能对话</span>,
      children: (
        <>
          <Card style={{ minHeight: 600, position: 'relative' }}>
            {/* 聊天头部 */}
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between', 
              padding: '16px 24px', 
              borderBottom: '1px solid #f0f0f0',
              marginBottom: 0
            }}>
              <Space>
                <RobotOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                <span style={{ fontSize: 18, fontWeight: 600 }}>智能Agent助手</span>
              </Space>
              <Space>
                <Button icon={<SettingOutlined />} size="small" />
              </Space>
            </div>

            {/* 消息列表 */}
            <div 
              style={{ 
                padding: '24px', 
                height: 400, 
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px'
              }}
            >
              {/* 欢迎消息 */}
              {messages.length === 0 && (
                <div style={{ textAlign: 'center', color: '#888', padding: '40px 0' }}>
                  <RobotOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                  <div style={{ fontSize: 16 }}>你好！我是你的智能化工助手</div>
                  <div style={{ fontSize: 14, marginTop: 8 }}>可以帮你处理文档、运行模拟、分析数据等</div>
                </div>
              )}

              {/* 消息 */}
              {messages.map((msg) => (
                <div 
                  key={msg.id} 
                  style={{
                    display: 'flex',
                    flexDirection: msg.type === 'user' ? 'row-reverse' : 'row',
                    alignItems: 'flex-start'
                  }}
                >
                  {/* 头像 */}
                  <div style={{
                    width: 36,
                    height: 36,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 8px'
                  }}>
                    {msg.type === 'user' ? (
                      <div style={{ background: '#1890ff', color: 'white', width: 36, height: 36, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>你</div>
                    ) : (
                      <div style={{ background: '#f0f0f0', width: 36, height: 36, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><RobotOutlined /></div>
                    )}
                  </div>

                  {/* 消息内容 */}
                  <div style={{
                    maxWidth: '70%',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}>
                    {/* 消息文本 */}
                    <div style={{
                      padding: '12px 16px',
                      borderRadius: msg.type === 'user' ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                      backgroundColor: msg.type === 'user' ? '#1890ff' : '#f5f5f5',
                      color: msg.type === 'user' ? 'white' : 'inherit'
                    }}>
                      {msg.content}
                    </div>

                    {/* 附件 */}
                    {msg.attachments && msg.attachments.length > 0 && (
                      <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px',
                        marginLeft: msg.type === 'user' ? '0' : '8px'
                      }}>
                        {msg.attachments.map((file, index) => (
                          <div key={index} style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '8px 12px',
                            borderRadius: '8px',
                            backgroundColor: msg.type === 'user' ? '#e6f7ff' : '#fafafa',
                            fontSize: 12
                          }}>
                            {getFileIcon(file.name)}
                            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {file.name}
                            </span>
                            <span style={{ color: '#888' }}>
                              {(file.size / 1024).toFixed(1)}KB
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* 时间戳 */}
                    <div style={{
                      fontSize: 12,
                      color: '#888',
                      textAlign: msg.type === 'user' ? 'right' : 'left',
                      marginTop: '4px'
                    }}>
                      {msg.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}

              {/* 加载状态 */}
              {loading && (
                <div style={{ textAlign: 'center', padding: '16px 0' }}>
                  <Spin size="small" />
                  <div style={{ marginTop: 8, fontSize: 12, color: '#888' }}>
                    正在思考...
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* 输入区域 */}
            <div style={{
              padding: '24px',
              borderTop: '1px solid #f0f0f0',
              position: 'sticky',
              bottom: 0,
              backgroundColor: 'white'
            }}>
              {/* 附件预览 */}
              {attachments.length > 0 && (
                <div style={{
                  display: 'flex',
                  gap: '8px',
                  marginBottom: '12px',
                  flexWrap: 'wrap'
                }}>
                  {attachments.map((file, index) => (
                    <div key={index} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '6px 12px',
                      borderRadius: '16px',
                      backgroundColor: '#f5f5f5',
                      fontSize: 12
                    }}>
                      {getFileIcon(file.name)}
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 200 }}>
                        {file.name}
                      </span>
                      <Button 
                        size="small" 
                        type="text" 
                        onClick={() => removeAttachment(index)}
                        style={{ color: '#ff4d4f' }}
                      >
                        ×
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {/* 输入框和按钮 */}
              <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
                {/* 文件上传 */}
                <Upload
                  beforeUpload={handleFileUpload}
                  showUploadList={false}
                  maxCount={5}
                >
                  <Button icon={<UploadOutlined />} size="small" />
                </Upload>

                {/* 输入框 */}
                <TextArea
                  rows={2}
                  placeholder="输入您的需求，例如：从这个PDF提取参数并生成报告，或者翻译这篇文档"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  style={{ flex: 1, resize: 'none' }}
                />

                {/* 发送按钮 */}
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleSubmit}
                  loading={loading}
                  disabled={!input.trim() && attachments.length === 0}
                  size="large"
                >
                  发送
                </Button>
              </div>
            </div>
          </Card>

          <Card
            title={<Space><RobotOutlined />使用说明</Space>}
            style={{ marginTop: 16 }}
          >
            <Title level={5}>支持的指令示例：</Title>
            <ul>
              <li><Text code>从这个PDF提取温度、压力参数</Text> - 参数提取</li>
              <li><Text code>翻译这篇文档到中文</Text> - 文档翻译</li>
              <li><Text code>生成一份参数汇总报告</Text> - 报告生成</li>
              <li><Text code>用Aspen Plus运行模拟</Text> - 模拟运行</li>
            </ul>
          </Card>
        </>
      ),
    },
    {
      key: '2',
      label: <span><ThunderboltOutlined />化工自动化</span>,
      children: (
        <>
          <Card
            title={
              <Space>
                <ThunderboltOutlined />
                <span>化工软件自动化Agent</span>
              </Space>
            }
          >
            <Alert
              message="智能化工软件操作"
              description="使用自然语言控制DWSIM、Aspen Plus、Excel、AutoCAD等化工软件"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <TextArea
              rows={3}
              placeholder="输入化工软件操作指令，例如：用DWSIM模拟一个乙醇精馏塔"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              style={{ marginBottom: 16 }}
            />

            <Space style={{ marginBottom: 16 }}>
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                onClick={handleAgentExecute}
                loading={agentLoading}
                disabled={agentLoading}
              >
                执行任务
              </Button>
              <Button
                icon={<FileSearchOutlined />}
                onClick={handleUnderstandTask}
                loading={agentLoading}
                disabled={agentLoading}
              >
                理解任务
              </Button>
            </Space>

            <div style={{ marginBottom: 16 }}>
              <Text type="secondary">快速示例：</Text>
              <Space wrap style={{ marginTop: 8 }}>
                {taskExamples.map((example, index) => (
                  <Tag
                    key={index}
                    color="blue"
                    style={{ cursor: 'pointer' }}
                    onClick={() => setInput(example.text)}
                  >
                    {example.text}
                  </Tag>
                ))}
              </Space>
            </div>

            {agentLoading && (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Spin size="large" />
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">正在执行化工软件操作...</Text>
                </div>
                <Progress percent={50} status="active" style={{ marginTop: 16, maxWidth: 400 }} />
              </div>
            )}

            {agentError && (
              <Alert
                message="执行错误"
                description={agentError}
                type="error"
                showIcon
                style={{ marginBottom: 16 }}
                closable
              />
            )}

            {agentResult && !agentLoading && (
              <Card size="small" title="执行结果">
                <Tag
                  color={agentResult.success ? 'success' : 'error'}
                  icon={agentResult.success ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                  style={{ marginBottom: 16 }}
                >
                  {agentResult.success ? '执行成功' : '执行失败'}
                </Tag>

                {agentResult.data && (
                  <>
                    <Row gutter={16} style={{ marginBottom: 16 }}>
                      <Col span={6}>
                        <Statistic
                          title="执行状态"
                          value={agentResult.data.status}
                          valueStyle={{ color: agentResult.data.status === 'completed' ? '#3f8600' : '#cf1322' }}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="执行步骤"
                          value={`${agentResult.data.steps_executed}/${agentResult.data.total_steps}`}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="执行时间"
                          value={agentResult.data.execution_time}
                          suffix="秒"
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="会话ID"
                          value={agentResult.data.session_id?.slice(0, 8) || 'N/A'}
                        />
                      </Col>
                    </Row>

                    {agentResult.data.step_results && agentResult.data.step_results.length > 0 && (
                      <div>
                        <Text strong>步骤详情：</Text>
                        <Timeline style={{ marginTop: 16 }}>
                          {agentResult.data.step_results.map((step: any, index: number) => (
                            <Timeline.Item
                              key={index}
                              color={step.success ? 'green' : 'red'}
                              dot={step.success ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                            >
                              <Card size="small" style={{ marginBottom: 8 }}>
                                <Text strong>{step.action}</Text>
                                <Tag color="blue">{step.skill}</Tag>
                                <Text type="secondary" style={{ marginLeft: 8 }}>
                                  {step.success ? '成功' : `失败: ${step.error}`}
                                </Text>
                                {step.result && (
                                  <div style={{ marginTop: 8 }}>
                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                      结果: {step.result.message || JSON.stringify(step.result)}
                                    </Text>
                                  </div>
                                )}
                              </Card>
                            </Timeline.Item>
                          ))}
                        </Timeline>
                      </div>
                    )}

                    {agentResult.data.final_result && (
                      <div style={{ marginTop: 16 }}>
                        <Divider orientation="left">最终结果</Divider>
                        <Card size="small" style={{ background: '#f0f5ff' }}>
                          <pre style={{ background: '#f0f5ff', padding: 12, borderRadius: 4, maxHeight: 400, overflow: 'auto' }}>
                            {JSON.stringify(agentResult.data.final_result, null, 2)}
                          </pre>
                        </Card>
                      </div>
                    )}
                  </>
                )}
              </Card>
            )}
          </Card>

          <Card
            title={<Space><BookOutlined />可用Skills</Space>}
            style={{ marginTop: 16 }}
            loading={loadingSkills}
          >
            {skills.length > 0 ? (
              <List
                grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4 }}
                dataSource={skills}
                renderItem={(skill: any) => (
                  <List.Item>
                    <Card
                      size="small"
                      hoverable
                      extra={
                        <Tag color={skill.is_enabled ? 'success' : 'default'}>
                          {skill.is_enabled ? '已启用' : '已禁用'}
                        </Tag>
                      }
                    >
                      <Card.Meta
                        title={skill.display_name}
                        description={
                          <div>
                            <Text type="secondary" ellipsis>{skill.description}</Text>
                            <div style={{ marginTop: 8 }}>
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                操作: {skill.actions?.length || 0}个
                              </Text>
                            </div>
                          </div>
                        }
                      />
                    </Card>
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="暂无Skills" />
            )}
          </Card>
        </>
      ),
    },
    {
      key: '3',
      label: <span><HistoryOutlined />执行历史</span>,
      children: (
        <>
          <Card
            title={
              <Space>
                <HistoryOutlined />
                <span>执行历史</span>
              </Space>
            }
            loading={loadingHistory}
          >
            {executionHistory.length > 0 ? (
              <List
                dataSource={executionHistory}
                renderItem={(item: any) => (
                  <List.Item>
                    <Card size="small" style={{ width: '100%' }}>
                      <List.Item.Meta
                        avatar={
                          <Badge
                            status={item.status === 'completed' ? 'success' : item.status === 'failed' ? 'error' : 'processing'}
                            text={item.status}
                          />
                        }
                        title={item.request}
                        description={
                          <Space>
                            <Text type="secondary">会话: {item.session_id?.slice(0, 8)}</Text>
                            <Text type="secondary">步骤: {item.steps_count}</Text>
                            <Text type="secondary">时间: {item.started_at}</Text>
                          </Space>
                        }
                      />
                    </Card>
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="暂无执行历史" />
            )}
          </Card>
        </>
      ),
    },
    {
      key: '4',
      label: <span><DatabaseOutlined />记忆系统</span>,
      children: (
        <>
          <Card
            title={
              <Space>
                <DatabaseOutlined />
                <span>Agent记忆系统</span>
              </Space>
            }
            loading={loadingMemory}
          >
            {memoryStats && (
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="会话数量"
                    value={memoryStats.sessions || 0}
                    prefix={<RobotOutlined />}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="知识条目"
                    value={memoryStats.knowledge_chunks || 0}
                    prefix={<BookOutlined />}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="执行记录"
                    value={memoryStats.execution_history?.length || 0}
                    prefix={<HistoryOutlined />}
                  />
                </Col>
              </Row>
            )}
          </Card>
        </>
      ),
    },
  ]

  return (
    <div className="agent-panel" style={{ padding: '24px' }}>
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
    </div>
  )
}

export default AgentPanel
