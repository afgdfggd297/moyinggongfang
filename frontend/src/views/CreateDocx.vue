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
const focused = ref(false)

// 文档风格
const docxStyles = [
  { value: 'formal', label: '正式商务', icon: '⬡', desc: '用词正式，结构严谨' },
  { value: 'academic', label: '学术论文', icon: '◎', desc: '引用规范，论证严密' },
  { value: 'technical', label: '技术文档', icon: '◈', desc: '术语准确，步骤清晰' },
  { value: 'creative', label: '创意文档', icon: '✦', desc: '语言生动，形式多样' },
  { value: 'report', label: '报告风格', icon: '○', desc: '数据驱动，结论明确' },
]

// 进度百分比（基于内容长度估算）
const progressPercent = computed(() => {
  if (!store.streaming) return 0
  const content = store.markdownContent
  if (!content) return 10
  // 假设目标内容约 5000 字符
  const targetLength = 5000
  const percent = Math.min(95, (content.length / targetLength) * 100)
  return Math.max(10, percent)
})

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
const editMode = ref(false)

// 简单的 Markdown 转 HTML 函数
function markdownToHtml(md: string): string {
  if (!md) return ''

  let html = md

  // 标题
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')

  // 粗体和斜体
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>')

  // 表格
  html = html.replace(/^\|(.+)\|$/gim, (match) => {
    const cells = match.split('|').filter(c => c.trim())
    if (cells.some(c => c.trim().match(/^[-:]+$/))) {
      return ''
    }
    const tag = 'td'
    const row = cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('')
    return `<tr>${row}</tr>`
  })
  html = html.replace(/(<tr>.*<\/tr>\n?)+/gs, '<table>$&</table>')

  // 无序列表
  html = html.replace(/^\s*[-*]\s+(.*$)/gim, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')

  // 有序列表
  html = html.replace(/^\s*\d+\.\s+(.*$)/gim, '<li>$1</li>')

  // 引用
  html = html.replace(/^\>\s+(.*$)/gim, '<blockquote>$1</blockquote>')

  // 分隔线
  html = html.replace(/^[-*_]{3,}$/gim, '<hr>')

  // 段落
  html = html.replace(/^(?!<[a-z]|$)(.*$)/gim, '<p>$1</p>')

  // 清理空行
  html = html.replace(/\n\s*\n/g, '\n')

  return html
}

const renderedHtml = computed(() => markdownToHtml(store.markdownContent))

function toggleEditMode() {
  editMode.value = !editMode.value
}

async function saveEdit() {
  await store.saveEdit()
  editMode.value = false
}
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
      <aside class="history-sidebar" :class="{ collapsed: !showHistory }">
        <!-- 折叠按钮 -->
        <button class="collapse-btn" @click="toggleHistory" :title="showHistory ? '收起' : '展开'">
          <span class="collapse-icon">{{ showHistory ? '«' : '»' }}</span>
        </button>

        <!-- 展开状态 -->
        <Transition name="sidebar-fade">
          <div v-if="showHistory" class="sidebar-content">
            <!-- 新建 -->
            <button class="new-btn" @click="store.reset()">
              <span class="new-icon">✦</span>
              <span>新建方案</span>
            </button>

            <!-- 历史列表 -->
            <div class="history-label">历史记录</div>
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
                  <span class="item-step">{{ item.step }}</span>
                </div>
                <button class="delete-btn" @click.stop="store.removeEntry(item.planId)" title="删除">✕</button>
              </div>
            </div>
          </div>
        </Transition>
      </aside>

      <main class="main-stage">
        <div class="content-area">
          <div class="card-area">
            <!-- 步骤1: 输入 -->
            <div v-if="isActive('input')" class="card input-card">
              <div class="corner-deco">01</div>
              <div class="card-title">
                <span class="icon">✦</span>
                <span>构思内容</span>
              </div>

              <p class="card-desc">
                将您的想法、大纲或素材交给 AI，它会为您规划出专业的文档方案。
              </p>

              <!-- 主输入区 -->
              <div class="input-stage" :class="{ focused }">
                <div class="input-label">
                  <span class="label-dot" />
                  文档内容
                </div>
                <textarea
                  v-model="inputText"
                  placeholder="在此输入您的文档内容…&#10;&#10;例如：关于人工智能发展趋势的分析报告，包含历史回顾、当前应用、未来展望三个部分…"
                  @focus="focused = true"
                  @blur="focused = false"
                />
                <div class="input-meta">
                  <span class="char-count" :class="{ warn: inputText.length > 2000 }">
                    {{ inputText.length }} 字
                  </span>
                </div>
              </div>

              <!-- 补充信息 -->
              <div class="extra-stage">
                <div class="input-label">
                  <span class="label-dot dim" />
                  补充说明 <span class="optional">可选</span>
                </div>
                <input
                  v-model="extraInfo"
                  type="text"
                  placeholder="面向投资人、学术汇报、公司内部分享…"
                />
              </div>

              <!-- 网络搜索开关 -->
              <div class="search-toggle-row">
                <div class="toggle-info">
                  <span class="toggle-label">联网搜索</span>
                  <span class="toggle-desc">开启后 AI 会自动搜索相关资料，生成更准确的方案</span>
                </div>
                <button
                  class="toggle-switch"
                  :class="{ on: enableSearch }"
                  @click="enableSearch = !enableSearch"
                >
                  <span class="toggle-knob" />
                </button>
              </div>

              <!-- 操作 -->
              <div class="actions">
                <button
                  class="btn btn-primary"
                  :disabled="store.loading || !inputText.trim()"
                  @click="submitPlan"
                >
                  <span v-if="store.loading" class="btn-loading">
                    <span class="btn-spinner" />
                    规划中
                  </span>
                  <span v-else>
                    <span class="btn-icon-text">→</span>
                    开始规划方案
                  </span>
                </button>
              </div>
            </div>

            <!-- 步骤2: 方案 -->
            <div v-else-if="isActive('plan')" class="card plan-card">
              <div class="corner-deco">02</div>
              <div class="card-title">
                <span class="icon">◈</span>
                <span>文档方案</span>
              </div>

              <!-- 标题 -->
              <div class="plan-title-section">
                <h2 class="plan-title">{{ store.title }}</h2>
                <p class="plan-summary">{{ store.planSummary }}</p>
              </div>

              <!-- 大纲 -->
              <div class="outline-section">
                <div class="section-label">
                  <span class="label-dot" />
                  大纲结构
                </div>
                <div class="outline-list">
                  <div v-for="(item, i) in store.outline" :key="i" class="outline-item">
                    <div class="outline-header">
                      <span class="outline-number">{{ i + 1 }}</span>
                      <span class="outline-title">{{ item.title }}</span>
                      <span class="outline-type">{{ item.content_type }}</span>
                    </div>
                    <div class="outline-details" v-if="item.details.length">
                      <div v-for="(d, j) in item.details" :key="j" class="outline-detail">
                        <span class="detail-bullet">•</span>
                        {{ d }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 风格选择 -->
              <div class="style-section">
                <div class="section-label">
                  <span class="label-dot" />
                  文档风格
                </div>
                <div class="style-grid">
                  <button
                    v-for="s in docxStyles"
                    :key="s.value"
                    class="style-card"
                    :class="{ active: store.selectedStyle === s.value }"
                    @click="store.selectedStyle = s.value"
                  >
                    <span class="style-icon">{{ s.icon }}</span>
                    <span class="style-name">{{ s.label }}</span>
                    <span class="style-desc">{{ s.desc }}</span>
                  </button>
                </div>
              </div>

              <!-- 数据来源 -->
              <div v-if="store.dataSources.length" class="sources-section">
                <div class="section-label">
                  <span class="label-dot" />
                  参考资料
                </div>
                <div class="sources-list">
                  <a v-for="(src, i) in store.dataSources" :key="i" :href="src.url" target="_blank" class="source-item">
                    <span class="source-icon">{{ src.is_trusted ? '✓' : '◎' }}</span>
                    <span class="source-title">{{ src.title }}</span>
                  </a>
                </div>
              </div>

              <!-- 操作 -->
              <div class="actions">
                <button class="btn btn-outline" @click="store.goToStep('input')">
                  <span class="btn-icon-text">←</span> 返回修改
                </button>
                <button class="btn btn-primary" :disabled="store.loading" @click="confirmPlan">
                  <span v-if="store.streaming" class="btn-loading">
                    <span class="btn-spinner" />
                    {{ store.streamProgress || '生成中...' }}
                  </span>
                  <span v-else>
                    <span class="btn-icon-text">→</span>
                    确认并生成
                  </span>
                </button>
              </div>

              <!-- 生成进度条 -->
              <Transition name="fade">
                <div v-if="store.streaming" class="progress-section">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
                  </div>
                  <div class="progress-info">
                    <span class="progress-text">{{ store.streamProgress }}</span>
                    <span class="progress-percent">{{ Math.round(progressPercent) }}%</span>
                  </div>
                </div>
              </Transition>
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
                <div class="toolbar-right">
                  <span class="content-info">
                    <span class="info-label">字数</span>
                    <span class="info-value">{{ store.markdownContent.length }}</span>
                  </span>
                </div>
              </div>

              <div class="preview-container">
                <div class="preview-content markdown-body" v-html="renderedHtml"></div>
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
                  <span v-if="store.loading" class="btn-loading">
                    <span class="btn-spinner" />
                    导出中...
                  </span>
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
  width: 220px;
  flex-shrink: 0;
  border-right: 1px solid rgba(255,255,255,0.04);
  background: rgba(12, 14, 20, 0.4);
  position: relative;
  transition: width 0.3s var(--ease-out);
  overflow: hidden;
}
.history-sidebar.collapsed {
  width: 42px;
}

.collapse-btn {
  position: absolute;
  top: 12px;
  right: 8px;
  width: 26px; height: 26px;
  border-radius: 6px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  z-index: 5;
}
.collapse-btn:hover {
  background: rgba(232,168,73,0.1);
  color: var(--amber);
}
.collapsed .collapse-btn {
  right: 50%;
  transform: translateX(50%);
}
.collapse-icon {
  font-size: 14px;
  font-weight: 700;
}

.sidebar-content {
  padding: 48px 12px 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.new-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 14px;
  background: var(--amber-glow);
  border: 1px solid rgba(232,168,73,0.15);
  border-radius: var(--radius-sm);
  color: var(--amber);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'Outfit', sans-serif;
  margin-bottom: 20px;
}
.new-btn:hover {
  background: rgba(232,168,73,0.2);
  border-color: rgba(232,168,73,0.3);
}
.new-icon { font-size: 16px; }

.history-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--text-muted);
  margin-bottom: 10px;
  padding: 0 4px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
}
.history-empty {
  font-size: 12px;
  color: var(--text-muted);
  padding: 20px 4px;
  text-align: center;
}
.history-item {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
  position: relative;
}
.history-item:hover {
  background: rgba(255,255,255,0.04);
}
.history-item.active {
  background: var(--amber-glow);
  border: 1px solid rgba(232,168,73,0.12);
}
.item-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}
.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.item-time {
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  color: var(--text-muted);
}
.item-step {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 8px;
  background: rgba(255,255,255,0.04);
  color: var(--text-muted);
  text-transform: uppercase;
}

