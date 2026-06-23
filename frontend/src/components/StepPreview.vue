<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { usePptStore } from '../stores/ppt'
import * as pptApi from '../api/ppt'

const store = usePptStore()
const iframeRef = ref<HTMLIFrameElement | null>(null)
const viewportRef = ref<HTMLDivElement | null>(null)
const fullscreenRef = ref<HTMLDivElement | null>(null)
const editMode = ref(false)
const slideCount = ref(0)
const isRefreshing = ref(false)
const previewScale = ref(0.7)
const currentSlide = ref(0)
const showThumbnails = ref(true)
const slidesHtml = ref<string[]>([])
const isFullscreen = ref(false)

// 单页重生成
const showRegenDialog = ref(false)
const regenSlideIndex = ref(0)
const regenInstruction = ref('')
const regenerating = ref(false)
const regeneratingSlide = ref(-1)

const IFRAME_W = 1280
const IFRAME_H = 720

function calcScale() {
  if (!viewportRef.value) return
  const containerW = viewportRef.value.clientWidth
  previewScale.value = Math.min(containerW / IFRAME_W, 1)
  viewportRef.value.style.setProperty('--preview-scale', String(previewScale.value))
}

onMounted(() => {
  calcScale()
  renderPreview()
  window.addEventListener('resize', calcScale)
  document.addEventListener('fullscreenchange', onFullscreenChange)
})
onUnmounted(() => {
  window.removeEventListener('resize', calcScale)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
})
watch(() => store.htmlContent, () => renderPreview())

function renderPreview() {
  if (!iframeRef.value || !store.htmlContent) return
  const doc = iframeRef.value.contentDocument || iframeRef.value.contentWindow?.document
  if (!doc) return

  doc.open()
  doc.write(store.htmlContent)
  doc.close()

  setTimeout(() => {
    try {
      const slides = doc.querySelectorAll('.slide')
      slideCount.value = slides.length
      slidesHtml.value = Array.from(slides).map(s => (s as HTMLElement).outerHTML)
    } catch {
      slideCount.value = 0
      slidesHtml.value = []
    }
  }, 300)
}

function scrollToSlide(index: number) {
  if (!iframeRef.value) return
  const doc = iframeRef.value.contentDocument || iframeRef.value.contentWindow?.document
  if (!doc) return
  const slides = doc.querySelectorAll('.slide')
  if (index >= 0 && index < slides.length) {
    slides[index].scrollIntoView({ behavior: 'smooth', block: 'start' })
    currentSlide.value = index
  }
}

function toggleEditMode() {
  editMode.value = !editMode.value
  const doc = iframeRef.value?.contentDocument || iframeRef.value?.contentWindow?.document
  if (!doc) return

  const body = doc.body
  if (editMode.value) {
    body.contentEditable = 'true'
    body.style.cursor = 'text'
    doc.querySelectorAll('.slide-title, .card, p, h1, h2, h3, li, td').forEach(el => {
      (el as HTMLElement).style.outline = '1px dashed rgba(232,168,73,0.35)'
      ;(el as HTMLElement).style.outlineOffset = '3px'
      ;(el as HTMLElement).style.transition = 'outline 0.2s'
    })
  } else {
    body.contentEditable = 'false'
    body.style.cursor = ''
    doc.querySelectorAll('[style*="outline"]').forEach(el => {
      (el as HTMLElement).style.outline = ''
      ;(el as HTMLElement).style.outlineOffset = ''
      ;(el as HTMLElement).style.transition = ''
    })
  }
}

function refreshPreview() {
  editMode.value = false
  isRefreshing.value = true
  renderPreview()
  setTimeout(() => { isRefreshing.value = false }, 500)
}

function toggleFullscreen() {
  if (!fullscreenRef.value) return

  if (!isFullscreen.value) {
    if (fullscreenRef.value.requestFullscreen) {
      fullscreenRef.value.requestFullscreen()
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
    }
  }
}

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement

  if (isFullscreen.value) {
    // 计算全屏缩放比例
    const scaleX = window.innerWidth / IFRAME_W
    const scaleY = window.innerHeight / IFRAME_H
    const scale = Math.min(scaleX, scaleY)
    fullscreenRef.value?.style.setProperty('--fullscreen-scale', String(scale))
  }
}

async function saveEdit() {
  const doc = iframeRef.value?.contentDocument || iframeRef.value?.contentWindow?.document
  if (!doc) return
  store.htmlContent = doc.documentElement.outerHTML
  await store.saveEdit()
  editMode.value = false
  renderPreview()
}

