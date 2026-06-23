<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import { useAuthStore } from '../stores/auth'
import * as dashboardApi from '../api/dashboard'
import type { DashboardStats, PlanSummary } from '../api/dashboard'

const router = useRouter()
const { theme, toggle: toggleTheme } = useTheme()
const authStore = useAuthStore()

// State
const stats = ref<DashboardStats>({ total_plans: 0, exported_count: 0, draft_count: 0, generated_count: 0, recent_activity_count: 0 })
const recentPlans = ref<PlanSummary[]>([])
const allPlans = ref<PlanSummary[]>([])
const loading = ref(true)
const statsLoading = ref(true)
const plansLoading = ref(true)

// Pagination
const currentPage = ref(1)
const pageSize = 12
const totalPages = ref(1)
const totalPlans = ref(0)

// Search & Filter
const searchQuery = ref('')
const statusFilter = ref<'all' | 'draft' | 'completed'>('all')

// Rename dialog
const renamingPlan = ref<PlanSummary | null>(null)
const newTitle = ref('')
const renameLoading = ref(false)

// Delete confirmation
const deletingPlan = ref<PlanSummary | null>(null)
const deleteLoading = ref(false)

// Computed
const userInitial = computed(() => {
  return authStore.user?.username?.charAt(0)?.toUpperCase() || '?'
})

const filteredPlans = computed(() => {
  let plans = allPlans.value
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    plans = plans.filter(p => (p.title || '').toLowerCase().includes(query))
  }
  if (statusFilter.value !== 'all') {
    plans = plans.filter(p => p.status === statusFilter.value)
  }
  return plans
})

// Load data
async function loadStats() {
  statsLoading.value = true
  try {
    stats.value = await dashboardApi.getStats()
  } catch (e) {
    console.error('Failed to load stats:', e)
  } finally {
    statsLoading.value = false
  }
}

async function loadRecentPlans() {
  try {
    recentPlans.value = await dashboardApi.getRecentPlans()
  } catch (e) {
    console.error('Failed to load recent plans:', e)
  }
}

async function loadPlans(page: number = 1) {
  plansLoading.value = true
  try {
    const result = await dashboardApi.getPlans(page, pageSize)
    allPlans.value = result.plans
    totalPages.value = Math.ceil(result.total / pageSize)
    totalPlans.value = result.total
    currentPage.value = result.page
  } catch (e) {
    console.error('Failed to load plans:', e)
  } finally {
    plansLoading.value = false
    loading.value = false
  }
}

// Actions
function goToCreate() {
  router.push('/create')
}

function viewPlan(plan: PlanSummary) {
  router.push(`/create?plan=${plan.id}`)
}

function startRename(plan: PlanSummary) {
  renamingPlan.value = plan
  newTitle.value = plan.title || ''
}

async function confirmRename() {
  if (!renamingPlan.value || !newTitle.value.trim()) return
  renameLoading.value = true
  try {
    await dashboardApi.renamePlan(renamingPlan.value.plan_id, newTitle.value.trim())
    // Update local state
    const plan = allPlans.value.find(p => p.plan_id === renamingPlan.value!.plan_id)
    if (plan) plan.title = newTitle.value.trim()
    const recent = recentPlans.value.find(p => p.plan_id === renamingPlan.value!.plan_id)
    if (recent) recent.title = newTitle.value.trim()
    renamingPlan.value = null
  } catch (e) {
    console.error('Failed to rename plan:', e)
  } finally {
    renameLoading.value = false
  }
}

function cancelRename() {
  renamingPlan.value = null
}

function startDelete(plan: PlanSummary) {
  deletingPlan.value = plan
}

async function confirmDelete() {
  if (!deletingPlan.value) return
  deleteLoading.value = true
  try {
    await dashboardApi.deletePlan(deletingPlan.value.plan_id)
    allPlans.value = allPlans.value.filter(p => p.plan_id !== deletingPlan.value!.plan_id)
    recentPlans.value = recentPlans.value.filter(p => p.plan_id !== deletingPlan.value!.plan_id)
    stats.value.total_plans = Math.max(0, stats.value.total_plans - 1)
    deletingPlan.value = null
  } catch (e) {
    console.error('Failed to delete plan:', e)
  } finally {
    deleteLoading.value = false
  }
}

function cancelDelete() {
  deletingPlan.value = null
}

