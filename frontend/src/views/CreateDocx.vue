<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useDocxStore } from '../stores/docx'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'

const store = useDocxStore()
const auth = useAuthStore()
const { theme, toggle: toggleTheme } = useTheme()
const router = useRouter()

const steps = [
  { key: 'input', label: '输入', icon: '✦' },
  { key: 'plan', label: '方案', icon: '◈' },
  { key: 'preview', label: '预览', icon: '◎' },
  { key: 'download', label: '下载', icon: '↓' },
] as const

const stepOrder: Record<string, number> = { input: 1, plan: 2, preview: 3, download: 4 }
const currentIndex = computed(() => stepOrder[store.currentStep] ?? 0)

function isActive(key: string) { return store.currentStep === key }
function isDone(key: string) { return currentIndex.value > (stepOrder[key] ?? 0) }

// 输入表单
const inputText = ref('')
const extraInfo = ref('')
const enableSearch = ref(true)

async function submitPlan() {
  if (!inputText.value.trim()) return
  await store.createPlan(inputText.value, extraInfo.value, enableSearch.value)
}

async function confirmPlan() {
  await store.confirmPlanStream()
}

// 历史记录
const showHistory = ref(false)

function toggleHistory() {
  showHistory.value = !showHistory.value
}

function loadFromHistory(planId: string) {
  store.loadPlan(planId)
  showHistory.value = false
}

// 预览
const iframeRef = ref<HTMLIFrameElement | null>(null)
const previewScale = ref(0.7)
const editMode = ref(false)