.delete-btn {
  position: absolute;
  top: 8px; right: 8px;
  width: 20px; height: 20px;
  border-radius: 4px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s;
}
.history-item:hover .delete-btn { opacity: 1; }
.delete-btn:hover {
  background: rgba(212,93,76,0.15);
  color: var(--vermillion);
}

.sidebar-fade-enter-active { transition: opacity 0.2s 0.1s; }
.sidebar-fade-leave-active { transition: opacity 0.15s; }
.sidebar-fade-enter-from, .sidebar-fade-leave-to { opacity: 0; }

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

/* 输入区域 */
.input-stage {
  margin-bottom: 20px;
  border-radius: var(--radius);
  border: 1px solid rgba(255,255,255,0.06);
  background: var(--ink-light);
  padding: 16px;
  transition: all 0.3s var(--ease-out);
}
.input-stage.focused {
  border-color: var(--amber-dim);
  box-shadow: 0 0 0 3px var(--amber-glow);
  background: var(--ink);
}

.input-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-bottom: 10px;
}

.label-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--amber);
}
.label-dot.dim { opacity: 0.4; }

.input-stage textarea {
  width: 100%;
  min-height: 120px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 15px;
  line-height: 1.7;
  resize: vertical;
  outline: none;
  font-family: 'Noto Sans SC', 'Outfit', sans-serif;
}
.input-stage textarea::placeholder { color: var(--text-muted); }

