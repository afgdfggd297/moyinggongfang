/** Templates API 服务 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截 — 自动注入 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    console.log(`[Templates API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('[Templates API] 请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截
api.interceptors.response.use(
  (response) => {
    console.log(`[Templates API] 响应 ${response.status}`)
    return response
  },
  (error) => {
    console.error('[Templates API] 响应错误:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

/** 模板分类 */
export type TemplateCategory = 'all' | 'business' | 'academic' | 'creative' | 'minimal' | 'tech'

/** 模板数据 */
export interface Template {
  id: string
  name: string
  description: string
  category: TemplateCategory
  thumbnail_url: string
  preview_url: string
  style: string
  color_scheme: string
  page_count: number
  usage_count: number
  tags: string[]
}

/** 模板列表响应 */
export interface TemplateListResponse {
  items: Template[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/** 获取模板列表 */
export async function getTemplates(
  category?: TemplateCategory,
  page: number = 1,
  pageSize: number = 12
): Promise<TemplateListResponse> {
  const params: Record<string, string | number> = { page, page_size: pageSize }
  if (category && category !== 'all') {
    params.category = category
  }
  const { data } = await api.get<TemplateListResponse>('/templates', { params })
  return data
}

/** 获取模板详情 */
export async function getTemplate(id: string): Promise<Template> {
  const { data } = await api.get<Template>(`/templates/${id}`)
  return data
}
