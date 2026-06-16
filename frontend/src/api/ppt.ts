/** PPT API 服务 - 支持流式输出 */
import axios from 'axios'
import type {
  PlanRequest,
  PlanResponse,
  ConfirmPlanRequest,
  GenerateResponse,
  EditRequest,
  ExportRequest,
  PPTResponse,
} from '../types/ppt'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 180000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data)
    return config
  },
  (error) => {
    console.error('[API] 请求错误:', error)
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => {
    console.log(`[API] 响应 ${response.status}:`, response.data)
    return response
  },
  (error) => {
    console.error('[API] 响应错误:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

/** 创建方案 */
export async function createPlan(req: PlanRequest): Promise<PlanResponse> {
  const { data } = await api.post<PlanResponse>('/ppt/plan', req)
  return data
}

/** 编辑方案 */
export async function updatePlan(planId: string, updates: { title?: string; outline?: string[] }): Promise<PlanResponse> {
  const { data } = await api.post<PlanResponse>('/ppt/update-plan', { plan_id: planId, ...updates })
  return data
}

/** 确认方案并生成HTML（非流式） */
export async function confirmPlan(req: ConfirmPlanRequest): Promise<GenerateResponse> {
  const { data } = await api.post<GenerateResponse>('/ppt/confirm-plan', req)
  return data
}

/** 流式回调类型 */
export interface StreamCallbacks {
  onStart?: (message: string) => void
  onChunk?: (content: string, fullContent: string) => void
  onDone?: (htmlContent: string, title: string) => void
  onError?: (message: string) => void
}

/** 确认方案并生成HTML（SSE流式输出） */
export async function confirmPlanStream(
  req: ConfirmPlanRequest,
  callbacks: StreamCallbacks
): Promise<void> {
  console.log('[API] 开始流式生成, plan_id:', req.plan_id)

  const response = await fetch('/api/v1/ppt/confirm-plan/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: '请求失败' }))
    callbacks.onError?.(err.detail || '请求失败')
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    callbacks.onError?.('无法读取响应流')
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''
  let fullContent = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const event = JSON.parse(line.slice(6))
        switch (event.type) {
          case 'start':
            callbacks.onStart?.(event.message)
            break
          case 'chunk':
            fullContent += event.content
            callbacks.onChunk?.(event.content, fullContent)
            break
          case 'done':
            callbacks.onDone?.(event.html_content, event.title)
            break
          case 'error':
            callbacks.onError?.(event.message)
            break
        }
      } catch (e) {
        console.warn('[API] 解析SSE事件失败:', line)
      }
    }
  }
}

/** 提交编辑后的HTML */
export async function editHtml(req: EditRequest): Promise<GenerateResponse> {
  const { data } = await api.post<GenerateResponse>('/ppt/edit', req)
  return data
}

/** 导出PPTX */
export async function exportPptx(req: ExportRequest): Promise<PPTResponse> {
  const { data } = await api.post<PPTResponse>('/ppt/export', req)
  return data
}

/** 获取下载URL */
export function getDownloadUrl(planId: string): string {
  return `/api/v1/ppt/download/${planId}`
}

/** 获取HTML内容 */
export async function getHtml(planId: string): Promise<{ plan_id: string; html_content: string }> {
  const { data } = await api.get(`/ppt/html/${planId}`)
  return data
}

/** 获取方案完整数据 */
export async function getPlan(planId: string): Promise<PlanResponse & { html_content: string }> {
  const { data } = await api.get(`/ppt/plan/${planId}`)
  return data
}
