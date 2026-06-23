/** 认证 Store - 用户登录/注册状态管理 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '../types/ppt'
import * as authApi from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string>(localStorage.getItem('auth_token') || '')
  const loading = ref(false)
  const error = ref('')

  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!user.value)

  // 初始化 — 从 localStorage 恢复 token 并验证
  async function checkAuth() {
    const savedToken = localStorage.getItem('auth_token')
    if (!savedToken) {
      token.value = ''
      user.value = null
      return false
    }

    token.value = savedToken
    try {
      const currentUser = await authApi.getCurrentUser()
      user.value = currentUser
      console.log('[Auth Store] Token 验证成功:', currentUser.username)
      return true
    } catch (e) {
      console.warn('[Auth Store] Token 已过期或无效')
      token.value = ''
      user.value = null
      localStorage.removeItem('auth_token')
      return false
    }
  }

  // 登录
  async function login(username: string, password: string) {
    loading.value = true
    error.value = ''
    try {
      console.log('[Auth Store] 登录:', username)
      const tokenData = await authApi.login(username, password)
      token.value = tokenData.access_token
      localStorage.setItem('auth_token', tokenData.access_token)
      user.value = tokenData.user
      console.log('[Auth Store] 登录成功:', tokenData.user.username)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '登录失败，请检查用户名和密码'
      error.value = msg
      console.error('[Auth Store] 登录失败:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  // 注册
  async function register(username: string, email: string, password: string) {
    loading.value = true
    error.value = ''
    try {
      console.log('[Auth Store] 注册:', username)
      const tokenData = await authApi.register(username, email, password)
      token.value = tokenData.access_token
      localStorage.setItem('auth_token', tokenData.access_token)
      user.value = tokenData.user
      console.log('[Auth Store] 注册并登录成功:', tokenData.user.username)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '注册失败，请稍后重试'
      error.value = msg
      console.error('[Auth Store] 注册失败:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  // 登出
  function logout() {
    console.log('[Auth Store] 登出')
    token.value = ''
    user.value = null
    localStorage.removeItem('auth_token')
  }

  // 更新用户信息
  async function fetchCurrentUser() {
    if (!token.value) return
    try {
      const currentUser = await authApi.getCurrentUser()
      user.value = currentUser
    } catch (e) {
      console.error('[Auth Store] 获取用户信息失败:', e)
    }
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    checkAuth,
    login,
    register,
    logout,
    fetchCurrentUser,
  }
})