.input-meta {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
.char-count {
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  color: var(--text-muted);
}
.char-count.warn { color: var(--vermillion); }

/* 补充信息 */
.extra-stage {
  margin-bottom: 20px;
}
.extra-stage input {
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
.extra-stage input:focus {
  outline: none;
  border-color: var(--amber-dim);
  box-shadow: 0 0 0 3px var(--amber-glow);
}
.optional {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
  background: rgba(255,255,255,0.04);
  color: var(--text-muted);
  text-transform: none;
  letter-spacing: 0;
}

/* 搜索开关 */
.search-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: var(--radius);
  margin-bottom: 24px;
}
.toggle-info { flex: 1; }
.toggle-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.toggle-desc {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.4;
}
.toggle-switch {
  width: 44px; height: 24px;
  border-radius: 12px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.08);
  cursor: pointer;
  position: relative;
  transition: all 0.3s;
  flex-shrink: 0;
  margin-left: 16px;
}
.toggle-switch.on {
  background: var(--amber);
  border-color: var(--amber);
}
.toggle-knob {
  position: absolute;
  top: 2px; left: 2px;
  width: 18px; height: 18px;
  border-radius: 50%;
  background: white;
  transition: transform 0.3s var(--ease-spring);
  box-shadow: 0 1px 4px rgba(0,0,0,0.2);
}
.toggle-switch.on .toggle-knob {
  transform: translateX(20px);
}