function openRegenDialog() {
  regenSlideIndex.value = currentSlide.value
  regenInstruction.value = ''
  showRegenDialog.value = true
}

async function confirmRegen() {
  if (!store.planId) return
  regenerating.value = true
  regeneratingSlide.value = regenSlideIndex.value
  showRegenDialog.value = false

  try {
    const result = await pptApi.regenerateSlide(
      store.planId,
      regenSlideIndex.value,
      regenInstruction.value
    )
    store.htmlContent = result.html_content
    renderPreview()
  } catch (e) {
    console.error('重生成失败:', e)
    alert('重生成失败，请重试')
  } finally {
    regenerating.value = false
    regeneratingSlide.value = -1
  }
}
</script>

<template>
  <div class="card preview-card">
    <div class="corner-deco">03</div>

    <div class="card-title">
      <span class="icon">◎</span>
      <span>预览与编辑</span>
    </div>

    <p class="card-desc">
      在下方预览生成的演示文稿。开启编辑模式后，可直接点击文字进行修改。
    </p>

    <!-- 工具栏 -->
    <div class="toolbar">
      <button class="tool-btn" :class="{ active: editMode }" @click="toggleEditMode">
        <span class="tool-icon">{{ editMode ? '✦' : '✎' }}</span>
        <span>{{ editMode ? '编辑中' : '开始编辑' }}</span>
      </button>
      <button class="tool-btn" @click="refreshPreview" :disabled="isRefreshing">
        <span class="tool-icon" :class="{ spinning: isRefreshing }">↻</span>
        <span>刷新</span>
      </button>
      <button class="tool-btn" :class="{ active: showThumbnails }" @click="showThumbnails = !showThumbnails">
        <span class="tool-icon">▦</span>
        <span>缩略图</span>
      </button>
      <button class="tool-btn" @click="openRegenDialog" :disabled="regenerating || slideCount === 0" title="重新生成某一页">
        <span class="tool-icon" :class="{ spinning: regenerating }">⟳</span>
        <span>{{ regenerating ? `重生成第${regeneratingSlide + 1}页` : '单页重生成' }}</span>
      </button>
      <button class="tool-btn" @click="toggleFullscreen" title="全屏预览">
        <span class="tool-icon">{{ isFullscreen ? '⊡' : '⛶' }}</span>
        <span>{{ isFullscreen ? '退出全屏' : '全屏' }}</span>
      </button>
      <div class="toolbar-right">
        <span v-if="editMode" class="edit-indicator">
          <span class="indicator-dot" />
          直接点击文字修改
        </span>
        <span class="slide-count">
          <span class="count-num">{{ currentSlide + 1 }}</span>
          <span class="count-sep">/</span>
          <span class="count-num">{{ slideCount }}</span>
        </span>
      </div>
    </div>

    <!-- 主预览区 -->
    <div ref="fullscreenRef" class="preview-layout" :class="{ 'is-fullscreen': isFullscreen }">
      <!-- 缩略图侧边栏 -->
      <Transition name="sidebar">
        <div v-if="showThumbnails && slideCount > 0 && !isFullscreen" class="thumbnail-sidebar">
          <div class="thumbnail-list">
            <div
              v-for="(_, i) in slidesHtml"
              :key="i"
              class="thumbnail-item"
              :class="{ active: currentSlide === i, regenerating: regeneratingSlide === i }"
              @click="scrollToSlide(i)"
            >
              <div class="thumbnail-frame">
                <div class="thumbnail-content" v-html="slidesHtml[i]" />
              </div>
              <span class="thumbnail-label">{{ i + 1 }}</span>
              <div v-if="regeneratingSlide === i" class="thumbnail-loading">
                <span class="spinner-sm" />
              </div>
            </div>
          </div>
        </div>
      </Transition>

      <!-- 主预览 -->
      <div ref="viewportRef" class="preview-viewport" :class="{ editing: editMode }">
        <div class="viewport-chrome">
          <span class="dot r" /><span class="dot y" /><span class="dot g" />
          <span class="chrome-title">预览 — {{ store.title }}</span>
        </div>
        <div class="preview-scaler">
          <iframe ref="iframeRef" class="preview-frame" />
        </div>
      </div>
    </div>

    <!-- 保存栏 -->
    <Transition name="slide-up">
      <div v-if="editMode" class="save-strip">
        <span class="save-hint">编辑模式已开启，修改后点击保存</span>
        <div class="save-btns">
          <button class="btn btn-outline btn-sm" @click="editMode = false; renderPreview()">取消</button>
          <button class="btn btn-primary btn-sm" :disabled="store.loading" @click="saveEdit">保存修改</button>
        </div>
      </div>
    </Transition>

    <!-- 单页重生成对话框 -->
    <Transition name="modal">
      <div v-if="showRegenDialog" class="modal-overlay" @click.self="showRegenDialog = false">
        <div class="modal-card">
          <h3 class="modal-title">单页重生成</h3>
          <div class="modal-field">
            <label>选择页码</label>
            <select v-model="regenSlideIndex" class="modal-select">
              <option v-for="i in slideCount" :key="i - 1" :value="i - 1">第 {{ i }} 页</option>
            </select>
          </div>
          <div class="modal-field">
            <label>调整指令（可选）</label>
            <input v-model="regenInstruction" type="text" class="modal-input" placeholder="如：更简洁、换个配色、加个图表..." />
          </div>
          <div class="modal-actions">
            <button class="btn btn-outline btn-sm" @click="showRegenDialog = false">取消</button>
            <button class="btn btn-primary btn-sm" @click="confirmRegen">开始重生成</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 操作 -->
    <div class="actions">
      <button class="btn btn-outline" @click="store.goToStep('plan')">← 返回方案</button>
      <button class="btn btn-success" :disabled="store.loading" @click="store.exportPpt()">
        <span v-if="store.loading">导出中…</span>
        <span v-else><span class="btn-icon-text">→</span> 确认并导出 PPT</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.preview-card { animation-delay: 0.05s; }

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

