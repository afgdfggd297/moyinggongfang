<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// Tab 切换
type TabType = 'login' | 'register'
const activeTab = ref<TabType>('login')

// 登录表单
const loginForm = ref({
  username: '',
  password: '',
})

// 注册表单
const registerForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

// 错误信息
const localError = ref('')

// 是否正在提交
const isSubmitting = computed(() => authStore.loading)

// 表单验证
function validateLogin(): string | null {
  if (!loginForm.value.username.trim()) return '请输入用户名'
  if (!loginForm.value.password) return '请输入密码'
  if (loginForm.value.password.length < 6) return '密码长度至少 6 位'
  return null
}

function validateRegister(): string | null {
  if (!registerForm.value.username.trim()) return '请输入用户名'
  if (registerForm.value.username.length < 3) return '用户名长度至少 3 位'
  if (!registerForm.value.email.trim()) return '请输入邮箱'
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(registerForm.value.email)) return '请输入有效的邮箱地址'
  if (!registerForm.value.password) return '请输入密码'
  if (registerForm.value.password.length < 6) return '密码长度至少 6 位'
  if (registerForm.value.password !== registerForm.value.confirmPassword) return '两次输入的密码不一致'
  return null
}

// 提交登录
async function handleLogin() {
  localError.value = ''
  const err = validateLogin()
  if (err) { localError.value = err; return }

  try {
    await authStore.login(loginForm.value.username, loginForm.value.password)
    router.push('/dashboard')
  } catch (e: unknown) {
    localError.value = e instanceof Error ? e.message : '登录失败，请检查用户名和密码'
  }
}

// 提交注册
async function handleRegister() {
  localError.value = ''
  const err = validateRegister()
  if (err) { localError.value = err; return }

  try {
    await authStore.register(
      registerForm.value.username,
      registerForm.value.email,
      registerForm.value.password
    )
    router.push('/dashboard')
  } catch (e: unknown) {
    localError.value = e instanceof Error ? e.message : '注册失败，请稍后重试'
  }
}

// 切换 Tab
function switchTab(tab: TabType) {
  activeTab.value = tab
  localError.value = ''
  authStore.error = ''
}
</script>

<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="bg-pattern" />
    <div class="bg-glow" />

    <!-- 顶部导航 -->
    <nav class="login-nav">
      <router-link to="/" class="brand">
        <div class="brand-mark">◈</div>
        <div class="brand-text">
          <span class="brand-name">墨印工坊</span>
          <span class="brand-sub">INKPRESS STUDIO</span>
        </div>
      </router-link>
    </nav>

    <!-- 主体 -->
    <main class="login-main">
      <div class="login-card">
        <!-- 顶部金线装饰 -->
        <div class="card-accent" />

        <!-- 标题 -->
        <div class="card-header">
          <h1 class="card-title">{{ activeTab === 'login' ? '欢迎回来' : '创建账号' }}</h1>
          <p class="card-subtitle">
            {{ activeTab === 'login' ? '登录您的墨印工坊账号' : '加入墨印工坊，开始创作' }}
          </p>
        </div>

        <!-- Tab 切换 -->
        <div class="tab-bar">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'login' }"
            @click="switchTab('login')"
          >
            <span class="tab-icon">→</span>
            登录
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'register' }"
            @click="switchTab('register')"
          >
            <span class="tab-icon">✦</span>
            注册
          </button>
        </div>

        <!-- 错误提示 -->
        <Transition name="error-slide">
          <div v-if="localError || authStore.error" class="error-alert">
            <span class="error-icon">✕</span>
            <span>{{ localError || authStore.error }}</span>
          </div>
        </Transition>

        <!-- 登录表单 -->
        <Transition name="form-fade" mode="out-in">
          <form v-if="activeTab === 'login'" key="login" @submit.prevent="handleLogin" class="auth-form">
            <div class="form-group">
              <label for="login-username">用户名</label>
              <div class="input-wrapper">
                <span class="input-icon">◎</span>
                <input
                  id="login-username"
                  v-model="loginForm.username"
                  type="text"
                  placeholder="输入您的用户名"
                  autocomplete="username"
                  :disabled="isSubmitting"
                />
              </div>
            </div>

            <div class="form-group">
              <label for="login-password">密码</label>
              <div class="input-wrapper">
                <span class="input-icon">◈</span>
                <input
                  id="login-password"
                  v-model="loginForm.password"
                  type="password"
                  placeholder="输入您的密码"
                  autocomplete="current-password"
                  :disabled="isSubmitting"
                />
              </div>
            </div>

            <button
              type="submit"
              class="btn btn-primary btn-full"
              :disabled="isSubmitting"
            >
              <span v-if="isSubmitting" class="btn-spinner" />
              <span v-else>→</span>
              {{ isSubmitting ? '登录中...' : '登录' }}
            </button>
          </form>

          <!-- 注册表单 -->
          <form v-else key="register" @submit.prevent="handleRegister" class="auth-form">
            <div class="form-group">
              <label for="reg-username">用户名</label>
              <div class="input-wrapper">
                <span class="input-icon">◎</span>
                <input
                  id="reg-username"
                  v-model="registerForm.username"
                  type="text"
                  placeholder="选择一个用户名"
                  autocomplete="username"
                  :disabled="isSubmitting"
                />
              </div>
            </div>

            <div class="form-group">
              <label for="reg-email">邮箱</label>
              <div class="input-wrapper">
                <span class="input-icon">◈</span>
                <input
                  id="reg-email"
                  v-model="registerForm.email"
                  type="email"
                  placeholder="输入您的邮箱"
                  autocomplete="email"
                  :disabled="isSubmitting"
                />
              </div>
            </div>

            <div class="form-group">
              <label for="reg-password">密码</label>
              <div class="input-wrapper">
                <span class="input-icon">◈</span>
                <input
                  id="reg-password"
                  v-model="registerForm.password"
                  type="password"
                  placeholder="设置密码（至少 6 位）"
                  autocomplete="new-password"
                  :disabled="isSubmitting"
                />
              </div>
            </div>

            <div class="form-group">
              <label for="reg-confirm">确认密码</label>
              <div class="input-wrapper">
                <span class="input-icon">◈</span>
                <input
                  id="reg-confirm"
                  v-model="registerForm.confirmPassword"
                  type="password"
                  placeholder="再次输入密码"
                  autocomplete="new-password"
                  :disabled="isSubmitting"
                />
              </div>
            </div>

            <button
              type="submit"
              class="btn btn-primary btn-full"
              :disabled="isSubmitting"
            >
              <span v-if="isSubmitting" class="btn-spinner" />
              <span v-else>✦</span>
              {{ isSubmitting ? '注册中...' : '创建账号' }}
            </button>
          </form>
        </Transition>

        <!-- 底部 -->
        <div class="card-footer">
          <p v-if="activeTab === 'login'" class="footer-text">
            还没有账号？
            <a href="#" @click.prevent="switchTab('register')" class="footer-link">立即注册</a>
          </p>
          <p v-else class="footer-text">
            已有账号？
            <a href="#" @click.prevent="switchTab('login')" class="footer-link">立即登录</a>
          </p>
        </div>
      </div>

      <!-- 底部品牌 -->
      <div class="login-brand-bottom">
        <span class="brand-tagline">AI 驱动的演示文稿生成工具</span>
      </div>
    </main>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ═══ 背景装饰 ═══ */