/* 按钮加载态 */
.btn-loading {
  display: flex;
  align-items: center;
  gap: 8px;
}
.btn-spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(12,14,20,0.2);
  border-top-color: var(--ink-deep);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

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

.toolbar-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 16px;
}

.content-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.info-label {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.info-value {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: var(--text-secondary);
}

/* 进度条 */
.progress-section {
  margin-top: 16px;
  padding: 16px;
  background: var(--ink-light);
  border-radius: var(--radius);
  border: 1px solid rgba(255,255,255,0.04);
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(255,255,255,0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--amber), var(--amber-dim));
  border-radius: 4px;
  transition: width 0.3s var(--ease-out);
}

.progress-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.progress-text {
  font-size: 13px;
  color: var(--text-secondary);
}

.progress-percent {
  font-size: 13px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: var(--amber);
}

/* 方案页面 */
.plan-title-section {
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

.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-bottom: 12px;
}

.outline-section {
  margin-bottom: 24px;
}

.outline-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.outline-item {
  padding: 12px 16px;
  background: var(--ink-light);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.2s;
}

.outline-item:hover {
  border-color: rgba(232,168,73,0.15);
}

.outline-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.outline-number {
  width: 22px; height: 22px;
  border-radius: 50%;
  background: var(--amber-glow);
  color: var(--amber);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  flex-shrink: 0;
}

