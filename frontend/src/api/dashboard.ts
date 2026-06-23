/** Dashboard API 服务 */
import api from './index'

/** 统计数据 */
export interface DashboardStats {
  total_plans: number
  exported_count: number
  draft_count: number
  generated_count: number
  recent_activity_count: number
}

/** 方案概要 */
export interface PlanSummary {
  id: string
  title: string | null
  status: string
  suggested_style: string | null
  created_at: string
  updated_at: string
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  plans: T[]
  total: number
  page: number
  page_size: number
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