async function duplicatePlan(plan: PlanSummary) {
  try {
    const newPlan = await dashboardApi.duplicatePlan(plan.id)
    allPlans.value.unshift(newPlan)
    stats.value.total_plans++
  } catch (e) {
    console.error('Failed to duplicate plan:', e)
  }
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays < 7) return `${diffDays} 天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: '草稿',
    processing: '处理中',
    completed: '已完成',
    exported: '已导出',
  }
  return labels[status] || status
}

function getStatusClass(status: string): string {
  if (status === 'completed' || status === 'exported') return 'status-success'
  if (status === 'processing') return 'status-warning'
  return 'status-draft'
}

onMounted(async () => {
  await Promise.all([loadStats(), loadRecentPlans(), loadPlans()])
})
</script>

<template>
  <div class="dashboard">
    <!-- 顶部导航 -->
    <nav class="topbar">
      <div class="topbar-inner">
        <div class="brand">
          <router-link to="/" class="brand-link">
            <div class="brand-mark">◈</div>
            <div class="brand-text">
              <span class="brand-name">墨印工坊</span>
              <span class="brand-sub">INKPRESS STUDIO</span>
            </div>
          </router-link>
        </div>

        <div class="nav-center">
          <router-link to="/dashboard" class="nav-link active">工作台</router-link>
          <router-link to="/templates" class="nav-link">模板库</router-link>
        </div>

        <div class="nav-right">
          <button class="theme-toggle" @click="toggleTheme" :title="theme === 'dark' ? '切换到日间模式' : '切换到夜间模式'">
            <span class="theme-icon">{{ theme === 'dark' ? '☀' : '☾' }}</span>
          </button>
          <div class="user-avatar" :title="authStore.user?.username">
            <span class="avatar-initial">{{ userInitial }}</span>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主内容 -->
    <main class="dashboard-main">
      <div class="dashboard-container">
        <!-- 欢迎区域 -->
        <section class="welcome-section">
          <div class="welcome-text">
            <h1 class="welcome-title">
              {{ authStore.user?.username ? `欢迎回来，${authStore.user.username}` : '我的工作台' }}
            </h1>
            <p class="welcome-desc">管理和创建你的演示文稿</p>
          </div>
          <button class="btn btn-primary" @click="goToCreate">
            <span>✦</span> 新建方案
          </button>
        </section>

        <!-- 统计卡片 -->
        <section class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">◈</div>
            <div class="stat-content">
              <div class="stat-value" :class="{ 'stat-loading': statsLoading }">
                {{ statsLoading ? '—' : stats.total_plans }}
              </div>
              <div class="stat-label">总方案数</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">↓</div>
            <div class="stat-content">
              <div class="stat-value" :class="{ 'stat-loading': statsLoading }">
                {{ statsLoading ? '—' : stats.exported_count }}
              </div>
              <div class="stat-label">已导出</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">✦</div>
            <div class="stat-content">
              <div class="stat-value" :class="{ 'stat-loading': statsLoading }">
                {{ statsLoading ? '—' : stats.generated_count }}
              </div>
              <div class="stat-label">已生成</div>
            </div>
          </div>
        </section>

        <!-- 最近方案 -->
        <section class="recent-section" v-if="recentPlans.length > 0">
          <div class="section-header">
            <h2 class="section-title">最近方案</h2>
            <button class="btn btn-outline btn-sm" @click="goToCreate">查看全部</button>
          </div>
          <div class="recent-grid">
            <div
              v-for="plan in recentPlans"
              :key="plan.id"
              class="recent-card"
              @click="viewPlan(plan)"
            >
              <div class="recent-card-header">
                <span class="recent-card-icon">◈</span>
                <span :class="['recent-card-status', getStatusClass(plan.status)]">
                  {{ getStatusLabel(plan.status) }}
                </span>
              </div>
              <h3 class="recent-card-title">{{ plan.title || '未命名方案' }}</h3>
              <div class="recent-card-meta">
                <span>{{ formatDate(plan.updated_at) }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 全部方案 -->
        <section class="plans-section">
          <div class="section-header">
            <h2 class="section-title">全部方案</h2>
            <div class="plans-controls">
              <div class="search-box">
                <span class="search-icon">⌕</span>
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="搜索方案..."
                  class="search-input"
                />
              </div>
              <select v-model="statusFilter" class="status-select">
                <option value="all">全部状态</option>
                <option value="draft">草稿</option>
                <option value="completed">已完成</option>
              </select>
            </div>
          </div>

          <!-- 加载状态 -->
          <div v-if="plansLoading" class="loading-state">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>

          <!-- 空状态 -->
          <div v-else-if="filteredPlans.length === 0" class="empty-state">
            <div class="empty-icon">◈</div>
            <h3 class="empty-title">暂无方案</h3>
            <p class="empty-desc">
              {{ searchQuery ? '没有找到匹配的方案' : '开始创建你的第一个演示文稿吧' }}
            </p>
            <button class="btn btn-primary" @click="goToCreate">
              <span>✦</span> 立即创建
            </button>
          </div>

          <!-- 方案列表 -->
          <div v-else class="plans-list">
            <div
              v-for="plan in filteredPlans"
              :key="plan.id"
              class="plan-item"
            >
              <div class="plan-item-main" @click="viewPlan(plan)">
                <div class="plan-item-icon">
                  <span>◈</span>
                </div>
                <div class="plan-item-info">
                  <h3 class="plan-item-title">{{ plan.title || '未命名方案' }}</h3>
                  <div class="plan-item-meta">
                    <span :class="['plan-status', getStatusClass(plan.status)]">
                      {{ getStatusLabel(plan.status) }}
                    </span>
                    <span class="plan-meta-sep">·</span>
                    <span v-if="plan.suggested_style">{{ plan.suggested_style }}</span>
                    <span v-if="plan.suggested_style" class="plan-meta-sep">·</span>
                    <span>{{ formatDate(plan.updated_at) }}</span>
                  </div>
                </div>
              </div>
              <div class="plan-item-actions">
                <button class="action-btn" title="重命名" @click.stop="startRename(plan)">
                  ✎
                </button>
                <button class="action-btn" title="复制" @click.stop="duplicatePlan(plan)">
                  ⧉
                </button>
                <button class="action-btn action-btn-danger" title="删除" @click.stop="startDelete(plan)">
                  ✕
                </button>
              </div>
            </div>
          </div>

          <!-- 分页 -->
          <div v-if="totalPages > 1" class="pagination">
            <button
              class="page-btn"
              :disabled="currentPage <= 1"
              @click="loadPlans(currentPage - 1)"
            >
              ← 上一页
            </button>
            <span class="page-info">
              第 {{ currentPage }} / {{ totalPages }} 页
            </span>
            <button
              class="page-btn"
              :disabled="currentPage >= totalPages"
              @click="loadPlans(currentPage + 1)"
            >
              下一页 →
            </button>
          </div>
        </section>
      </div>
    </main>

    <!-- 重命名对话框 -->
    <Transition name="modal">
      <div v-if="renamingPlan" class="modal-overlay" @click.self="cancelRename">
        <div class="modal-card">
          <h3 class="modal-title">重命名方案</h3>
          <input
            v-model="newTitle"
            type="text"
            class="modal-input"
            placeholder="输入新名称"
            @keyup.enter="confirmRename"
            autofocus
          />
          <div class="modal-actions">
            <button class="btn btn-outline" @click="cancelRename">取消</button>
            <button
              class="btn btn-primary"
              :disabled="!newTitle.trim() || renameLoading"
              @click="confirmRename"
            >
              {{ renameLoading ? '保存中...' : '确认' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 删除确认对话框 -->
    <Transition name="modal">
      <div v-if="deletingPlan" class="modal-overlay" @click.self="cancelDelete">
        <div class="modal-card">
          <h3 class="modal-title">确认删除</h3>
          <p class="modal-desc">
            确定要删除方案「{{ deletingPlan.title || '未命名方案' }}」吗？此操作无法撤销。
          </p>
          <div class="modal-actions">
            <button class="btn btn-outline" @click="cancelDelete">取消</button>
            <button
              class="btn btn-warning"
              :disabled="deleteLoading"
              @click="confirmDelete"
            >
              {{ deleteLoading ? '删除中...' : '确认删除' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: var(--ink-deep);
}

/* ═══ 导航 ═══ */
.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(12, 14, 20, 0.85);
  backdrop-filter: blur(20px) saturate(1.5);
  border-bottom: 1px solid rgba(232, 168, 73, 0.08);
}
.topbar-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 32px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand-link {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
}
.brand-mark {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, var(--amber), var(--amber-dim));
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: var(--ink-deep);
  font-weight: 800;
  box-shadow: 0 2px 12px rgba(232, 168, 73, 0.25);
}
.brand-text {
  display: flex;
  flex-direction: column;
}
.brand-name {
  font-family: 'Noto Serif SC', serif;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 2px;
  line-height: 1.2;
}
.brand-sub {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px;
  color: var(--text-muted);
  letter-spacing: 3px;
  text-transform: uppercase;
}

/* 导航中心链接 */
.nav-center {
  display: flex;
  gap: 8px;
}
.nav-link {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.25s var(--ease-out);
}
.nav-link:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.04);
}
.nav-link.active {
  color: var(--amber);
  background: var(--amber-glow);
}

/* 导航右侧 */
.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.theme-toggle {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s var(--ease-out);
}
.theme-toggle:hover {
  background: rgba(232, 168, 73, 0.12);
  border-color: rgba(232, 168, 73, 0.25);
  color: var(--amber);
  transform: rotate(30deg);
}
.theme-icon {
  font-size: 16px;
}

/* 用户头像 */
.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--amber), var(--amber-dim));
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s var(--ease-out);
}
.user-avatar:hover {
  transform: scale(1.1);
  box-shadow: 0 0 16px rgba(232, 168, 73, 0.3);
}
.avatar-initial {
  font-size: 14px;
  font-weight: 700;
  color: var(--ink-deep);
  font-family: 'Outfit', sans-serif;
}

/* ═══ 主内容 ═══ */
.dashboard-main {
  padding: 32px;
}
.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
}

/* ═══ 欢迎区域 ═══ */
.welcome-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}
.welcome-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}
.welcome-desc {
  font-size: 15px;
  color: var(--text-secondary);
}
.btn-sm {
  padding: 8px 20px;
  font-size: 13px;
}

/* ═══ 统计卡片 ═══ */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}
.stat-card {
  background: var(--ink-mid);
  border: 1px solid rgba(232, 168, 73, 0.08);
  border-radius: var(--radius);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.3s var(--ease-out);
}
.stat-card:hover {
  border-color: rgba(232, 168, 73, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}
.stat-icon {
  width: 48px;
  height: 48px;
  background: var(--amber-glow);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: var(--amber);
}
.stat-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 32px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: 4px;
}
.stat-value.stat-loading {
  color: var(--text-muted);
}
.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

/* ═══ 区块标题 ═══ */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.section-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

/* ═══ 最近方案 ═══ */
.recent-section {
  margin-bottom: 40px;
}
.recent-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.recent-card {
  background: var(--ink-mid);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: var(--radius);
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s var(--ease-out);
}
.recent-card:hover {
  border-color: rgba(232, 168, 73, 0.2);
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
}
.recent-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.recent-card-icon {
  font-size: 18px;
  color: var(--amber);
}
.recent-card-status {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.status-success {
  background: var(--jade-glow);
  color: var(--jade);
}
.status-warning {
  background: rgba(232, 168, 73, 0.15);
  color: var(--amber);
}
.status-draft {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-muted);
}
.recent-card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.recent-card-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);
}

/* ═══ 方案列表 ═══ */
.plans-section {
  margin-bottom: 40px;
}
.plans-controls {
  display: flex;
  gap: 12px;
}
.search-box {
  position: relative;
}
.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
  color: var(--text-muted);
  pointer-events: none;
}
.search-input {
  padding: 8px 12px 8px 36px;
  background: var(--ink-light);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-primary);
  width: 220px;
  transition: all 0.25s var(--ease-out);
  font-family: 'Outfit', sans-serif;
}
.search-input::placeholder {
  color: var(--text-muted);
}
.search-input:focus {
  outline: none;
  border-color: var(--amber-dim);
  box-shadow: 0 0 0 3px var(--amber-glow);
  background: var(--ink);
}
.status-select {
  padding: 8px 12px;
  background: var(--ink-light);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  font-family: 'Outfit', sans-serif;
}
.status-select:focus {
  outline: none;
  border-color: var(--amber-dim);
}

/* 加载状态 */
.loading-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-muted);
}
.spinner {
  width: 40px;
  height: 40px;
  border: 2px solid rgba(232, 168, 73, 0.15);
  border-top-color: var(--amber);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 0;
}
.empty-icon {
  font-size: 48px;
  color: var(--text-muted);
  margin-bottom: 20px;
  opacity: 0.5;
}
.empty-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.empty-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 24px;
}

/* 方案列表项 */
.plans-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.plan-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--ink-mid);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: var(--radius);
  padding: 16px 20px;
  transition: all 0.25s var(--ease-out);
}
.plan-item:hover {
  border-color: rgba(232, 168, 73, 0.15);
  background: var(--ink);
}
.plan-item-main {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  cursor: pointer;
  min-width: 0;
}
.plan-item-icon {
  width: 40px;
  height: 40px;
  background: var(--amber-glow);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: var(--amber);
  flex-shrink: 0;
}
.plan-item-info {
  flex: 1;
  min-width: 0;
}
.plan-item-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.plan-item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
}
.plan-status {
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}
.plan-meta-sep {
  opacity: 0.4;
}

/* 操作按钮 */
.plan-item-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}
.plan-item:hover .plan-item-actions {
  opacity: 1;
}
.action-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition: all 0.2s;
}
.action-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
}
.action-btn-danger:hover {
  background: var(--vermillion-glow);
  color: var(--vermillion);
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}
.page-btn {
  padding: 8px 16px;
  background: var(--ink-light);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'Outfit', sans-serif;
}
.page-btn:hover:not(:disabled) {
  border-color: var(--amber-dim);
  color: var(--amber);
}
.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.page-info {
  font-size: 13px;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}

/* ═══ 模态框 ═══ */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.modal-card {
  background: var(--ink-mid);
  border: 1px solid rgba(232, 168, 73, 0.1);
  border-radius: var(--radius);
  padding: 32px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}
.modal-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 16px;
}
.modal-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 24px;
}
.modal-input {
  width: 100%;
  padding: 12px 16px;
  background: var(--ink-light);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-sm);
  font-size: 15px;
  color: var(--text-primary);
  margin-bottom: 24px;
  transition: all 0.25s var(--ease-out);
  font-family: 'Outfit', sans-serif;
}
.modal-input:focus {
  outline: none;
  border-color: var(--amber-dim);
  box-shadow: 0 0 0 3px var(--amber-glow);
}
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* 模态框动画 */
.modal-enter-active {
  transition: opacity 0.3s var(--ease-out);
}
.modal-leave-active {
  transition: opacity 0.2s var(--ease-out);
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-active .modal-card {
  animation: modalIn 0.3s var(--ease-spring) both;
}
.modal-leave-active .modal-card {
  animation: modalOut 0.2s var(--ease-out) both;
}
@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
@keyframes modalOut {
  from {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
  to {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
}

/* ═══ 日间模式 ═══ */
[data-theme='light'] .topbar {
  background: rgba(244, 241, 236, 0.9);
  border-bottom-color: rgba(0, 0, 0, 0.06);
}
[data-theme='light'] .brand-name {
  color: #1a1612;
}
[data-theme='light'] .brand-sub {
  color: #9a9488;
}
[data-theme='light'] .nav-link {
  color: #5c564e;
}
[data-theme='light'] .nav-link:hover {
  background: rgba(0, 0, 0, 0.04);
}
[data-theme='light'] .stat-card {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.06);
}
[data-theme='light'] .stat-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}
[data-theme='light'] .recent-card {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.06);
}
[data-theme='light'] .recent-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
}
[data-theme='light'] .plan-item {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.06);
}
[data-theme='light'] .plan-item:hover {
  background: #fafaf8;
}
[data-theme='light'] .search-input,
[data-theme='light'] .status-select {
  background: #f0ece5;
  border-color: rgba(0, 0, 0, 0.08);
  color: #1a1612;
}
[data-theme='light'] .page-btn {
  background: #f0ece5;
  border-color: rgba(0, 0, 0, 0.08);
}
[data-theme='light'] .modal-card {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.08);
}
[data-theme='light'] .modal-input {
  background: #f0ece5;
  border-color: rgba(0, 0, 0, 0.08);
}

/* ═══ 响应式 ═══ */
@media (max-width: 1024px) {
  .recent-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 768px) {
  .dashboard-main {
    padding: 20px 16px;
  }
  .welcome-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  .welcome-title {
    font-size: 22px;
  }
  .stats-grid {
    grid-template-columns: 1fr;
  }
  .recent-grid {
    grid-template-columns: 1fr;
  }
  .plans-controls {
    flex-direction: column;
    width: 100%;
  }
  .search-input {
    width: 100%;
  }
  .nav-center {
    display: none;
  }
}
</style>