.outline-title {
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.outline-type {
  font-size: 10px;
  padding: 2px 8px;
  background: rgba(255,255,255,0.04);
  color: var(--text-muted);
  border-radius: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.outline-details {
  padding-left: 32px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.outline-detail {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  display: flex;
  gap: 8px;
}

.detail-bullet {
  color: var(--text-muted);
  flex-shrink: 0;
}

/* 风格选择 */
.style-section {
  margin-bottom: 24px;
}

.style-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.style-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 10px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.style-card:hover {
  border-color: rgba(255,255,255,0.12);
  background: var(--ink);
}

.style-card.active {
  border-color: var(--amber);
  background: var(--amber-glow);
}

.style-icon {
  font-size: 20px;
  color: var(--text-muted);
  transition: color 0.2s;
}

.style-card.active .style-icon {
  color: var(--amber);
}

.style-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.style-desc {
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
  line-height: 1.3;
}

/* 数据来源 */
.sources-section {
  margin-bottom: 24px;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--ink-light);
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: all 0.2s;
}

.source-item:hover {
  background: var(--ink);
}

.source-icon {
  font-size: 12px;
  color: var(--jade);
}

.source-title {
  font-size: 13px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-container {
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 24px;
  background: white;
  max-height: 600px;
  overflow-y: auto;
}

.preview-content {
  padding: 32px 40px;
  min-height: 400px;
}

/* Markdown 样式 */
.markdown-body h1 {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e8a849;
}

.markdown-body h2 {
  font-size: 22px;
  font-weight: 600;
  color: #2c3e50;
  margin-top: 32px;
  margin-bottom: 16px;
}

.markdown-body h3 {
  font-size: 18px;
  font-weight: 600;
  color: #34495e;
  margin-top: 24px;
  margin-bottom: 12px;
}

.markdown-body p {
  font-size: 15px;
  line-height: 1.8;
  color: #333;
  margin-bottom: 12px;
}

.markdown-body ul,
.markdown-body ol {
  margin-bottom: 12px;
  padding-left: 24px;
}

.markdown-body li {
  font-size: 15px;
  line-height: 1.6;
  margin-bottom: 6px;
}

.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.markdown-body th,
.markdown-body td {
  border: 1px solid #ddd;
  padding: 10px 14px;
  text-align: left;
  font-size: 14px;
}

.markdown-body th {
  background: #f5f5f5;
  font-weight: 600;
}

.markdown-body tr:nth-child(even) {
  background: #fafafa;
}

.markdown-body blockquote {
  border-left: 4px solid #e8a849;
  padding-left: 16px;
  margin-left: 0;
  color: #666;
  font-style: italic;
  margin-bottom: 12px;
}

.markdown-body hr {
  border: none;
  border-top: 1px solid #ddd;
  margin: 32px 0;
}

.markdown-body strong {
  font-weight: 700;
  color: #1a1a1a;
}

.markdown-body em {
  font-style: italic;
}

/* 预览滚动条 */
.preview-container::-webkit-scrollbar { width: 8px; }
.preview-container::-webkit-scrollbar-track { background: #f5f5f5; }
.preview-container::-webkit-scrollbar-thumb { background: #ddd; border-radius: 4px; }
.preview-container::-webkit-scrollbar-thumb:hover { background: #bbb; }

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
[data-theme="light"] .input-stage { background: #F0ECE5; border-color: rgba(0,0,0,0.06); }
[data-theme="light"] .input-stage.focused { background: #ffffff; }
[data-theme="light"] .extra-stage input { background: #F0ECE5; border-color: rgba(0,0,0,0.06); color: #1A1612; }
[data-theme="light"] .search-toggle-row { background: #F0ECE5; border-color: rgba(0,0,0,0.04); }
[data-theme="light"] .outline-item { background: #F0ECE5; border-color: rgba(0,0,0,0.04); }
[data-theme="light"] .outline-item:hover { border-color: rgba(232,168,73,0.2); }
[data-theme="light"] .style-card { background: #F0ECE5; border-color: rgba(0,0,0,0.04); }
[data-theme="light"] .style-card:hover { border-color: rgba(0,0,0,0.1); background: #E8E4DD; }
[data-theme="light"] .source-item { background: #F0ECE5; }
[data-theme="light"] .source-item:hover { background: #E8E4DD; }
[data-theme="light"] .preview-container { border-color: rgba(0,0,0,0.06); background: #ffffff; }
[data-theme="light"] .rail-arrow { color: rgba(0,0,0,0.1); }
[data-theme="light"] .rail-dot { background: #F0ECE5; border-color: rgba(0,0,0,0.08); }
[data-theme="light"] .history-sidebar {
  border-right-color: rgba(0,0,0,0.06);
  background: rgba(244,241,236,0.5);
}
[data-theme="light"] .collapse-btn {
  background: rgba(0,0,0,0.03);
  border-color: rgba(0,0,0,0.06);
}
[data-theme="light"] .history-item:hover {
  background: rgba(0,0,0,0.03);
}
[data-theme="light"] .history-btn { background: rgba(0,0,0,0.04); }
[data-theme="light"] .progress-section { background: #F0ECE5; border-color: rgba(0,0,0,0.04); }
[data-theme="light"] .progress-bar { background: rgba(0,0,0,0.1); }

.global-error { position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%); background: var(--vermillion); color: white; padding: 14px 24px; border-radius: var(--radius); font-size: 14px; font-weight: 500; display: flex; align-items: center; gap: 10px; box-shadow: 0 8px 30px rgba(212,93,76,0.4); cursor: pointer; z-index: 200; animation: errorIn 0.4s var(--ease-spring) both; }
.error-icon { width: 20px; height: 20px; background: rgba(255,255,255,0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; }
@keyframes errorIn { from { opacity: 0; transform: translateX(-50%) translateY(20px) scale(0.9); } to { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); } }

.fade-enter-active { transition: opacity 0.3s; }
.fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
