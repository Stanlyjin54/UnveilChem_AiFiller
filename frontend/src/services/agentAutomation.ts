import api from './api';

export interface Skill {
  name: string;
  display_name: string;
  keywords: string[];
  description: string;
  category: string;
  software_type: string;
  is_enabled: boolean;
  actions: SkillAction[];
}

export interface SkillAction {
  name: string;
  description: string;
  required_params: string[];
  optional_params: string[];
}

export interface ExecutionPlan {
  task_id: string;
  original_request: string;
  task_type: string;
  required_skills: string[];
  steps: ExecutionStep[];
  estimated_time: number;
  confidence: number;
  created_at: string;
}

export interface ExecutionStep {
  step_id: number;
  skill_name: string;
  action: string;
  parameters: Record<string, any>;
  depends_on: number[];
  description?: string;
}

export interface AgentExecuteRequest {
  request: string;
  session_id?: string;
  max_iterations?: number;
}

export interface AgentExecuteResult {
  success: boolean;
  data: {
    status: string;
    session_id: string;
    steps_executed: number;
    total_steps: number;
    execution_time: number;
    final_result: any;
    step_results: any[];
  };
  message: string;
}

export interface KnowledgeSearchResult {
  content: string;
  source_type: string;
  source_name: string;
  score: number;
}

export interface SessionInfo {
  session_id: string;
  created_at: string;
}

export interface MemoryStats {
  sessions: number;
  knowledge_chunks: number;
  execution_history: any;
}

export const agentAutomationAPI = {
  // 软件发现
  discoverSoftware: async (softwareType?: string) => {
    const params = softwareType ? `?software_type=${softwareType}` : '';
    const response = await api.get(`/automation/discover-software${params}`);
    return response.data;
  },

  getSoftwareStatus: async (softwareName: string) => {
    const response = await api.get(`/automation/software-status/${softwareName}`);
    return response.data;
  },

  registerDiscoveredSoftware: async (softwareName: string) => {
    const response = await api.post(`/automation/register-discovered-software/${softwareName}`);
    return response.data;
  },

  // Skills管理
  getSkills: async (category?: string, enabledOnly?: boolean) => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (enabledOnly) params.append('enabled_only', 'true');
    const response = await api.get(`/automation/skills?${params}`);
    return response.data;
  },

  getSkillDetail: async (skillName: string) => {
    const response = await api.get(`/automation/skills/${skillName}`);
    return response.data;
  },

  searchSkills: async (keyword: string) => {
    const response = await api.get(`/automation/skills/search/${keyword}`);
    return response.data;
  },

  toggleSkill: async (skillName: string, enabled: boolean) => {
    const response = await api.post(`/automation/skills/${skillName}/toggle?enabled=${enabled}`);
    return response.data;
  },

  // 任务理解
  understandTask: async (request: string, maxSteps: number = 10) => {
    const response = await api.post('/automation/understand-task', {
      request,
      max_steps: maxSteps
    });
    return response.data;
  },

  validatePlan: async (plan: ExecutionPlan) => {
    const response = await api.post('/automation/validate-plan', plan);
    return response.data;
  },

  getTaskTypes: async () => {
    const response = await api.get('/automation/task-types');
    return response.data;
  },

  // Agent执行
  executeAgent: async (req: AgentExecuteRequest) => {
    const response = await api.post('/automation/agent/execute', req);
    return response.data;
  },

  getAgentStatus: async (sessionId: string) => {
    const response = await api.get(`/automation/agent/status/${sessionId}`);
    return response.data;
  },

  listActiveAgents: async () => {
    const response = await api.get('/automation/agent/active');
    return response.data;
  },

  getExecutionHistory: async (sessionId?: string, limit: number = 10) => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (sessionId) params.append('session_id', sessionId);
    const response = await api.get(`/automation/agent/executions?${params}`);
    return response.data;
  },

  getExecutionDetail: async (recordId: string) => {
    const response = await api.get(`/automation/agent/execution/${recordId}`);
    return response.data;
  },

  // 记忆系统 - 会话
  createSession: async (userId?: number) => {
    const params = userId ? `?user_id=${userId}` : '';
    const response = await api.post(`/automation/memory/session${params}`);
    return response.data;
  },

  getSession: async (sessionId: string) => {
    const response = await api.get(`/automation/memory/session/${sessionId}`);
    return response.data;
  },

  addSessionMessage: async (sessionId: string, role: string, content: string) => {
    const response = await api.post(
      `/automation/memory/session/${sessionId}/message?role=${role}&content=${encodeURIComponent(content)}`
    );
    return response.data;
  },

  // 记忆系统 - 知识
  addKnowledge: async (
    sourceType: string,
    sourceName: string,
    content: string,
    keywords?: string[]
  ) => {
    const params = new URLSearchParams({
      source_type: sourceType,
      source_name: sourceName,
      content
    });
    if (keywords?.length) {
      params.append('keywords', keywords.join(','));
    }
    const response = await api.post(`/automation/memory/knowledge?${params}`);
    return response.data;
  },

  searchKnowledge: async (query: string, topK: number = 3) => {
    const response = await api.get(
      `/automation/memory/knowledge/search?query=${encodeURIComponent(query)}&top_k=${topK}`
    );
    return response.data;
  },

  // 记忆系统 - 统一搜索
  searchAllMemory: async (query: string) => {
    const response = await api.get(
      `/automation/memory/search?query=${encodeURIComponent(query)}`
    );
    return response.data;
  },

  // 记忆系统 - 统计
  getMemoryStats: async () => {
    const response = await api.get('/automation/memory/stats');
    return response.data;
  }
};

export default agentAutomationAPI;
