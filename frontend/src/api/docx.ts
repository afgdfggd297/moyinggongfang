/** DOCX API 服务 */
import api from './index'
import { API_TIMEOUT_LONG, API_TIMEOUT_STREAM } from '../config'

/** 文档方案请求 */
export interface DocxPlanRequest {
  text: string
  extra_info?: string
  enable_search?: boolean
}

/** 文档方案响应 */
export interface DocxPlanResponse {
  plan_id: string
  title: string
  outline: DocxOutlineItem[]
  suggested_style: string
  summary: string
  data_sources: DataSource[]
}

/** 大纲条目 */
export interface DocxOutlineItem {
  title: string
  content_type: string
  level: number
  details: string[]
}

/** 数据来源 */
export interface DataSource {
  title: string
  url: string
  summary: string
  is_trusted: boolean
}

/** 确认方案请求 */
export interface DocxConfirmRequest {
  plan_id: string
  style: string
  custom_style?: string
}

/** 生成响应 */
export interface DocxGenerateResponse {
  plan_id: string
  markdown_content: string
  title: string
}

/** 编辑请求 */
export interface DocxEditRequest {
  plan_id: string
  markdown_content: string
}

/** 导出请求 */
export interface DocxExportRequest {
  plan_id: string
  markdown_content: string
}

/** 通用响应 */
export interface DocxResponse {
  success: boolean
  message: string
  data?: Record<string, unknown>
}

/** 流式回调类型 */
export interface DocxStreamCallbacks {
  onStart?: (message: string) => void
  onChunk?: (content: string, fullContent: string) => void
  onDone?: (markdownContent: string, title: string) => void
  onError?: (message: string) => void
}

/** 创建文档方案 */
export async function createDocxPlan(req: DocxPlanRequest): Promise<DocxPlanResponse> {
  const { data } = await api.post<DocxPlanResponse>('/docx/plan', req, { timeout: API_TIMEOUT_LONG })
  return data
}

/** 确认方案并生成内容（非流式） */
export async function confirmDocxPlan(req: DocxConfirmRequest): Promise<DocxGenerateResponse> {
  const { data } = await api.post<DocxGenerateResponse>('/docx/confirm', req, { timeout: API_TIMEOUT_LONG })
  return data
}

/** 确认方案并生成内容（SSE流式输出） */
export async function confirmDocxPlanStream(
  req: DocxConfirmRequest,
  callbacks: DocxStreamCallbacks
): Promise<void> {
  const response = await fetch('/api/v1/docx/confirm/stream', {
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
            callbacks.onDone?.(event.markdown_content, event.title)
            break
          case 'error':
            callbacks.onError?.(event.message)
            break
        }
      } catch {
        console.warn('[DOCX API] 解析SSE事件失败:', line)
      }
    }
  }
}

/** 提交编辑后的HTML */
export async function editDocxHtml(req: DocxEditRequest): Promise<DocxGenerateResponse> {
  const { data } = await api.post<DocxGenerateResponse>('/docx/edit', req)
  return data
}

/** 导出DOCX */
export async function exportDocx(req: DocxExportRequest): Promise<DocxResponse> {
  const { data } = await api.post<DocxResponse>('/docx/export', req, { timeout: API_TIMEOUT_LONG })
  return data
}

/** 获取下载URL */
export function getDocxDownloadUrl(planId: string): string {
  return `/api/v1/docx/download/${planId}`
}

/** 获取HTML预览内容（Markdown → HTML） */
export async function getDocxHtml(planId: string): Promise<{ plan_id: string; html_content: string }> {
  const { data } = await api.get(`/docx/html/${planId}`)
  return data
}

/** 获取方案完整数据 */
export async function getDocxPlan(planId: string): Promise<DocxPlanResponse & { markdown_content: string }> {
  const { data } = await api.get(`/docx/plan/${planId}`)
  return data
}
