<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import { useAuthStore } from '../stores/auth'
import * as templatesApi from '../api/templates'
import type { Template } from '../api/templates'

const router = useRouter()
const { theme, toggle: toggleTheme } = useTheme()
const authStore = useAuthStore()

// Categories
const categories: { key: string; label: string; icon: string }[] = [
  { key: 'all', label: '全部', icon: '◈' },
  { key: 'business', label: '商务', icon: '◆' },
  { key: 'academic', label: '学术', icon: '◇' },
  { key: 'creative', label: '创意', icon: '✦' },
  { key: 'minimal', label: '简约', icon: '○' },
  { key: 'tech', label: '科技', icon: '◎' },
]

// State
const templates = ref<Template[]>([])
const loading = ref(true)
const activeCategory = ref<string>('all')
const searchQuery = ref('')

// Pagination
const currentPage = ref(1)
const pageSize = 12
const totalPages = ref(1)
const totalTemplates = ref(0)

// Preview modal
const previewTemplate = ref<Template | null>(null)

// Computed
const userInitial = computed(() => {
  return authStore.user?.username?.charAt(0)?.toUpperCase() || '?'
})

const filteredTemplates = computed(() => {
  if (!searchQuery.value) return templates.value
  const query = searchQuery.value.toLowerCase()
  return templates.value.filter(
    t =>
      t.name.toLowerCase().includes(query) ||
      (t.description || '').toLowerCase().includes(query)
  )
})

// Load templates
async function loadTemplates(category?: string, page: number = 1) {
  loading.value = true
  try {
    const result = await templatesApi.getTemplates(
      category && category !== 'all' ? category : undefined,
      page,
      pageSize
    )
    templates.value = result.templates
    totalPages.value = Math.ceil(result.total / pageSize)
    totalTemplates.value = result.total
    currentPage.value = result.page
  } catch (e) {
    console.error('Failed to load templates:', e)
  } finally {
    loading.value = false
  }
}

// Actions
function selectCategory(category: string) {
  activeCategory.value = category
  currentPage.value = 1
  loadTemplates(category)
}

function goToPage(page: number) {
  loadTemplates(activeCategory.value, page)
}

function openPreview(template: Template) {
  previewTemplate.value = template
}

function closePreview() {
  previewTemplate.value = null
}

function useTemplate(template: Template) {
  // Redirect to create page with template pre-filled
  router.push({
    path: '/create',
    query: {
      template: template.id,
      style: template.style,
      colors: template.color_scheme,
    },
  })
}

function goToDashboard() {
  router.push('/dashboard')
}

function goToCreate() {
  router.push('/create')
}

function getCategoryLabel(category: string): string {
  const cat = categories.find(c => c.key === category)
  return cat?.label || category
}

onMounted(() => {
  loadTemplates()
})
</script>