function renderPreview() {
  if (!iframeRef.value || !store.htmlContent) return
  const doc = iframeRef.value.contentDocument || iframeRef.value.contentWindow?.document
  if (!doc) return

  const fullHtml = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      font-family: 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
      line-height: 1.8;
      color: #333;
      max-width: 800px;
      margin: 0 auto;
      padding: 40px;
    }
    h1 { font-size: 28px; font-weight: 700; color: #1a1a1a; margin-bottom: 24px; border-bottom: 2px solid #e8a849; padding-bottom: 12px; }
    h2 { font-size: 22px; font-weight: 600; color: #2c3e50; margin-top: 32px; margin-bottom: 16px; }
    h3 { font-size: 18px; font-weight: 600; color: #34495e; margin-top: 24px; margin-bottom: 12px; }
    p { margin-bottom: 12px; }
    ul, ol { margin-bottom: 12px; padding-left: 24px; }
    li { margin-bottom: 6px; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    th, td { border: 1px solid #ddd; padding: 10px 14px; text-align: left; }
    th { background: #f5f5f5; font-weight: 600; }
    tr:nth-child(even) { background: #fafafa; }
  </style>
</head>
<body>
${store.htmlContent}
</body>
</html>`

  doc.open()
  doc.write(fullHtml)
  doc.close()
}

function toggleEditMode() {
  editMode.value = !editMode.value
  const doc = iframeRef.value?.contentDocument || iframeRef.value?.contentWindow?.document
  if (!doc) return

  const body = doc.body
  if (editMode.value) {
    body.contentEditable = 'true'
    body.style.cursor = 'text'
  } else {
    body.contentEditable = 'false'
    body.style.cursor = ''
  }
}

async function saveEdit() {
  const doc = iframeRef.value?.contentDocument || iframeRef.value?.contentWindow?.document
  if (!doc) return
  store.htmlContent = doc.body.innerHTML
  await store.saveEdit()
  editMode.value = false
}

watch(() => store.htmlContent, () => {
  nextTick(renderPreview)
})

onMounted(() => {
  if (store.htmlContent) {
    nextTick(renderPreview)
  }
})
</script>

<template>
  <div class="app-shell">
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
        <button class="theme-toggle" @click="toggleTheme" :title="theme === 'dark' ? '切换到日间模式' : '切换到夜间模式'">
          <span class="theme-icon">{{ theme === 'dark' ? '☀' : '☾' }}</span>
        </button>
        <button class="topbar-btn" @click="router.push('/create')" title="制作PPT">
          <span>PPT</span>
        </button>
        <template v-if="auth.isAuthenticated">
          <button class="topbar-btn" @click="router.push('/dashboard')" title="仪表盘">
            <span class="topbar-avatar">{{ (auth.user?.username || 'U')[0].toUpperCase() }}</span>
          </button>
        </template>
        <template v-else>
          <button class="topbar-btn" @click="router.push('/login')" title="登录">登录</button>
        </template>
      </div>
    </nav>

    <!-- 主体布局 -->
    <div class="app-body">
      <!-- 历史记录侧边栏 -->
      <aside class="history-sidebar" :class="{ show: showHistory }">
        <div class="history-header">
          <h3>历史记录</h3>
          <button class="close-btn" @click="showHistory = false">✕</button>
        </div>
        <div class="history-list">
          <div v-if="store.historyList.length === 0" class="history-empty">
            暂无历史记录
          </div>
          <div
            v-for="item in store.historyList"
            :key="item.planId"
            class="history-item"
            :class="{ active: store.planId === item.planId }"
            @click="loadFromHistory(item.planId)"
          >
            <div class="item-title">{{ item.title }}</div>
            <div class="item-meta">
              <span class="item-time">{{ item.time }}</span>
              <button class="delete-btn" @click.stop="store.removeEntry(item.planId)">✕</button>
            </div>
          </div>
        </div>
      </aside>

      <main class="main-stage">
        <div class="content-area">
          <div class="card-area">
            <!-- 步骤1: 输入 -->
            <div v-if="isActive('input')" class="card">
              <div class="corner-deco">01</div>
              <div class="card-title">
                <span class="icon">✦</span>
                <span>输入内容</span>
                <button class="history-btn" @click="toggleHistory" title="历史记录">
                  <span>📋</span>
                </button>
              </div>
              <p class="card-desc">输入你想生成文档的内容，AI 会自动规划文档结构。</p>

              <div class="form-group">
                <label>主要内容 *</label>
                <textarea
                  v-model="inputText"
                  class="form-textarea"
                  rows="6"
                  placeholder="例如：我们公司Q3业绩回顾，营收增长主要来自海外业务..."
                />
              </div>

              <div class="form-group">
                <label>额外说明（可选）</label>
                <input v-model="extraInfo" class="form-input" placeholder="补充说明或特殊要求..." />
              </div>

              <div class="form-group">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="enableSearch" />
                  <span>联网搜索相关资料</span>
                </label>
              </div>

              <div class="actions">
                <button class="btn btn-primary" :disabled="!inputText.trim() || store.loading" @click="submitPlan">
                  <span v-if="store.loading">规划中...</span>
                  <span v-else>开始规划</span>
                </button>
              </div>
            </div>

            <!-- 步骤2: 方案 -->
            <div v-else-if="isActive('plan')" class="card">
              <div class="corner-deco">02</div>
              <div class="card-title">
                <span class="icon">◈</span>
                <span>文档方案</span>
              </div>

              <div class="plan-header">
                <h2 class="plan-title">{{ store.title }}</h2>
                <p class="plan-summary">{{ store.planSummary }}</p>
              </div>

              <div class="outline-list">
                <div v-for="(item, i) in store.outline" :key="i" class="outline-item">
                  <div class="outline-header">
                    <span class="outline-level">{{ '·'.repeat(item.level) }}</span>
                    <span class="outline-title">{{ item.title }}</span>
                    <span class="outline-type">{{ item.content_type }}</span>
                  </div>
                  <div class="outline-details" v-if="item.details.length">
                    <div v-for="(d, j) in item.details" :key="j" class="outline-detail">- {{ d }}</div>
                  </div>
                </div>
              </div>

              <div class="form-group">
                <label>文档风格</label>
                <select v-model="store.selectedStyle" class="form-select">
                  <option value="formal">正式商务</option>
                  <option value="academic">学术论文</option>
                  <option value="technical">技术文档</option>
                  <option value="creative">创意文档</option>
                  <option value="report">报告风格</option>
                </select>
              </div>

              <div class="actions">
                <button class="btn btn-outline" @click="store.goToStep('input')">← 返回修改</button>
                <button class="btn btn-primary" :disabled="store.loading" @click="confirmPlan">
                  <span v-if="store.streaming">{{ store.streamProgress || '生成中...' }}</span>
                  <span v-else>确认并生成</span>
                </button>
              </div>
            </div>

            <!-- 步骤3: 预览 -->
            <div v-else-if="isActive('preview')" class="card">
              <div class="corner-deco">03</div>
              <div class="card-title">
                <span class="icon">◎</span>
                <span>预览文档</span>
              </div>

              <div class="toolbar">
                <button class="tool-btn" :class="{ active: editMode }" @click="toggleEditMode">
                  <span class="tool-icon">{{ editMode ? '✦' : '✎' }}</span>
                  <span>{{ editMode ? '编辑中' : '开始编辑' }}</span>
                </button>
                <button class="tool-btn" @click="toggleHistory">
                  <span class="tool-icon">📋</span>
                  <span>历史</span>
                </button>
              </div>

              <div class="preview-container">
                <iframe ref="iframeRef" class="preview-frame" :style="{ transform: `scale(${previewScale})` }" />
              </div>

              <Transition name="slide-up">
                <div v-if="editMode" class="save-strip">
                  <span class="save-hint">编辑模式已开启，修改后点击保存</span>
                  <div class="save-btns">
                    <button class="btn btn-outline btn-sm" @click="editMode = false; renderPreview()">取消</button>
                    <button class="btn btn-primary btn-sm" :disabled="store.loading" @click="saveEdit">保存修改</button>
                  </div>
                </div>
              </Transition>

              <div class="actions">
                <button class="btn btn-outline" @click="store.goToStep('plan')">← 返回方案</button>
                <button class="btn btn-success" :disabled="store.loading" @click="store.exportDocx()">
                  <span v-if="store.loading">导出中...</span>
                  <span v-else>导出 DOCX</span>
                </button>
              </div>
            </div>

            <!-- 步骤4: 下载 -->
            <div v-else-if="isActive('download')" class="card">
              <div class="corner-deco">04</div>
              <div class="card-title">
                <span class="icon">↓</span>
                <span>导出完成</span>
              </div>

              <div class="download-content">
                <div class="download-icon">✓</div>
                <h3>文档已生成</h3>
                <p>{{ store.title }}</p>
              </div>

              <div class="actions">
                <button class="btn btn-outline" @click="store.goToStep('preview')">← 返回预览</button>
                <button class="btn btn-primary" @click="store.reset()">创建新文档</button>
              </div>
            </div>
          </div>

          <nav class="steps-rail">
            <div class="rail-label">流程</div>
            <div class="rail-track">
              <template v-for="(s, i) in steps" :key="s.key">
                <button
                  class="rail-node"
                  :class="{ active: isActive(s.key), done: isDone(s.key) }"
                  @click="isDone(s.key) ? store.goToStep(s.key as any) : null"
                >
                  <div class="rail-dot">
                    <span v-if="isDone(s.key)" class="rail-check">✓</span>
                    <span v-else class="rail-icon">{{ s.icon }}</span>
                  </div>
                  <span class="rail-label-text">{{ s.label }}</span>
                </button>
                <div v-if="i < steps.length - 1" class="rail-arrow" :class="{ filled: isDone(s.key) }">
                  <svg width="12" height="20" viewBox="0 0 12 20" fill="none">
                    <path d="M6 0 L6 14 M2 10 L6 16 L10 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
              </template>
            </div>
          </nav>
        </div>
      </main>
    </div>

    <Transition name="fade">
      <div v-if="store.error" class="global-error" @click="store.error = ''">
        <span class="error-icon">✕</span>
        <span>{{ store.error }}</span>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}

.topbar {
  position: sticky; top: 0; z-index: 100;
  background: rgba(12, 14, 20, 0.85);
  backdrop-filter: blur(20px) saturate(1.5);
  border-bottom: 1px solid rgba(232,168,73,0.08);
}

.topbar-inner {
  max-width: 1400px; margin: 0 auto; padding: 0 32px;
  height: 56px; display: flex; align-items: center; justify-content: space-between;
}

.brand-link { display: flex; align-items: center; gap: 12px; text-decoration: none; }

.brand-mark {
  width: 34px; height: 34px;
  background: linear-gradient(135deg, var(--amber), var(--amber-dim));
  border-radius: 8px; display: flex; align-items: center; justify-content: center;
  font-size: 18px; color: var(--ink-deep); font-weight: 800;
  box-shadow: 0 2px 12px rgba(232,168,73,0.25);
}

.brand-text { display: flex; flex-direction: column; }

.brand-name { font-family: 'Noto Serif SC', serif; font-size: 16px; font-weight: 700; color: var(--text-primary); letter-spacing: 2px; line-height: 1.2; }

.brand-sub { font-family: 'JetBrains Mono', monospace; font-size: 8px; color: var(--text-muted); letter-spacing: 3px; text-transform: uppercase; }

.theme-toggle {
  width: 34px; height: 34px; border-radius: 50%;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08);
  color: var(--text-secondary); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.3s var(--ease-out);
}

.theme-toggle:hover { background: rgba(232,168,73,0.12); border-color: rgba(232,168,73,0.25); color: var(--amber); transform: rotate(30deg); }

.theme-icon { font-size: 16px; }

.topbar-btn {
  height: 34px; padding: 0 14px; border-radius: 8px;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08);
  color: var(--text-secondary); cursor: pointer; font-size: 13px;
  font-family: 'Outfit', sans-serif;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.3s var(--ease-out);
}

.topbar-btn:hover { background: rgba(232,168,73,0.12); border-color: rgba(232,168,73,0.25); color: var(--amber); }

.topbar-avatar {
  width: 24px; height: 24px; border-radius: 50%;
  background: linear-gradient(135deg, var(--amber), var(--amber-dim));
  color: var(--ink-deep);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
}

[data-theme="light"] .theme-toggle { background: rgba(0,0,0,0.04); border-color: rgba(0,0,0,0.08); }
[data-theme="light"] .topbar { background: rgba(244,241,236,0.9); border-bottom-color: rgba(0,0,0,0.06); }
[data-theme="light"] .brand-name { color: #1A1612; }
[data-theme="light"] .brand-sub { color: #9A9488; }

.app-body { flex: 1; display: flex; justify-content: center; min-height: calc(100vh - 56px); padding: 36px 48px 80px; }
.main-stage { width: 100%; max-width: 1400px; display: flex; justify-content: center; }
.content-area { display: flex; justify-content: space-between; align-items: flex-start; width: 100%; gap: 24px; }
.card-area { flex: 1; min-width: 0; }

/* 历史记录侧边栏 */
.history-sidebar {
  width: 280px;
  background: var(--ink-mid);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius);
  padding: 16px;
  position: fixed;
  left: -300px;
  top: 80px;
  z-index: 50;
  transition: left 0.3s var(--ease-out);
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}

.history-sidebar.show {
  left: 20px;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.history-header h3 {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.close-btn {
  width: 28px; height: 28px;
  border: none;
  background: rgba(255,255,255,0.06);
  color: var(--text-muted);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255,255,255,0.12);
  color: var(--text-primary);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-empty {
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
  padding: 20px 0;
}

.history-item {
  padding: 12px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  border-color: rgba(232,168,73,0.2);
  background: var(--ink);
}

.history-item.active {
  border-color: var(--amber);
  background: var(--amber-glow);
}

.item-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.item-time {
  font-size: 12px;
  color: var(--text-muted);
}

.delete-btn {
  width: 20px; height: 20px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  opacity: 0;
  transition: all 0.2s;
}

.history-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: var(--vermillion-glow);
  color: var(--vermillion);
}

.card {
  background: var(--ink-mid);
  border: 1px solid rgba(232, 168, 73, 0.08);
  border-radius: var(--radius-lg);
  padding: 32px;
  position: relative;
  box-shadow: var(--shadow-lg);
  animation: cardIn 0.5s var(--ease-out) both;
}

@keyframes cardIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.corner-deco {
  position: absolute;
  top: 16px; right: 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 42px;
  font-weight: 800;
  color: rgba(232,168,73,0.06);
  line-height: 1;
  pointer-events: none;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Noto Serif SC', serif;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.card-title .icon {
  color: var(--amber);
  font-size: 18px;
}

.history-btn {
  margin-left: auto;
  width: 32px; height: 32px;
  border: none;
  background: rgba(255,255,255,0.06);
  color: var(--text-secondary);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: all 0.2s;
}

.history-btn:hover {
  background: rgba(232,168,73,0.12);
  color: var(--amber);
}

.card-desc {
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.6;
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.form-textarea,
.form-input,
.form-select {
  width: 100%;
  padding: 12px 16px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-primary);
  font-family: 'Outfit', sans-serif;
  transition: all 0.25s var(--ease-out);
}

.form-textarea:focus,
.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--amber-dim);
  box-shadow: 0 0 0 3px var(--amber-glow);
}

.form-textarea {
  resize: vertical;
  min-height: 120px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-secondary);
}

.checkbox-label input[type="checkbox"] {
  accent-color: var(--amber);
}

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 20px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s;
  font-family: 'Outfit', sans-serif;
}

.tool-btn:hover {
  border-color: rgba(255,255,255,0.12);
  color: var(--text-primary);
  background: var(--ink);
}

.tool-btn.active {
  background: var(--amber-glow);
  border-color: var(--amber-dim);
  color: var(--amber);
}

.tool-icon { font-size: 14px; }

.plan-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.plan-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.plan-summary {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.outline-list {
  margin-bottom: 24px;
}

.outline-item {
  padding: 12px 16px;
  background: var(--ink-light);
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
}

.outline-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.outline-level {
  color: var(--amber);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}

.outline-title {
  font-weight: 600;
  color: var(--text-primary);
}

.outline-type {
  font-size: 11px;
  padding: 2px 6px;
  background: var(--amber-glow);
  color: var(--amber);
  border-radius: 4px;
  margin-left: auto;
}

.outline-details {
  padding-left: 20px;
}

.outline-detail {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.preview-container {
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 24px;
  background: white;
}

.preview-frame {
  width: 800px;
  height: 600px;
  border: none;
  transform-origin: top left;
}

/* 保存栏 */
.save-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  background: var(--amber-glow);
  border: 1px solid rgba(232,168,73,0.12);
  border-radius: var(--radius-sm);
  margin-bottom: 16px;
}

.save-hint {
  font-size: 13px;
  color: var(--amber);
  font-weight: 500;
}

.save-btns {
  display: flex;
  gap: 8px;
}

.btn-sm { padding: 8px 16px; font-size: 13px; }

.slide-up-enter-active { transition: all 0.3s var(--ease-out); }
.slide-up-leave-active { transition: all 0.2s var(--ease-out); }
.slide-up-enter-from { opacity: 0; transform: translateY(8px); }
.slide-up-leave-to { opacity: 0; transform: translateY(4px); }

.download-content {
  text-align: center;
  padding: 40px 20px;
  margin-bottom: 24px;
}

.download-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background: var(--jade);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
}

.download-content h3 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.download-content p {
  font-size: 14px;
  color: var(--text-secondary);
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}

.btn {
  padding: 12px 24px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
  font-family: 'Outfit', sans-serif;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-primary {
  background: linear-gradient(135deg, var(--amber), var(--amber-dim));
  color: var(--ink-deep);
  border: none;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(232,168,73,0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-outline {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.12);
  color: var(--text-secondary);
}

.btn-outline:hover {
  border-color: var(--amber-dim);
  color: var(--amber);
}

.btn-success {
  background: var(--jade);
  color: white;
  border: none;
}

.btn-success:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(91,168,140,0.3);
}

.btn-success:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.steps-rail { width: 64px; flex-shrink: 0; position: sticky; top: 92px; padding-top: 16px; }
.rail-label { font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: var(--text-muted); text-align: center; margin-bottom: 12px; }
.rail-track { display: flex; flex-direction: column; align-items: center; }
.rail-node { display: flex; flex-direction: column; align-items: center; gap: 6px; background: none; border: none; cursor: default; padding: 4px; transition: all 0.3s var(--ease-out); }
.rail-node.done { cursor: pointer; }
.rail-node.done:hover { transform: scale(1.1); }
.rail-dot { width: 38px; height: 38px; border-radius: 50%; background: var(--ink-light); border: 1.5px solid rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: center; transition: all 0.3s var(--ease-out); }
.rail-icon { font-size: 14px; color: var(--text-muted); transition: color 0.3s; }
.rail-check { font-size: 13px; font-weight: 700; color: white; }
.rail-node.active .rail-dot { background: var(--amber); border-color: var(--amber); box-shadow: 0 0 20px rgba(232,168,73,0.4); transform: scale(1.1); }
.rail-node.active .rail-icon { color: var(--ink-deep); }
.rail-node.done .rail-dot { background: var(--jade); border-color: var(--jade); }
.rail-label-text { font-size: 11px; font-weight: 600; color: var(--text-muted); transition: color 0.3s; }
.rail-node.active .rail-label-text { color: var(--amber); }
.rail-node.done .rail-label-text { color: var(--jade); }
.rail-arrow { display: flex; justify-content: center; color: rgba(255,255,255,0.1); margin: 2px 0; transition: color 0.4s; }
.rail-arrow.filled { color: rgba(91,168,140,0.5); }

[data-theme="light"] .card { background: #ffffff; border-color: rgba(0,0,0,0.06); }
[data-theme="light"] .form-textarea,
[data-theme="light"] .form-input,
[data-theme="light"] .form-select { background: #F0ECE5; border-color: rgba(0,0,0,0.06); color: #1A1612; }
[data-theme="light"] .outline-item { background: #F0ECE5; }
[data-theme="light"] .preview-container { border-color: rgba(0,0,0,0.06); }
[data-theme="light"] .rail-arrow { color: rgba(0,0,0,0.1); }
[data-theme="light"] .rail-dot { background: #F0ECE5; border-color: rgba(0,0,0,0.08); }
[data-theme="light"] .history-sidebar { background: #ffffff; border-color: rgba(0,0,0,0.06); }
[data-theme="light"] .history-item { background: #F0ECE5; border-color: rgba(0,0,0,0.04); }
[data-theme="light"] .close-btn { background: rgba(0,0,0,0.04); }
[data-theme="light"] .history-btn { background: rgba(0,0,0,0.04); }

.global-error { position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%); background: var(--vermillion); color: white; padding: 14px 24px; border-radius: var(--radius); font-size: 14px; font-weight: 500; display: flex; align-items: center; gap: 10px; box-shadow: 0 8px 30px rgba(212,93,76,0.4); cursor: pointer; z-index: 200; animation: errorIn 0.4s var(--ease-spring) both; }
.error-icon { width: 20px; height: 20px; background: rgba(255,255,255,0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; }
@keyframes errorIn { from { opacity: 0; transform: translateX(-50%) translateY(20px) scale(0.9); } to { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); } }

.fade-enter-active { transition: opacity 0.3s; }
.fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