.bg-pattern {
  position: fixed;
  inset: 0;
  z-index: 0;
  background-image:
    radial-gradient(circle at 20% 50%, rgba(232, 168, 73, 0.04) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(107, 125, 179, 0.03) 0%, transparent 40%),
    radial-gradient(circle at 60% 80%, rgba(91, 168, 140, 0.03) 0%, transparent 40%);
  pointer-events: none;
}

.bg-glow {
  position: fixed;
  top: -20%;
  left: -10%;
  width: 60vw;
  height: 60vw;
  background: radial-gradient(circle, rgba(232, 168, 73, 0.06) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
  animation: glowPulse 8s ease-in-out infinite alternate;
}

@keyframes glowPulse {
  from { opacity: 0.6; transform: translate(0, 0); }
  to { opacity: 1; transform: translate(5%, 3%); }
}

/* ═══ 导航 ═══ */
.login-nav {
  position: relative;
  z-index: 10;
  padding: 24px 40px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  transition: opacity 0.3s;
}

.brand:hover {
  opacity: 0.85;
}

.brand-mark {
  width: 38px;
  height: 38px;
  background: linear-gradient(135deg, var(--amber), var(--amber-dim));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: var(--ink-deep);
  font-weight: 800;
  box-shadow: 0 2px 16px rgba(232, 168, 73, 0.3);
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-family: 'Noto Serif SC', serif;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 3px;
  line-height: 1.2;
}

.brand-sub {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: var(--text-muted);
  letter-spacing: 3px;
  text-transform: uppercase;
}

/* ═══ 主体 ═══ */
.login-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
  padding: 0 20px 80px;
}

/* ═══ 登录卡片 ═══ */
.login-card {
  width: 100%;
  max-width: 440px;
  background: var(--ink-mid);
  border: 1px solid rgba(232, 168, 73, 0.08);
  border-radius: var(--radius-lg);
  padding: 40px 36px 32px;
  position: relative;
  box-shadow: var(--shadow-lg), var(--shadow-glow);
  animation: cardEnter 0.6s var(--ease-out) both;
}

@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(24px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.card-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent 0%, var(--amber) 30%, var(--amber-dim) 70%, transparent 100%);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

/* ═══ 卡片头部 ═══ */
.card-header {
  text-align: center;
  margin-bottom: 28px;
}

.card-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 2px;
  margin-bottom: 8px;
}

