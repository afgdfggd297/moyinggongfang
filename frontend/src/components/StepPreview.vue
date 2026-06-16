<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { usePptStore } from '../stores/ppt'

const store = usePptStore()
const iframeRef = ref<HTMLIFrameElement | null>(null)
const viewportRef = ref<HTMLDivElement | null>(null)
const editMode = ref(false)
const slideCount = ref(0)
const isRefreshing = ref(false)
const previewScale = ref(0.8)
const viewportHeight = ref(600)

const IFRAME_W = 1280
const IFRAME_H = 720

function calcScale() {
  if (!viewportRef.value) return
  const containerW = viewportRef.value.clientWidth
  const scale = Math.min(containerW / IFRAME_W, 1)
  previewScale.value = scale
  // 不限制高度，让滚动条处理
  viewportHeight.value = Math.floor(IFRAME_H * scale)
  viewportRef.value.style.setProperty('--preview-scale', String(scale))
}

onMounted(() => {
  calcScale()
  renderPreview()
  window.addEventListener('resize', calcScale)
})
onUnmounted(() => {
  window.removeEventListener('resize', calcScale)
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
    } catch { slideCount.value = 0 }
  }, 300)
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

async function saveEdit() {
  const doc = iframeRef.value?.contentDocument || iframeRef.value?.contentWindow?.document
  if (!doc) return
  store.htmlContent = doc.documentElement.outerHTML
  await store.saveEdit()
  editMode.value = false
  renderPreview()
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
      <button
        class="tool-btn"
        :class="{ active: editMode }"
        @click="toggleEditMode"
      >
        <span class="tool-icon">{{ editMode ? '✦' : '✎' }}</span>
        <span>{{ editMode ? '编辑中' : '开始编辑' }}</span>
      </button>
      <button class="tool-btn" @click="refreshPreview" :disabled="isRefreshing">
        <span class="tool-icon" :class="{ spinning: isRefreshing }">↻</span>
        <span>刷新</span>
      </button>
      <div class="toolbar-right">
        <span v-if="editMode" class="edit-indicator">
          <span class="indicator-dot" />
          直接点击文字修改
        </span>
        <span class="slide-count">
          <span class="count-num">{{ slideCount }}</span> 页
        </span>
      </div>
    </div>

    <!-- 预览区 -->
    <div ref="viewportRef" class="preview-viewport" :class="{ editing: editMode }">
      <div class="viewport-chrome">
        <span class="dot r" /><span class="dot y" /><span class="dot g" />
        <span class="chrome-title">预览 — {{ store.title }}</span>
      </div>
      <div class="preview-scaler">
        <iframe
          ref="iframeRef"
          class="preview-frame"
        />
      </div>
    </div>

    <!-- 保存栏 -->
    <Transition name="slide-up">
      <div v-if="editMode" class="save-strip">
        <span class="save-hint">编辑模式已开启，修改后点击保存</span>
        <div class="save-btns">
          <button class="btn btn-outline btn-sm" @click="editMode = false; renderPreview()">取消</button>
          <button class="btn btn-primary btn-sm" :disabled="store.loading" @click="saveEdit">
            保存修改
          </button>
        </div>
      </div>
    </Transition>

    <!-- 操作 -->
    <div class="actions">
      <button class="btn btn-outline" @click="store.goToStep('plan')">← 返回方案</button>
      <button class="btn btn-success" :disabled="store.loading" @click="store.exportPpt()">
        <span v-if="store.loading">导出中…</span>
        <span v-else>
          <span class="btn-icon-text">→</span>
          确认并导出 PPT
        </span>
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
}
.count-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: var(--text-secondary);
}

/* 预览视口 */
.preview-viewport {
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
  transform: scale(var(--preview-scale, 0.8));
}
.preview-scaler {
  overflow: auto;
  max-height: 520px;
  background: var(--ink);
}
/* 滚动条样式 - 暗色 */
.preview-scaler::-webkit-scrollbar { width: 8px; height: 8px; }
.preview-scaler::-webkit-scrollbar-track { background: var(--ink-light); border-radius: 4px; }
.preview-scaler::-webkit-scrollbar-thumb { background: var(--ink-lighter); border-radius: 4px; }
.preview-scaler::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
.preview-scaler::-webkit-scrollbar-corner { background: var(--ink-light); }

/* 滚动条样式 - 亮色 */
[data-theme="light"] .preview-scaler { background: #E5E1DA; }
[data-theme="light"] .preview-scaler::-webkit-scrollbar-track { background: #F0ECE5; }
[data-theme="light"] .preview-scaler::-webkit-scrollbar-thumb { background: #D4CEC2; }
[data-theme="light"] .preview-scaler::-webkit-scrollbar-thumb:hover { background: #9A9488; }
[data-theme="light"] .preview-scaler::-webkit-scrollbar-corner { background: #F0ECE5; }

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
</style>
