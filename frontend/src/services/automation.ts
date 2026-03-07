import api from './api';

// 任务状态枚举
export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

// 任务优先级枚举
export enum TaskPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent'
}

// 支持的软件类型
export enum SoftwareType {
  ASPEN_PLUS = 'aspen_plus',
  PRO_II = 'pro_ii',
  CHEMCAD = 'chemcad',
  DWSIM = 'dwsim',
  AUTOCAD = 'autocad',
  SOLIDWORKS = 'solidworks',
  EXCEL = 'excel'
}

// 任务接口
export interface Task {
  task_id: string;
  name: string;
  status: TaskStatus;
  target_software: SoftwareType;
  created_time: string;
  scheduled_time?: string;
  started_time?: string;
  completed_time?: string;
  retry_count: number;
  max_retries: number;
  priority: TaskPriority;
  error_message?: string;
  progress: number;
  parameters: Record<string, any>;
  user_id: string;
  result?: TaskResult;
}

// 任务结果接口
export interface TaskResult {
  task_id: string;
  success: boolean;
  status: TaskStatus;
  message: string;
  parameters_set: Record<string, any>;
  execution_time: number;
  error_details?: string;
  output_files?: string[];
  screenshots?: string[];
}

// 任务提交请求接口
export interface TaskSubmitRequest {
  name: string;
  target_software: SoftwareType;
  parameters: Record<string, any>;
  priority?: TaskPriority;
  scheduled_time?: string;
  max_retries?: number;
}

// 批量任务提交请求接口
export interface BatchTaskSubmitRequest {
  tasks: TaskSubmitRequest[];
  batch_name?: string;
}

// 错误报告接口
export interface ErrorReport {
  error_id: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  message: string;
  details: string;
  resolved: boolean;
  recovery_attempts: number;
  task_id?: string;
  user_id?: string;
  error_type?: string;
  error_message?: string;
}

// 统计信息接口
export interface Statistics {
  total_tasks: number;
  running_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  pending_tasks: number;
  queue_size: number;
  supported_adapters: string[];
  supported_software: string[];
  average_execution_time: number;
  success_rate: number;
}

// 适配器状态接口
export interface AdapterStatus {
  software_type: SoftwareType;
  is_connected: boolean;
  last_heartbeat: string;
  version?: string;
  capabilities: string[];
  error_rate: number;
  total_tasks: number;
  successful_tasks: number;
}

// 自动化服务类
export class AutomationService {
  // 提交单任务
  static async submitTask(taskData: TaskSubmitRequest): Promise<{ task_id: string; status: string }> {
    const response = await api.post('/automation/submit-task', {
      name: taskData.name,
      parameters: taskData.parameters,
      target_software: taskData.target_software,
      adapter_type: taskData.target_software, // 临时使用相同的软件类型作为适配器类型
      priority: taskData.priority || 1,
      scheduled_time: taskData.scheduled_time
    });
    return response.data;
  }

  // 批量提交任务
  static async submitBatchTasks(batchData: BatchTaskSubmitRequest): Promise<{ task_ids: string[]; total_tasks: number; status: string }> {
    const response = await api.post('/automation/batch-submit', {
      tasks: batchData.tasks,
      wait_for_completion: false
    });
    return response.data;
  }

  // 获取任务状态
  static async getTaskStatus(taskId: string): Promise<Task> {
    const response = await api.get(`/automation/task-status/${taskId}`);
    return response.data;
  }

  // 获取所有任务
  static async getAllTasks(page: number = 1, limit: number = 20, status?: TaskStatus): Promise<{ tasks: Task[]; total: number }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString()
    });
    
    if (status) {
      params.append('status', status);
    }
    
    const response = await api.get(`/automation/all-tasks?${params}`);
    return response.data;
  }

  // 获取任务结果
  static async getTaskResult(taskId: string): Promise<TaskResult> {
    const response = await api.get(`/automation/task-result/${taskId}`);
    return response.data;
  }

  // 取消任务
  static async cancelTask(taskId: string): Promise<{ message: string; task_id: string }> {
    const response = await api.post(`/automation/cancel-task/${taskId}`);
    return response.data;
  }

  // 清除已完成的任务
  static async clearCompletedTasks(): Promise<{ message: string }> {
    const response = await api.post('/automation/clear-completed');
    return response.data;
  }

  // 获取统计信息
  static async getStatistics(): Promise<Statistics> {
    const response = await api.get('/automation/statistics');
    return response.data;
  }

  // 获取错误报告
  static async getErrors(limit: number = 10, severity?: string): Promise<ErrorReport[]> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (severity) {
      params.append('severity', severity);
    }
    
    const response = await api.get(`/automation/errors?${params}`);
    return response.data;
  }

  // 获取适配器状态
  static async getAdapterStatuses(): Promise<AdapterStatus[]> {
    const response = await api.get('/automation/adapter-statuses');
    return response.data;
  }

  // 测试适配器连接
  static async testAdapterConnection(softwareType: SoftwareType): Promise<{ connected: boolean; message: string }> {
    const response = await api.post(`/automation/test-connection/${softwareType}`);
    return response.data;
  }

  // 获取支持的任务参数模板
  static async getTaskTemplates(): Promise<Record<SoftwareType, Record<string, any>>> {
    const response = await api.get('/automation/task-templates');
    return response.data;
  }

  // 验证任务参数
  static async validateTaskParameters(softwareType: SoftwareType, parameters: Record<string, any>): Promise<{ valid: boolean; errors: string[] }> {
    const response = await api.post('/automation/validate-parameters', {
      software_type: softwareType,
      parameters
    });
    return response.data;
  }

  // 获取任务执行历史
  static async getTaskHistory(taskId: string, limit: number = 10): Promise<any[]> {
    const response = await api.get(`/automation/task-history/${taskId}?limit=${limit}`);
    return response.data;
  }

  // 获取队列状态
  static async getQueueStatus(): Promise<{
    pending_tasks: number;
    running_tasks: number;
    queue_position: number;
    estimated_wait_time: number;
  }> {
    const response = await api.get('/automation/queue-status');
    return response.data;
  }

  // 清理已完成的任务
  static async cleanupTasks(retentionDays: number = 30): Promise<{ cleaned_count: number }> {
    const response = await api.post(`/automation/cleanup-tasks?retention_days=${retentionDays}`);
    return response.data;
  }

  // 导出任务报告
  static async exportTaskReport(taskIds: string[], format: 'csv' | 'xlsx' | 'json' = 'xlsx'): Promise<Blob> {
    const response = await api.post('/automation/export-report', {
      task_ids: taskIds,
      format
    }, {
      responseType: 'blob'
    });
    return response.data;
  }
}

export default AutomationService;