<template>
  <div class="templates-page">
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
          <router-link to="/dashboard" class="nav-link" @click="goToDashboard">工作台</router-link>
          <router-link to="/templates" class="nav-link active">模板库</router-link>
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
    <main class="templates-main">
      <div class="templates-container">
        <!-- 页面标题 -->
        <section class="templates-header">
          <div class="header-text">
            <h1 class="page-title">模板库</h1>
            <p class="page-desc">选择专业设计的模板，快速开始你的演示文稿</p>
          </div>
          <div class="header-search">
            <div class="search-box">
              <span class="search-icon">⌕</span>
              <input
                v-model="searchQuery"
                type="text"
                placeholder="搜索模板..."
                class="search-input"
              />
            </div>
          </div>
        </section>

        <!-- 分类标签 -->
        <section class="category-tabs">
          <button
            v-for="cat in categories"
            :key="cat.key"
            :class="['category-tab', { active: activeCategory === cat.key }]"
            @click="selectCategory(cat.key)"
          >
            <span class="tab-icon">{{ cat.icon }}</span>
            <span class="tab-label">{{ cat.label }}</span>
          </button>
        </section>

        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>加载模板中...</p>
        </div>

        <!-- 空状态 -->
        <div v-else-if="filteredTemplates.length === 0" class="empty-state">
          <div class="empty-icon">◎</div>
          <h3 class="empty-title">暂无模板</h3>
          <p class="empty-desc">
            {{ searchQuery ? '没有找到匹配的模板' : '该分类下暂无模板' }}
          </p>
          <button class="btn btn-primary" @click="goToCreate">
            <span>✦</span> 自由创作
          </button>
        </div>

        <!-- 模板网格 -->
        <div v-else class="templates-grid">
          <div
            v-for="template in filteredTemplates"
            :key="template.id"
            class="template-card"
            @click="openPreview(template)"
          >
            <!-- 预览缩略图 -->
            <div class="template-thumbnail">
              <img
                v-if="template.thumbnail_url"
                :src="template.thumbnail_url"
                :alt="template.name"
                class="thumbnail-img"
              />
              <div v-else class="thumbnail-placeholder">
                <span class="placeholder-icon">◈</span>
                <span class="placeholder-text">{{ template.name }}</span>
              </div>
              <div class="template-overlay">
                <button class="overlay-btn" @click.stop="useTemplate(template)">
                  使用此模板
                </button>
              </div>
            </div>

            <!-- 模板信息 -->
            <div class="template-info">
              <div class="template-header">
                <h3 class="template-name">{{ template.name }}</h3>
                <span class="template-category">{{ getCategoryLabel(template.category) }}</span>
              </div>
              <p class="template-desc">{{ template.description }}</p>
              <div class="template-meta">
                <span class="meta-item">{{ template.style || '通用' }}</span>
                <span class="meta-sep">·</span>
                <span class="meta-item">{{ template.color_scheme || '默认' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="pagination">
          <button
            class="page-btn"
            :disabled="currentPage <= 1"
            @click="goToPage(currentPage - 1)"
          >
            ← 上一页
          </button>
          <span class="page-info">
            第 {{ currentPage }} / {{ totalPages }} 页
            <span class="total-count">共 {{ totalTemplates }} 个模板</span>
          </span>
          <button
            class="page-btn"
            :disabled="currentPage >= totalPages"
            @click="goToPage(currentPage + 1)"
          >
            下一页 →
          </button>
        </div>
      </div>
    </main>

    <!-- 预览模态框 -->
    <Transition name="modal">
      <div v-if="previewTemplate" class="modal-overlay" @click.self="closePreview">
        <div class="preview-modal">
          <button class="modal-close" @click="closePreview">✕</button>

          <div class="preview-content">
            <!-- 预览大图 -->
            <div class="preview-image">
              <img
                v-if="previewTemplate.thumbnail_url"
                :src="previewTemplate.thumbnail_url"
                :alt="previewTemplate.name"
              />
              <div v-else class="preview-placeholder">
                <span>◈</span>
                <p>暂无预览图</p>
              </div>
            </div>

            <!-- 模板详情 -->
            <div class="preview-details">
              <div class="preview-header">
                <span class="preview-category">{{ getCategoryLabel(previewTemplate.category) }}</span>
                <h2 class="preview-title">{{ previewTemplate.name }}</h2>
              </div>

              <p class="preview-desc">{{ previewTemplate.description }}</p>

              <div class="preview-specs">
                <div class="spec-item">
                  <span class="spec-label">风格</span>
                  <span class="spec-value">{{ previewTemplate.style || '通用' }}</span>
                </div>
                <div class="spec-item">
                  <span class="spec-label">配色</span>
                  <span class="spec-value">{{ previewTemplate.color_scheme || '默认' }}</span>
                </div>
                <div class="spec-item">
                  <span class="spec-label">分类</span>
                  <span class="spec-value">{{ getCategoryLabel(previewTemplate.category || '') }}</span>
                </div>
                <div class="spec-item">
                  <span class="spec-label">类型</span>
                  <span class="spec-value">{{ previewTemplate.is_system ? '系统模板' : '用户模板' }}</span>
                </div>
              </div>

              <div class="preview-actions">
                <button class="btn btn-primary btn-lg" @click="useTemplate(previewTemplate)">
                  <span>✦</span> 使用此模板
                </button>
                <button class="btn btn-outline" @click="closePreview">
                  返回浏览
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.templates-page {
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
.templates-main {
  padding: 32px;
}
.templates-container {
  max-width: 1200px;
  margin: 0 auto;
}

/* ═══ 页面标题 ═══ */
.templates-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 32px;
}
.page-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}
.page-desc {
  font-size: 15px;
  color: var(--text-secondary);
}
.header-search {
  flex-shrink: 0;
}
.search-box {
  position: relative;
}
.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 18px;
  color: var(--text-muted);
  pointer-events: none;
}
.search-input {
  padding: 12px 16px 12px 42px;
  background: var(--ink-light);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-primary);
  width: 280px;
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

/* ═══ 分类标签 ═══ */
.category-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 32px;
  flex-wrap: wrap;
}
.category-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--ink-mid);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
  font-family: 'Outfit', sans-serif;
}
.category-tab:hover {
  border-color: rgba(232, 168, 73, 0.15);
  color: var(--text-primary);
  background: var(--ink);
}
.category-tab.active {
  background: var(--amber-glow);
  border-color: var(--amber);
  color: var(--amber);
}
.tab-icon {
  font-size: 16px;
}

