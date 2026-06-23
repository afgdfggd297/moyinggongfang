/** PPT 相关类型定义 */

/** 方案请求 */
export interface PlanRequest {
  text: string
  extra_info?: string
  enable_search?: boolean
}

/** 数据来源 */
export interface DataSource {
  title: string
  url: string
  summary: string
  is_trusted: boolean
}

/** 大纲条目 */
export interface OutlineItem {
  title: string
  details: string[]
}

/** 方案响应 */
export interface PlanResponse {
  plan_id: string
  title: string
  outline: OutlineItem[]
  suggested_pages: number
  suggested_style: string
  summary: string
  data_sources: DataSource[]
}

/** 确认方案请求 */
export interface ConfirmPlanRequest {
  plan_id: string
  pages: number
  style: string
  color_scheme: string
  custom_colors?: string[]
  custom_style?: string
  font_scheme?: string
  layout_density?: string
  bg_style?: string
  page_number?: string
  border_radius?: string
  shadow_level?: string
  content_align?: string
  extra_options?: Record<string, string>
}

/** 生成响应 */
export interface GenerateResponse {
  plan_id: string
  html_content: string
  title: string
}

/** 编辑请求 */
export interface EditRequest {
  plan_id: string
  html_content: string
}

/** 导出请求 */
export interface ExportRequest {
  plan_id: string
  html_content: string
}

/** 通用响应 */
export interface PPTResponse {
  success: boolean
  message: string
  data?: Record<string, unknown>
}

/** 工作流步骤 */
export type StepType = 'input' | 'plan' | 'preview' | 'download'

/** 风格类型 */
export type StyleType = 'business' | 'academic' | 'creative' | 'minimal'

/** 配色类型 */
export type ColorType = 'blue' | 'green' | 'red' | 'purple' | 'dark' | 'custom'

/** ═══ 用户认证 ═══ */

/** 用户信息 */
export interface User {
  id: string
  username: string
  email: string
  avatar_url?: string
  created_at?: string
  is_active?: boolean
}

/** Token 响应 */
export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

/** 登录请求 */
export interface LoginRequest {
  username: string
  password: string
}

/** 注册请求 */
export interface RegisterRequest {
  username: string
  email: string
  password: string
}

/** 更新用户请求 */
export interface UpdateUserRequest {
  username?: string
  email?: string
  avatar_url?: string
}
