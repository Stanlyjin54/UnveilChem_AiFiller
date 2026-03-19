import api from './api'

export interface ProcessRequest {
  user_input: string
  context?: Record<string, any>
  attachments?: string[]
  target_software?: string
  provider?: string
}

export interface AgentResponse {
  intent: string
  confidence: number
  extracted_parameters: Record<string, any>
  suggested_actions: Array<{ label: string; action: string }>
  execution_plan: Record<string, any>
  response_text?: string
}

export interface TranslateRequest {
  text: string
  source_lang?: string
  target_lang?: string
  style?: string
  provider?: string
}

export interface TranslateResponse {
  translated_text: string
  source_lang: string
  target_lang: string
  confidence: number
  cached?: boolean
}

export interface ReportRequest {
  report_type: string
  source_data: Record<string, any>
  template?: string
  format?: string
  title?: string
  custom_sections?: string[]
  provider?: string
}

export interface ReportResponse {
  report_id: string
  content: string
  format: string
  created_at: string
}

export interface ExecutionPlan {
  steps: Array<{
    id: string
    tool: string
    parameters: Record<string, any>
    dependencies?: string[]
  }>
}

export const agentAPI = {
  process: async (request: ProcessRequest): Promise<AgentResponse> => {
    const response = await api.post('/agent/process', request)
    return response.data.data
  },

  getIntents: async () => {
    const response = await api.get('/agent/intents')
    return response.data.data
  },

  executePlan: async (plan: ExecutionPlan) => {
    const response = await api.post('/agent/execute_plan', plan)
    return response.data.data
  }
}

export const translationAPI = {
  translate: async (request: TranslateRequest): Promise<TranslateResponse> => {
    const response = await api.post('/translation/translate', request)
    return response.data.data
  },

  translateDocument: async (
    file: File,
    targetLang: string = 'zh',
    style: string = 'professional',
    provider?: string
  ): Promise<{ translated_content: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('target_lang', targetLang)
    formData.append('style', style)
    if (provider) {
      formData.append('provider', provider)
    }

    const response = await api.post('/translation/document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data.data
  },

  translatePdfToWord: async (
    file: File,
    sourceLang: string = 'en',
    targetLang: string = 'zh'
  ): Promise<{ output_file: string; filename: string; message: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('source_lang', sourceLang)
    formData.append('target_lang', targetLang)

    const response = await api.post('/translation/pdf-to-word', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data.data
  },

  getLanguages: async () => {
    const response = await api.get('/translation/languages')
    return response.data.data
  },

  clearCache: async () => {
    const response = await api.post('/translation/cache/clear')
    return response.data
  }
}

export const reportAPI = {
  generate: async (request: ReportRequest): Promise<ReportResponse> => {
    const response = await api.post('/report/generate', request)
    return response.data.data
  },

  generateParameterSummary: async (
    parameters: Array<Record<string, any>>,
    title: string = '参数汇总报告'
  ): Promise<ReportResponse> => {
    const response = await api.post('/report/parameter_summary', { parameters, title })
    return response.data.data
  },

  generateComparison: async (
    dataItems: Array<Record<string, any>>,
    comparisonFields: string[],
    title: string = '数据对比报告'
  ): Promise<ReportResponse> => {
    const response = await api.post('/report/comparison', {
      data_items: dataItems,
      comparison_fields: comparisonFields,
      title
    })
    return response.data.data
  },

  getTemplates: async () => {
    const response = await api.get('/report/templates')
    return response.data.data
  },

  getFormats: async () => {
    const response = await api.get('/report/formats')
    return response.data.data
  }
}
