/** PPT API 服务 - 支持流式输出 */
import api from './index'
import { API_TIMEOUT_LONG, API_TIMEOUT_STREAM } from '../config'
import type {
  PlanRequest,
  PlanResponse,
  ConfirmPlanRequest,
  GenerateResponse,
  EditRequest,
  ExportRequest,
  PPTResponse,
} from '../types/ppt'

/** 创建方案 */
export async function createPlan(req: PlanRequest): Promise<PlanResponse> {
  const { data } = await api.post<PlanResponse>('/ppt/plan', req, { timeout: API_TIMEOUT_LONG })
  return data
}

/** 编辑方案 */
export async function updatePlan(planId: string, updates: { title?: string; outline?: string[] }): Promise<PlanResponse> {
  const { data } = await api.post<PlanResponse>('/ppt/update-plan', { plan_id: planId, ...updates })
  return data
}

/** 确认方案并生成HTML（非流式） */
export async function confirmPlan(req: ConfirmPlanRequest): Promise<GenerateResponse> {
  const { data } = await api.post<GenerateResponse>('/ppt/confirm-plan', req, { timeout: API_TIMEOUT_LONG })
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
      } catch {
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
  const { data } = await api.post<PPTResponse>('/ppt/export', req, { timeout: API_TIMEOUT_LONG })
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

/** 单页重生成 */
export async function regenerateSlide(
  planId: string,
  slideIndex: number,
  userInstruction: string = ''
): Promise<{ plan_id: string; html_content: string; slide_index: number }> {
  const { data } = await api.post('/ppt/regenerate-slide', null, {
    params: { plan_id: planId, slide_index: slideIndex, user_instruction: userInstruction },
    timeout: API_TIMEOUT_STREAM,
  })
  return data
}
