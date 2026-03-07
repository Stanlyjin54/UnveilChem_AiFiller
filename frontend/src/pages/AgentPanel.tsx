import React, { useState, useEffect } from 'react'
import { Card, Input, Button, Spin, Tag, Divider, Alert, Typography, Space, Progress, Tabs, List, Badge, Statistic, Row, Col, Empty, Timeline, Modal } from 'antd'
import { RobotOutlined, SendOutlined, SettingOutlined, FileTextOutlined, TranslationOutlined, FileSearchOutlined, CheckCircleOutlined, CloseCircleOutlined, ThunderboltOutlined, DatabaseOutlined, BookOutlined, HistoryOutlined } from '@ant-design/icons'
import { agentAPI, ProcessRequest, AgentResponse, ExecutionPlan } from '../services/agentApi'
import agentAutomationAPI, { AgentExecuteResult } from '../services/agentAutomation'

const { TextArea } = Input
const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs

const intentIcons: Record<string, React.ReactNode> = {
  parameter_extraction: <FileSearchOutlined />,
  document_translation: <TranslationOutlined />,
  report_generation: <FileTextOutlined />,
  general_chat: <RobotOutlined />
}

const intentColors: Record<string, string> = {
  parameter_extraction: 'blue',
  document_translation: 'green',
  report_generation: 'purple',
  simulation_run: 'orange',
  software_operation: 'red',
  general_chat: 'default'
}

const AgentPanel: React.FC = () => {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<AgentResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [executing, setExecuting] = useState(false)
  const [executionProgress, setExecutionProgress] = useState(0)

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

  const handleSubmit = async () => {
    if (!input.trim()) return

    setLoading(true)
    setError(null)
    setResponse(null)

    try {
      const request: ProcessRequest = {
        user_input: input,
        attachments: []
      }

      const result = await agentAPI.process(request)
      setResponse(result)
    } catch (err: any) {
      setError(err.unifiedMessage || '处理请求失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const handleExecutePlan = async () => {
    if (!response?.execution_plan) return

    setExecuting(true)
    setExecutionProgress(0)

    try {
      await agentAPI.executePlan(response.execution_plan as ExecutionPlan)
      setExecutionProgress(100)
    } catch (err: any) {
      setError(err.unifiedMessage || '执行计划失败')
    } finally {
      setExecuting(false)
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

  return (
    <div className="agent-panel" style={{ padding: '24px' }}>
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab={<span><RobotOutlined />智能对话</span>} key="1">
          <Card
            title={
              <Space>
                <RobotOutlined />
                <span>智能Agent控制面板</span>
              </Space>
            }
            extra={
              <Space>
                <Button icon={<SettingOutlined />}>设置</Button>
              </Space>
            }
          >
            <div style={{ marginBottom: 24 }}>
              <TextArea
                rows={4}
                placeholder="输入您的需求，例如：从这个PDF提取参数并生成报告，或者翻译这篇文档"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                style={{ marginBottom: 16 }}
              />

              <Space>
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleSubmit}
                  loading={loading}
                  size="large"
                >
                  发送请求
                </Button>
              </Space>
            </div>

            {loading && (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Spin size="large" />
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">正在分析您的请求...</Text>
                </div>
              </div>
            )}

            {error && (
              <Alert
                message="错误"
                description={error}
                type="error"
                showIcon
                style={{ marginBottom: 24 }}
                closable
              />
            )}

            {response && !loading && (
              <div className="response-section">
                <Divider orientation="left">处理结果</Divider>

                <Card size="small" style={{ marginBottom: 16 }}>
                  <Space>
                    <Text strong>识别意图：</Text>
                    <Tag
                      color={intentColors[response.intent] || 'default'}
                      icon={intentIcons[response.intent]}
                    >
                      {response.intent}
                    </Tag>
                    <Text type="secondary">置信度：{(response.confidence * 100).toFixed(1)}%</Text>
                  </Space>
                </Card>

                {response.extracted_parameters && Object.keys(response.extracted_parameters).length > 0 && (
                  <Card size="small" title="提取的参数" style={{ marginBottom: 16 }}>
                    <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
                      {JSON.stringify(response.extracted_parameters, null, 2)}
                    </pre>
                  </Card>
                )}

                {response.suggested_actions && response.suggested_actions.length > 0 && (
                  <Card size="small" title="建议操作" style={{ marginBottom: 16 }}>
                    <Space wrap>
                      {response.suggested_actions.map((action, index) => (
                        <Tag key={index} color="blue">
                          {action.label}
                        </Tag>
                      ))}
                    </Space>
                  </Card>
                )}

                {response.execution_plan && (
                  <Card
                    size="small"
                    title="执行计划"
                    extra={
                      <Button
                        type="primary"
                        onClick={handleExecutePlan}
                        loading={executing}
                        disabled={executing}
                      >
                        {executing ? '执行中...' : '执行计划'}
                      </Button>
                    }
                  >
                    {executing && (
                      <Progress percent={executionProgress} status="active" style={{ marginBottom: 16 }} />
                    )}
                    <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
                      {JSON.stringify(response.execution_plan, null, 2)}
                    </pre>
                  </Card>
                )}

                {response.response_text && (
                  <Card size="small" title="响应" style={{ marginTop: 16 }}>
                    <Paragraph>{response.response_text}</Paragraph>
                  </Card>
                )}
              </div>
            )}
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
        </TabPane>

        <TabPane tab={<span><ThunderboltOutlined />化工自动化</span>} key="2">
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
        </TabPane>

        <TabPane tab={<span><HistoryOutlined />执行历史</span>} key="3">
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
        </TabPane>

        <TabPane tab={<span><DatabaseOutlined />记忆系统</span>} key="4">
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
        </TabPane>
      </Tabs>
    </div>
  )
}

export default AgentPanel
