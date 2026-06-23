/** Dashboard API 服务 */
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
    console.log(`[Dashboard API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('[Dashboard API] 请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截
api.interceptors.response.use(
  (response) => {
    console.log(`[Dashboard API] 响应 ${response.status}`)
    return response
  },
  (error) => {
    console.error('[Dashboard API] 响应错误:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

/** 统计数据 */
export interface DashboardStats {
  total_plans: number
  exported_count: number
  templates_count: number
}

/** 方案概要 */
export interface PlanSummary {
  plan_id: string
  title: string
  status: string
  created_at: string
  updated_at: string
  page_count: number
  style: string
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/** 获取统计数据 */
export async function getStats(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>('/dashboard/stats')
  return data
}

/** 获取最近方案 */
export async function getRecentPlans(): Promise<PlanSummary[]> {
  const { data } = await api.get<PlanSummary[]>('/dashboard/recent')
  return data
}

/** 获取方案列表（分页） */
export async function getPlans(page: number = 1, pageSize: number = 12): Promise<PaginatedResponse<PlanSummary>> {
  const { data } = await api.get<PaginatedResponse<PlanSummary>>('/dashboard/plans', {
    params: { page, page_size: pageSize },
  })
  return data
}

/** 删除方案 */
export async function deletePlan(planId: string): Promise<void> {
  await api.delete(`/dashboard/plans/${planId}`)
}

/** 重命名方案 */
export async function renamePlan(planId: string, title: string): Promise<void> {
  await api.put(`/dashboard/plans/${planId}/title`, { title })
}

/** 复制方案 */
export async function duplicatePlan(planId: string): Promise<PlanSummary> {
  const { data } = await api.post<PlanSummary>(`/dashboard/plans/${planId}/duplicate`)
  return data
}
