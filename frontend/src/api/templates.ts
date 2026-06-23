/** Templates API 服务 */
import api from './index'

/** 模板分类 */
export type TemplateCategory = 'all' | 'business' | 'academic' | 'creative' | 'minimal' | 'tech'

/** 模板数据 */
export interface Template {
  id: string
  name: string
  description: string | null
  category: string | null
  style: string | null
  color_scheme: string | null
  thumbnail_url: string | null
  is_system: boolean
  created_at: string
}

/** 模板列表响应 */
export interface TemplateListResponse {
  templates: Template[]
  total: number
  page: number
  page_size: number
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