/* ═══ 加载与空状态 ═══ */
.loading-state {
  text-align: center;
  padding: 80px 0;
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

/* ═══ 模板网格 ═══ */
.templates-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 40px;
}
.template-card {
  background: var(--ink-mid);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: var(--radius);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s var(--ease-out);
}
.template-card:hover {
  border-color: rgba(232, 168, 73, 0.2);
  transform: translateY(-6px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
}

/* 缩略图 */
.template-thumbnail {
  position: relative;
  aspect-ratio: 16 / 10;
  background: var(--ink-light);
  overflow: hidden;
}
.thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.thumbnail-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-muted);
}
.placeholder-icon {
  font-size: 32px;
  opacity: 0.5;
}
.placeholder-text {
  font-size: 13px;
  opacity: 0.7;
}

/* 悬停覆盖层 */
.template-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s var(--ease-out);
}
.template-card:hover .template-overlay {
  opacity: 1;
}
.overlay-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, var(--amber), var(--amber-dim));
  border: none;
  border-radius: var(--radius-sm);
  color: var(--ink-deep);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
  font-family: 'Outfit', sans-serif;
}
.overlay-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 20px rgba(232, 168, 73, 0.4);
}

/* 模板信息 */
.template-info {
  padding: 20px;
}
.template-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 8px;
}
.template-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
}
.template-category {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  background: var(--amber-glow);
  color: var(--amber);
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}
.template-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.template-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 12px;
}
.meta-sep {
  opacity: 0.4;
}
.template-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.tag {
  font-size: 11px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 4px;
  color: var(--text-muted);
  font-weight: 500;
}

/* ═══ 分页 ═══ */
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
  padding: 10px 20px;
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
  display: flex;
  align-items: center;
  gap: 12px;
}
.total-count {
  font-size: 12px;
  opacity: 0.7;
}

/* ═══ 预览模态框 ═══ */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 32px;
}
.preview-modal {
  background: var(--ink-mid);
  border: 1px solid rgba(232, 168, 73, 0.1);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.5);
}
.modal-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  z-index: 10;
}
.modal-close:hover {
  background: rgba(255, 255, 255, 0.15);
  color: var(--text-primary);
}

.preview-content {
  display: flex;
  gap: 32px;
  padding: 32px;
}
.preview-image {
  flex: 1;
  min-width: 0;
  aspect-ratio: 16 / 10;
  background: var(--ink-light);
  border-radius: var(--radius);
  overflow: hidden;
}
.preview-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.preview-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-muted);
  font-size: 32px;
}
.preview-placeholder p {
  font-size: 14px;
}

.preview-details {
  width: 300px;
  flex-shrink: 0;
}
.preview-header {
  margin-bottom: 16px;
}
.preview-category {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  background: var(--amber-glow);
  color: var(--amber);
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: inline-block;
  margin-bottom: 12px;
}
.preview-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
}
.preview-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 20px;
}
.preview-specs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}
.spec-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.spec-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.spec-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.preview-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}
.preview-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.btn-lg {
  padding: 14px 28px;
  font-size: 15px;
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
.modal-enter-active .preview-modal {
  animation: modalIn 0.3s var(--ease-spring) both;
}
.modal-leave-active .preview-modal {
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
[data-theme='light'] .search-input {
  background: #f0ece5;
  border-color: rgba(0, 0, 0, 0.08);
  color: #1a1612;
}
[data-theme='light'] .category-tab {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.06);
}
[data-theme='light'] .category-tab:hover {
  background: #fafaf8;
}
[data-theme='light'] .template-card {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.06);
}
[data-theme='light'] .template-card:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
}
[data-theme='light'] .template-thumbnail {
  background: #f0ece5;
}
[data-theme='light'] .tag {
  background: rgba(0, 0, 0, 0.04);
}
[data-theme='light'] .page-btn {
  background: #f0ece5;
  border-color: rgba(0, 0, 0, 0.08);
}
[data-theme='light'] .preview-modal {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.08);
}
[data-theme='light'] .preview-image {
  background: #f0ece5;
}

/* ═══ 响应式 ═══ */
@media (max-width: 1024px) {
  .templates-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .preview-content {
    flex-direction: column;
  }
  .preview-details {
    width: 100%;
  }
}
@media (max-width: 768px) {
  .templates-main {
    padding: 20px 16px;
  }
  .templates-header {
    flex-direction: column;
    gap: 20px;
  }
  .page-title {
    font-size: 24px;
  }
  .search-input {
    width: 100%;
  }
  .header-search {
    width: 100%;
  }
  .templates-grid {
    grid-template-columns: 1fr;
  }
  .category-tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: 8px;
  }
  .category-tab {
    white-space: nowrap;
  }
  .nav-center {
    display: none;
  }
  .preview-modal {
    max-height: 95vh;
  }
  .preview-content {
    padding: 20px;
  }
}
</style>
