/** 认证 API 服务 */
import api from './index'
import type {
  User,
  TokenResponse,
  RegisterRequest,
  UpdateUserRequest,
} from '../types/ppt'

/** 登录 */
export async function login(username: string, password: string): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/login', { username, password })
  return data
}

/** 注册 */
export async function register(username: string, email: string, password: string): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/register', {
    username,
    email,
    password,
  } as RegisterRequest)
  return data
}

/** 获取当前用户信息 */
export async function getCurrentUser(): Promise<User> {
  const { data } = await api.get<User>('/auth/me')
  return data
}

/** 更新用户信息 */
export async function updateUser(updates: UpdateUserRequest): Promise<User> {
  const { data } = await api.put<User>('/auth/me', updates)
  return data
}