.card-desc {
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.6;
  margin-bottom: 24px;
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
.spinning { animation: spin 0.8s linear infinite; }

.toolbar-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 16px;
}
.edit-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--amber);
  font-weight: 600;
}
.indicator-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--amber);
  animation: pulse 1.5s ease infinite;
}
.slide-count {
  font-size: 13px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 2px;
}
.count-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: var(--text-secondary);
}
.count-sep { opacity: 0.4; }

/* 主预览区布局 */
.preview-layout {
  display: flex;
  gap: 12px;
  min-height: 400px;
}
.preview-layout.is-fullscreen {
  background: var(--ink-deep);
  padding: 0;
  gap: 0;
  align-items: stretch;
  justify-content: stretch;
  width: 100vw;
  height: 100vh;
}
.preview-layout.is-fullscreen .preview-viewport {
  flex: 1;
  border: none;
  border-radius: 0;
  display: flex;
  flex-direction: column;
}
.preview-layout.is-fullscreen .viewport-chrome {
  display: none;
}
.preview-layout.is-fullscreen .preview-scaler {
  flex: 1;
  width: 100%;
  height: 100%;
  max-width: none;
  max-height: none;
  border-radius: 0;
  overflow: auto;
}
.preview-layout.is-fullscreen .preview-frame {
  width: 1280px;
  height: 720px;
  transform-origin: top left;
  transform: scale(var(--fullscreen-scale, 1));
}

/* 缩略图侧边栏 */
.thumbnail-sidebar {
  width: 100px;
  flex-shrink: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 4px;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius);
  background: var(--ink-light);
}
.thumbnail-sidebar::-webkit-scrollbar { width: 4px; }
.thumbnail-sidebar::-webkit-scrollbar-track { background: transparent; }
.thumbnail-sidebar::-webkit-scrollbar-thumb { background: var(--ink-lighter); border-radius: 2px; }

.thumbnail-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.thumbnail-item {
  position: relative;
  cursor: pointer;
  border-radius: 6px;
  overflow: hidden;
  border: 2px solid transparent;
  transition: all 0.2s;
}
.thumbnail-item:hover {
  border-color: rgba(232,168,73,0.3);
}
.thumbnail-item.active {
  border-color: var(--amber);
  box-shadow: 0 0 8px rgba(232,168,73,0.2);
}
.thumbnail-item.regenerating {
  opacity: 0.6;
}

.thumbnail-frame {
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: white;
  border-radius: 4px;
  position: relative;
}

.thumbnail-content {
  width: 1280px;
  height: 720px;
  transform-origin: top left;
  transform: scale(0.1);
  pointer-events: none;
  position: absolute;
  top: 0;
  left: 0;
}

.thumbnail-label {
  display: block;
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  padding: 4px 0;
  font-family: 'JetBrains Mono', monospace;
}
.thumbnail-item.active .thumbnail-label {
  color: var(--amber);
}

