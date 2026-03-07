import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Button, Space, Tag, Progress, 
         Modal, Form, Input, Select, DatePicker, message, Descriptions,
         Timeline, Alert, Typography } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, ReloadOutlined,
         PlusOutlined, EyeOutlined, DeleteOutlined,
         CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import * as echarts from 'echarts';
import AutomationService, { Task, TaskResult, Statistics, ErrorReport, TaskStatus, TaskPriority } from '../services/automation';

const { Option } = Select;
const { Text } = Typography;

// 简单的折线图组件
const SimpleLineChart: React.FC<{ data: any[] }> = ({ data }) => {
  const chartRef = React.useRef<HTMLDivElement>(null);
  const chartInstance = React.useRef<any>(null);

  React.useEffect(() => {
    if (chartRef.current && data.length > 0) {
      if (chartInstance.current) {
        chartInstance.current.dispose();
      }
      
      chartInstance.current = echarts.init(chartRef.current);
      
      const option = {
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['completed', 'failed', 'running']
        },
        xAxis: {
          type: 'category',
          data: data.map(item => item.time)
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: 'completed',
            type: 'line',
            data: data.map(item => item.completed)
          },
          {
            name: 'failed',
            type: 'line',
            data: data.map(item => item.failed)
          },
          {
            name: 'running',
            type: 'line',
            data: data.map(item => item.running)
          }
        ]
      };
      
      chartInstance.current.setOption(option);
      
      return () => {
        if (chartInstance.current) {
          chartInstance.current.dispose();
        }
      };
    }
  }, [data]);

  return <div ref={chartRef} style={{ width: '100%', height: '300px' }} />;
};

const AutomationDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [errors, setErrors] = useState<ErrorReport[]>([]);
  const [taskModalVisible, setTaskModalVisible] = useState(false);
  const [resultModalVisible, setResultModalVisible] = useState(false);
  const [taskResult, setTaskResult] = useState<TaskResult | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  // 获取统计信息
  const fetchStatistics = async () => {
    try {
      const data = await AutomationService.getStatistics();
      setStatistics(data);
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  // 获取任务列表
  const fetchTasks = async () => {
    try {
      const data = await AutomationService.getAllTasks(1, 20);
      setTasks(data.tasks);
    } catch (error) {
      console.error('获取任务列表失败:', error);
      message.error('获取任务列表失败');
    }
  };

  // 获取错误报告
  const fetchErrors = async () => {
    try {
      const data = await AutomationService.getErrors(10);
      setErrors(data);
    } catch (error) {
      console.error('获取错误报告失败:', error);
    }
  };

  // 获取任务结果
  const fetchTaskResult = async (taskId: string) => {
    try {
      const data = await AutomationService.getTaskResult(taskId);
      setTaskResult(data);
      setResultModalVisible(true);
    } catch (error) {
      console.error('获取任务结果失败:', error);
      message.error('获取任务结果失败');
    }
  };

  // 提交新任务
  const submitTask = async (values: any) => {
    try {
      setLoading(true);
      const taskData = {
        name: values.name,
        target_software: values.target_software,
        parameters: values.parameters,
        priority: values.priority || TaskPriority.MEDIUM,
        scheduled_time: values.scheduled_time ? dayjs(values.scheduled_time).toISOString() : undefined
      };
      
      await AutomationService.submitTask(taskData);
      message.success('任务提交成功');
      setTaskModalVisible(false);
      fetchTasks();
      fetchStatistics();
    } catch (error) {
      console.error('提交任务失败:', error);
      message.error('提交任务失败');
    } finally {
      setLoading(false);
    }
  };

  // 取消任务
  const cancelTask = async (taskId: string) => {
    try {
      await AutomationService.cancelTask(taskId);
      message.success('任务已取消');
      fetchTasks();
      fetchStatistics();
    } catch (error) {
      console.error('取消任务失败:', error);
      message.error('取消任务失败');
    }
  };

  // 清除已完成任务
  const clearCompletedTasks = async () => {
    try {
      await AutomationService.clearCompletedTasks();
      message.success('已清除已完成任务');
      fetchTasks();
      fetchStatistics();
    } catch (error) {
      console.error('清除任务失败:', error);
      message.error('清除任务失败');
    }
  };

  // 获取状态标签颜色
  const getStatusColor = (status: TaskStatus) => {
    switch (status) {
      case TaskStatus.COMPLETED:
        return 'success';
      case TaskStatus.FAILED:
        return 'error';
      case TaskStatus.RUNNING:
        return 'processing';
      case TaskStatus.PENDING:
        return 'warning';
      default:
        return 'default';
    }
  };

  // 获取状态图标
  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case TaskStatus.COMPLETED:
        return <CheckCircleOutlined />;
      case TaskStatus.FAILED:
        return <CloseCircleOutlined />;
      case TaskStatus.RUNNING:
        return <ReloadOutlined spin />;
      case TaskStatus.PENDING:
        return <ClockCircleOutlined />;
      default:
        return <ClockCircleOutlined />;
    }
  };

  // 生成图表数据
  const generateChartData = () => {
    // 模拟数据生成
    const data = [];
    for (let i = 0; i < 7; i++) {
      data.push({
        time: dayjs().subtract(i, 'day').format('MM-DD'),
        completed: Math.floor(Math.random() * 20),
        failed: Math.floor(Math.random() * 5),
        running: Math.floor(Math.random() * 10)
      });
    }
    setChartData(data.reverse());
  };

  // 开始轮询
  const startPolling = () => {
    const interval = setInterval(() => {
      fetchTasks();
      fetchStatistics();
      fetchErrors();
    }, 5000); // 每5秒轮询一次
    
    setPollingInterval(interval);
  };

  // 停止轮询
  const stopPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
  };

  // 初始化
  useEffect(() => {
    fetchStatistics();
    fetchTasks();
    fetchErrors();
    generateChartData();
    startPolling();
    
    return () => {
      stopPolling();
    };
  }, []);

  // 任务表格列定义
  const taskColumns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 120,
      render: (text: string) => <code>{text.substring(0, 8)}...</code>
    },
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      width: 200
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: TaskStatus) => (
        <Tag icon={getStatusIcon(status)} color={getStatusColor(status)}>
          {status.toUpperCase()}
        </Tag>
      )
    },
    {
      title: '目标软件',
      dataIndex: 'target_software',
      key: 'target_software',
      width: 150,
      render: (software: string) => <Tag color="blue">{software.toUpperCase()}</Tag>
    },
    {
      title: '创建时间',
      dataIndex: 'created_time',
      key: 'created_time',
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: '重试次数',
      dataIndex: 'retry_count',
      key: 'retry_count',
      width: 100,
      render: (count: number) => count > 0 ? <Tag color="orange">{count}</Tag> : <span>0</span>
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: Task) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => fetchTaskResult(record.task_id)}
          >
            查看结果
          </Button>
          {record.status === TaskStatus.RUNNING && (
            <Button
              type="link"
              size="small"
              danger
              icon={<CloseCircleOutlined />}
              onClick={() => cancelTask(record.task_id)}
            >
              取消
            </Button>
          )}
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <h1>自动化仪表板</h1>
          <p>管理和监控软件自动化任务</p>
        </Col>
        <Col>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setTaskModalVisible(true)}
            >
              新建任务
            </Button>
            <Button
              icon={<DeleteOutlined />}
              onClick={clearCompletedTasks}
            >
              清除已完成
            </Button>
            <Button
              icon={pollingInterval ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={pollingInterval ? stopPolling : startPolling}
            >
              {pollingInterval ? '暂停轮询' : '开始轮询'}
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 统计卡片 */}
      {statistics && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总任务数"
                value={statistics.total_tasks}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="运行中"
                value={statistics.running_tasks}
                prefix={<ReloadOutlined spin={statistics.running_tasks > 0} />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已完成"
                value={statistics.completed_tasks}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="失败"
                value={statistics.failed_tasks}
                prefix={<CloseCircleOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 任务队列状态 */}
      {statistics && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={12}>
            <Card title="任务队列状态">
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>队列大小</span>
                  <span>{statistics.queue_size}</span>
                </div>
                <Progress 
                  percent={Math.min(statistics.queue_size * 10, 100)} 
                  status="active"
                />
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>平均执行时间</span>
                  <span>{statistics.average_execution_time}s</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>成功率</span>
                  <span>{statistics.success_rate}%</span>
                </div>
              </div>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="任务趋势">
              <SimpleLineChart data={chartData} />
            </Card>
          </Col>
        </Row>
      )}

      {/* 任务列表 */}
      <Card title="任务列表" style={{ marginBottom: 24 }}>
        <Table
          columns={taskColumns}
          dataSource={tasks}
          rowKey="task_id"
          pagination={false}
          loading={loading}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* 错误报告 */}
      {errors.length > 0 && (
        <Card title="最近错误报告" style={{ marginBottom: 24 }}>
          <Timeline>
            {errors.slice(0, 5).map((error, index) => (
              <Timeline.Item key={index} color="red">
                <Descriptions size="small" column={2}>
                  <Descriptions.Item label="任务ID">{error.task_id}</Descriptions.Item>
                  <Descriptions.Item label="时间">{dayjs(error.timestamp).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
                  <Descriptions.Item label="错误类型" span={2}>
                    <Tag color="red">{error.category}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="错误信息" span={2}>
                    <Text type="danger">{error.message}</Text>
                  </Descriptions.Item>
                </Descriptions>
              </Timeline.Item>
            ))}
          </Timeline>
        </Card>
      )}

      {/* 新建任务模态框 */}
      <Modal
        title="新建自动化任务"
        open={taskModalVisible}
        onCancel={() => setTaskModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form layout="vertical" onFinish={submitTask}>
          <Form.Item
            label="任务名称"
            name="name"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="请输入任务名称" />
          </Form.Item>
          
          <Form.Item
            label="目标软件"
            name="target_software"
            rules={[{ required: true, message: '请选择目标软件' }]}
          >
            <Select placeholder="请选择目标软件">
              <Option value="aspen_plus">Aspen Plus</Option>
              <Option value="hysys">HYSYS</Option>
              <Option value="chemcad">ChemCAD</Option>
              <Option value="proii">PRO/II</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            label="任务参数"
            name="parameters"
            rules={[{ required: true, message: '请输入任务参数' }]}
          >
            <Input.TextArea 
              rows={4} 
              placeholder="请输入JSON格式的任务参数"
            />
          </Form.Item>
          
          <Form.Item
            label="优先级"
            name="priority"
          >
            <Select defaultValue={TaskPriority.MEDIUM}>
              <Option value={TaskPriority.LOW}>低</Option>
              <Option value={TaskPriority.MEDIUM}>中</Option>
              <Option value={TaskPriority.HIGH}>高</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            label="计划执行时间"
            name="scheduled_time"
          >
            <DatePicker 
              showTime 
              format="YYYY-MM-DD HH:mm:ss"
              style={{ width: '100%' }}
            />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                提交任务
              </Button>
              <Button onClick={() => setTaskModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 任务结果模态框 */}
      <Modal
        title="任务执行结果"
        open={resultModalVisible}
        onCancel={() => setResultModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setResultModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {taskResult && (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="任务ID" span={2}>
              {taskResult.task_id}
            </Descriptions.Item>
            <Descriptions.Item label="执行状态">
              <Tag color={taskResult.success ? 'success' : 'error'}>
                {taskResult.status.toUpperCase()}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="执行时间">
              {taskResult.execution_time.toFixed(2)} 秒
            </Descriptions.Item>
            <Descriptions.Item label="消息">
              {taskResult.message}
            </Descriptions.Item>
            <Descriptions.Item label="设置的参数" span={2}>
              <pre style={{ background: '#f5f5f5', padding: '8px', borderRadius: '4px', maxHeight: '200px', overflow: 'auto' }}>
                {JSON.stringify(taskResult.parameters_set, null, 2)}
              </pre>
            </Descriptions.Item>
            {taskResult.error_details && (
              <Descriptions.Item label="错误详情" span={2}>
                <Alert 
                  message={taskResult.error_details}
                  type="error"
                  showIcon
                />
              </Descriptions.Item>
            )}
            {taskResult.output_files && taskResult.output_files.length > 0 && (
              <Descriptions.Item label="输出文件" span={2}>
                <ul>
                  {taskResult.output_files.map((file, index) => (
                    <li key={index}>
                      <a href={file} target="_blank" rel="noopener noreferrer">
                        {file}
                      </a>
                    </li>
                  ))}
                </ul>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default AutomationDashboard;