import api from './api'

export interface LLMFactory {
  name: string
  display_name: string
  tags: string[]
}

export interface LLMModel {
  name: string
  model_type: string
  max_tokens: number
}

export interface LLMConfig {
  id: number
  tenant_id: number
  llm_factory: string
  llm_name: string
  model_type: string
  api_key?: string
  api_base: string
  api_version: string
  max_tokens: number
  temperature: number
  status: string
  is_valid: boolean
  used_tokens: number
  created_at: string
  updated_at: string
}

export const llmConfigAPI = {
  getFactories: () => api.get<any, any>('/llm/factories'),
  
  getFactoryModels: (factory: string) => api.get<any, any>(`/llm/factories/${factory}/models`),
  
  getMyConfigs: () => api.get<any, any>('/llm/configs'),
  
  createConfig: (config: {
    llm_factory: string
    llm_name: string
    model_type: string
    api_key: string
    api_base?: string
    api_version?: string
    max_tokens?: number
    temperature?: number
  }) => api.post<any, any>('/llm/configs', config),
  
  updateConfig: (configId: number, config: Partial<LLMConfig>) => 
    api.put<any, any>(`/llm/configs/${configId}`, config),
  
  deleteConfig: (configId: number) => 
    api.delete<any, any>(`/llm/configs/${configId}`),
  
  toggleConfig: (configId: number) => 
    api.post<any, any>(`/llm/configs/${configId}/toggle`),
  
  getValidConfigs: () => api.get<any, any>('/llm/configs/valid'),
  
  testConfig: (configId: number) => 
    api.post<any, any>(`/llm/configs/${configId}/test`),
}