.thumbnail-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.5);
  border-radius: 4px;
}
.spinner-sm {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255,255,255,0.2);
  border-top-color: var(--amber);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

/* 预览视口 */
.preview-viewport {
  flex: 1;
  min-width: 0;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--ink);
  transition: border-color 0.3s;
}
.preview-viewport.editing {
  border-color: var(--amber-dim);
  box-shadow: 0 0 0 2px var(--amber-glow);
}
.viewport-chrome {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--ink-light);
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.dot {
  width: 10px; height: 10px;
  border-radius: 50%;
}
.dot.r { background: #FF5F57; }
.dot.y { background: #FFBD2E; }
.dot.g { background: #28C840; }
.chrome-title {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: 8px;
  font-family: 'JetBrains Mono', monospace;
}
.preview-frame {
  width: 1280px;
  height: 720px;
  border: none;
  background: white;
  transform-origin: top left;
  transform: scale(var(--preview-scale, 0.7));
}
.preview-scaler {
  overflow: hidden;
  width: calc(1280px * var(--preview-scale, 0.7));
  height: calc(720px * var(--preview-scale, 0.7));
  background: var(--ink);
  border-radius: 0 0 var(--radius) var(--radius);
}
.preview-scaler::-webkit-scrollbar { width: 8px; height: 8px; }
.preview-scaler::-webkit-scrollbar-track { background: var(--ink-light); border-radius: 4px; }
.preview-scaler::-webkit-scrollbar-thumb { background: var(--ink-lighter); border-radius: 4px; }
.preview-scaler::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
.preview-scaler::-webkit-scrollbar-corner { background: var(--ink-light); }

[data-theme="light"] .preview-scaler { background: #E5E1DA; }
[data-theme="light"] .preview-scaler::-webkit-scrollbar-track { background: #F0ECE5; }
[data-theme="light"] .preview-scaler::-webkit-scrollbar-thumb { background: #D4CEC2; }
[data-theme="light"] .preview-scaler::-webkit-scrollbar-thumb:hover { background: #9A9488; }
[data-theme="light"] .preview-scaler::-webkit-scrollbar-corner { background: #F0ECE5; }
[data-theme="light"] .thumbnail-sidebar { background: #F0ECE5; border-color: rgba(0,0,0,0.06); }
[data-theme="light"] .thumbnail-frame { background: white; }

/* 保存栏 */
.save-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  background: var(--amber-glow);
  border: 1px solid rgba(232,168,73,0.12);
  border-radius: var(--radius-sm);
  margin-top: 12px;
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

.btn-icon-text {
  font-size: 16px;
  transition: transform 0.25s var(--ease-spring);
}
.btn:hover .btn-icon-text { transform: translateX(3px); }

/* 过渡 */
.slide-up-enter-active { transition: all 0.3s var(--ease-out); }
.slide-up-leave-active { transition: all 0.2s var(--ease-out); }
.slide-up-enter-from { opacity: 0; transform: translateY(8px); }
.slide-up-leave-to { opacity: 0; transform: translateY(4px); }

.sidebar-enter-active { transition: all 0.3s var(--ease-out); }
.sidebar-leave-active { transition: all 0.2s var(--ease-out); }
.sidebar-enter-from { opacity: 0; width: 0; }
.sidebar-leave-to { opacity: 0; width: 0; }

/* 模态框 */
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
  padding: 28px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}
.modal-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 20px;
}
.modal-field {
  margin-bottom: 16px;
}
.modal-field label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.modal-select,
.modal-input {
  width: 100%;
  padding: 10px 12px;
  background: var(--ink-light);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-primary);
  font-family: 'Outfit', sans-serif;
}
.modal-select:focus,
.modal-input:focus {
  outline: none;
  border-color: var(--amber-dim);
  box-shadow: 0 0 0 3px var(--amber-glow);
}
.modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 20px;
}

.modal-enter-active { transition: opacity 0.3s var(--ease-out); }
.modal-leave-active { transition: opacity 0.2s var(--ease-out); }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-active .modal-card { animation: modalIn 0.3s var(--ease-spring) both; }
.modal-leave-active .modal-card { animation: modalOut 0.2s var(--ease-out) both; }
@keyframes modalIn {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
@keyframes modalOut {
  from { opacity: 1; transform: scale(1) translateY(0); }
  to { opacity: 0; transform: scale(0.95) translateY(10px); }
}
</style>