.card-subtitle {
  font-family: 'Outfit', sans-serif;
  font-size: 14px;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

/* ═══ Tab 栏 ═══ */
.tab-bar {
  display: flex;
  background: var(--ink-light);
  border-radius: var(--radius-sm);
  padding: 4px;
  margin-bottom: 24px;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.tab-btn {
  flex: 1;
  padding: 10px 16px;
  background: transparent;
  border: none;
  border-radius: 6px;
  font-family: 'Outfit', sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.3s var(--ease-out);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.tab-btn:hover {
  color: var(--text-secondary);
}

.tab-btn.active {
  background: var(--ink-mid);
  color: var(--amber);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.tab-icon {
  font-size: 12px;
}

/* ═══ 错误提示 ═══ */
.error-alert {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--vermillion-glow);
  border: 1px solid rgba(212, 93, 76, 0.2);
  border-left: 3px solid var(--vermillion);
  border-radius: var(--radius-sm);
  margin-bottom: 20px;
  font-size: 13px;
  font-weight: 500;
  color: var(--vermillion);
  font-family: 'Outfit', sans-serif;
}

.error-icon {
  width: 18px;
  height: 18px;
  background: rgba(212, 93, 76, 0.15);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  flex-shrink: 0;
}

.error-slide-enter-active {
  transition: all 0.3s var(--ease-out);
}
.error-slide-leave-active {
  transition: all 0.2s ease;
}
.error-slide-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.error-slide-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* ═══ 表单 ═══ */
.auth-form {
  margin-bottom: 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-family: 'Outfit', sans-serif;
  font-weight: 600;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 1.5px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 14px;
  font-size: 14px;
  color: var(--text-muted);
  pointer-events: none;
  transition: color 0.3s;
  z-index: 1;
}

.input-wrapper input {
  width: 100%;
  padding: 13px 16px 13px 40px;
  background: var(--ink-light);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-sm);
  font-family: 'Outfit', sans-serif;
  font-size: 14px;
  color: var(--text-primary);
  transition: all 0.25s var(--ease-out);
  outline: none;
}

.input-wrapper input::placeholder {
  color: var(--text-muted);
  font-size: 13px;
}

.input-wrapper input:focus {
  border-color: var(--amber-dim);
  box-shadow: 0 0 0 3px var(--amber-glow);
  background: var(--ink);
}

.input-wrapper input:focus + .input-icon,
.input-wrapper:has(input:focus) .input-icon {
  color: var(--amber);
}

.input-wrapper input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ═══ 按钮 ═══ */
.btn-full {
  width: 100%;
  justify-content: center;
  padding: 14px 28px;
  font-size: 15px;
  margin-top: 8px;
  font-family: 'Outfit', sans-serif;
  letter-spacing: 0.5px;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(12, 14, 20, 0.2);
  border-top-color: var(--ink-deep);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ═══ 表单切换动画 ═══ */
.form-fade-enter-active {
  transition: all 0.35s var(--ease-out);
}
.form-fade-leave-active {
  transition: all 0.2s ease;
}
.form-fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}
.form-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* ═══ 底部 ═══ */
.card-footer {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  text-align: center;
}

.footer-text {
  font-family: 'Outfit', sans-serif;
  font-size: 13px;
  color: var(--text-muted);
}

.footer-link {
  color: var(--amber);
  text-decoration: none;
  font-weight: 600;
  transition: all 0.2s;
  position: relative;
}

.footer-link::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 0;
  height: 1px;
  background: var(--amber);
  transition: width 0.3s var(--ease-out);
}

.footer-link:hover::after {
  width: 100%;
}

.footer-link:hover {
  color: var(--amber-dim);
}

/* ═══ 底部品牌 ═══ */
.login-brand-bottom {
  margin-top: 32px;
  text-align: center;
  animation: fadeIn 0.8s var(--ease-out) 0.3s both;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.brand-tagline {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 2px;
  opacity: 0.5;
}

/* ═══ 亮色模式适配 ═══ */
[data-theme="light"] .login-card {
  background: #FFFFFF;
  border-color: rgba(0, 0, 0, 0.06);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.08);
}

[data-theme="light"] .tab-bar {
  background: #F0ECE5;
  border-color: rgba(0, 0, 0, 0.04);
}

[data-theme="light"] .tab-btn.active {
  background: #FFFFFF;
  color: var(--amber-dim);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

[data-theme="light"] .input-wrapper input {
  background: #F0ECE5;
  border-color: rgba(0, 0, 0, 0.06);
  color: #1A1612;
}

[data-theme="light"] .input-wrapper input:focus {
  background: #FFFFFF;
  border-color: var(--amber-dim);
}

[data-theme="light"] .input-wrapper input::placeholder {
  color: #9A9488;
}

[data-theme="light"] .input-icon {
  color: #9A9488;
}

[data-theme="light"] .card-footer {
  border-top-color: rgba(0, 0, 0, 0.06);
}

/* ═══ 响应式 ═══ */
@media (max-width: 480px) {
  .login-card {
    padding: 32px 24px 24px;
    border-radius: var(--radius);
  }

  .card-title {
    font-size: 24px;
  }

  .login-nav {
    padding: 16px 20px;
  }

  .brand-name {
    font-size: 16px;
  }
}
</style>
