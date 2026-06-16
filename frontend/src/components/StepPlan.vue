<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { usePptStore } from '../stores/ppt'
import type { StyleType, ColorType, OutlineItem } from '../types/ppt'
import draggable from 'vuedraggable'

const store = usePptStore()

const editingTitle = ref(false)
const editTitle = ref('')
const editingOutline = ref(false)
const editOutline = ref<OutlineItem[]>([])
const drag = ref(false)

const styles: { value: StyleType; label: string; icon: string; desc: string }[] = [
  { value: 'business', label: '商务', icon: '⬡', desc: '简洁专业，适合正式场合' },
  { value: 'academic', label: '学术', icon: '◎', desc: '严谨规范，适合论文答辩' },
  { value: 'creative', label: '创意', icon: '◈', desc: '活泼生动，适合头脑风暴' },
  { value: 'minimal', label: '极简', icon: '○', desc: '干净清爽，留白为主' },
]

const colors: { value: ColorType; label: string; cssClass: string; hex: string }[] = [
  { value: 'blue', label: '靛蓝', cssClass: 'color-blue', hex: '#4F46E5' },
  { value: 'green', label: '翡翠', cssClass: 'color-green', hex: '#059669' },
  { value: 'red', label: '朱砂', cssClass: 'color-red', hex: '#DC2626' },
  { value: 'purple', label: '紫檀', cssClass: 'color-purple', hex: '#7C3AED' },
  { value: 'dark', label: '墨色', cssClass: 'color-dark', hex: '#374151' },
]

const customColorInput = ref('')
const showCustomStyle = ref(false)
const showAdvanced = ref(false)

function toggleColor(value: ColorType) {
  const idx = store.selectedColors.indexOf(value)
  if (idx >= 0) {
    store.selectedColors.splice(idx, 1)
  } else {
    store.selectedColors.push(value)
  }
}

function addCustomColor() {
  const hex = customColorInput.value.trim()
  if (hex && /^#[0-9a-fA-F]{3,8}$/.test(hex) && !store.customColors.includes(hex)) {
    store.customColors.push(hex)
    customColorInput.value = ''
  }
}

function removeCustomColor(i: number) {
  store.customColors.splice(i, 1)
}

const outlineDisplay = computed(() => store.outline)

function startEditTitle() {
  editTitle.value = store.title
  editingTitle.value = true
}
async function saveTitle() {
  store.title = editTitle.value
  await store.updatePlan({ title: editTitle.value })
  editingTitle.value = false
}

function startEditOutline() {
  editOutline.value = store.outline.map(item => ({
    title: item.title,
    details: [...item.details],
  }))
  editingOutline.value = true
}
async function saveOutline() {
  const filtered = editOutline.value.filter(item => item.title.trim())
  store.outline = filtered
  store.selectedPages = filtered.length
  await store.updatePlan({ outline: filtered })
  editingOutline.value = false
}
function addOutlineItem() {
  editOutline.value.push({ title: '', details: [''] })
}
function removeOutlineItem(i: number) {
  editOutline.value.splice(i, 1)
}
function addDetail(i: number) {
  editOutline.value[i].details.push('')
}
function removeDetail(i: number, j: number) {
  editOutline.value[i].details.splice(j, 1)
}
</script>

<template>
  <div class="card plan-card">
    <div class="corner-deco">02</div>

    <div class="card-title">
      <span class="icon">◈</span>
      <span>确认方案</span>
    </div>

    <!-- 流式进度 -->
    <Transition name="fade">
      <div v-if="store.streaming" class="stream-bar">
        <div class="stream-pulse" />
        <div class="stream-info">
          <span class="stream-label">正在生成演示文稿</span>
          <span class="stream-meta">{{ store.streamingContent.length }} 字符已输出</span>
        </div>
        <div class="stream-progress">
          <div class="stream-progress-bar" />
        </div>
      </div>
    </Transition>

    <!-- 方案摘要 -->
    <div class="plan-meta">
      <div class="meta-badge">
        <span class="badge-label">方案 ID</span>
        <span class="badge-value mono">{{ store.planId }}</span>
      </div>
    </div>

    <!-- 标题 -->
    <section class="section">
      <div class="section-head">
        <h3 class="section-title">
          <span class="section-icon">§</span>
          演示文稿标题
        </h3>
        <button v-if="!editingTitle" class="edit-btn" @click="startEditTitle">
          <span class="edit-icon">✎</span> 编辑
        </button>
      </div>
      <div v-if="editingTitle" class="inline-editor">
        <input
          v-model="editTitle"
          type="text"
          class="editor-input"
          @keyup.enter="saveTitle"
        />
        <button class="btn btn-primary btn-sm" @click="saveTitle">保存</button>
        <button class="btn btn-outline btn-sm" @click="editingTitle = false">取消</button>
      </div>
      <div v-else class="plan-title-display" @click="startEditTitle">
        {{ store.title }}
      </div>
    </section>

    <!-- 大纲 -->
    <section class="section">
      <div class="section-head">
        <h3 class="section-title">
          <span class="section-icon">≡</span>
          大纲结构
        </h3>
        <button v-if="!editingOutline" class="edit-btn" @click="startEditOutline">
          <span class="edit-icon">✎</span> 编辑
        </button>
      </div>

      <!-- 编辑模式 -->
      <div v-if="editingOutline" class="outline-editor">
        <draggable
          v-model="editOutline"
          item-key="title"
          handle=".drag-handle"
          animation="200"
          @start="drag = true"
          @end="drag = false"
        >
          <template #item="{ element: item, index: i }">
            <div class="outline-card">
              <div class="card-header">
                <span class="drag-handle" title="拖拽排序">⠿</span>
                <span class="card-num">{{ String(i + 1).padStart(2, '0') }}</span>
                <input
                  v-model="item.title"
                  type="text"
                  class="editor-input card-title-input"
                  placeholder="页面标题"
                />
                <button class="remove-btn" @click="removeOutlineItem(i)">×</button>
              </div>
              <div class="card-details">
                <div v-for="(detail, j) in item.details" :key="j" class="detail-row">
                  <span class="detail-bullet">•</span>
                  <input
                    v-model="item.details[j]"
                    type="text"
                    class="detail-input"
                    placeholder="要点描述"
                  />
                  <button class="detail-remove" @click="removeDetail(i, j)">×</button>
                </div>
                <button class="detail-add" @click="addDetail(i)">+ 添加要点</button>
              </div>
            </div>
          </template>
        </draggable>
        <div class="outline-actions">
          <button class="btn btn-outline btn-sm" @click="addOutlineItem">+ 添加页面</button>
          <div class="outline-action-right">
            <button class="btn btn-outline btn-sm" @click="editingOutline = false">取消</button>
            <button class="btn btn-primary btn-sm" @click="saveOutline">保存</button>
          </div>
        </div>
      </div>

      <!-- 展示模式 -->
      <div v-else class="outline-display">
        <div
          v-for="(item, i) in outlineDisplay"
          :key="i"
          class="outline-card-view"
          :style="{ animationDelay: `${i * 0.05}s` }"
        >
          <div class="view-header">
            <span class="view-num">{{ String(i + 1).padStart(2, '0') }}</span>
            <span class="view-title">{{ item.title }}</span>
          </div>
          <ul v-if="item.details.length" class="view-details">
            <li v-for="(d, j) in item.details" :key="j">{{ d }}</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- 摘要 -->
    <section class="section">
      <h3 class="section-title">
        <span class="section-icon">¶</span>
        方案摘要
      </h3>
      <div class="summary-block">{{ store.planSummary }}</div>
    </section>

    <!-- 数据来源 -->
    <Transition name="fade">
      <div v-if="store.dataSources.length > 0" class="sources-section">
        <div class="section-head">
          <h3 class="section-title">
            <span class="section-icon">⟳</span>
            数据来源
          </h3>
          <span class="source-count">共 {{ store.dataSources.length }} 条</span>
        </div>
        <div class="sources-grid">
          <div
            v-for="(src, i) in store.dataSources"
            :key="i"
            class="source-card"
            :class="{ trusted: src.is_trusted }"
          >
            <div class="source-header">
              <span class="source-badge">{{ src.is_trusted ? '受信' : '参考' }}</span>
              <span class="source-title">{{ src.title }}</span>
            </div>
            <p class="source-summary">{{ src.summary }}</p>
            <a :href="src.url" target="_blank" class="source-link">
              {{ new URL(src.url).hostname }} ↗
            </a>
          </div>
        </div>
      </div>
    </Transition>

    <div class="divider" />

    <!-- 参数选择 -->
    <div class="params-grid">
      <!-- 页数 -->
      <div class="param-group">
        <div class="param-label">页数</div>
        <div class="pages-control">
          <button class="pages-btn" @click="store.selectedPages = Math.max(3, store.selectedPages - 1)">−</button>
          <span class="pages-value">{{ store.selectedPages }}</span>
          <button class="pages-btn" @click="store.selectedPages = Math.min(30, store.selectedPages + 1)">+</button>
        </div>
      </div>

      <!-- 风格 -->
      <div class="param-group" style="grid-column: span 2;">
        <div class="param-label">风格</div>
        <div class="styles-grid">
          <button
            v-for="s in styles"
            :key="s.value"
            class="style-card"
            :class="{ selected: store.selectedStyle === s.value }"
            @click="store.selectedStyle = s.value"
          >
            <span class="style-icon">{{ s.icon }}</span>
            <span class="style-name">{{ s.label }}</span>
            <span class="style-desc">{{ s.desc }}</span>
          </button>
          <!-- 自定义风格 -->
          <button
            class="style-card custom-style-card"
            :class="{ selected: showCustomStyle }"
            @click="showCustomStyle = !showCustomStyle"
          >
            <span class="style-icon">✎</span>
            <span class="style-name">自定义</span>
            <span class="style-desc">描述你想要的风格</span>
          </button>
        </div>
        <Transition name="fade">
          <div v-if="showCustomStyle" class="custom-style-input">
            <input
              v-model="store.customStyleDesc"
              type="text"
              placeholder="例如：赛博朋克风格，霓虹灯光效果，深色背景…"
            />
          </div>
        </Transition>
      </div>

      <!-- 配色 -->
      <div class="param-group" style="grid-column: span 3;">
        <div class="param-label">配色 <span class="label-hint">可多选</span></div>
        <div class="colors-row">
          <button
            v-for="c in colors"
            :key="c.value"
            class="color-chip"
            :class="[c.cssClass, { selected: store.selectedColors.includes(c.value) }]"
            @click="toggleColor(c.value)"
          >
            <span class="chip-dot" />
            <span class="chip-name">{{ c.label }}</span>
          </button>
        </div>
        <!-- 自定义配色 -->
        <div class="custom-colors">
          <div class="custom-color-input-row">
            <input
              v-model="customColorInput"
              type="text"
              class="custom-color-input"
              placeholder="输入 HEX 色值，如 #FF6B35"
              @keyup.enter="addCustomColor"
            />
            <button class="btn btn-outline btn-sm" @click="addCustomColor">添加</button>
          </div>
          <div v-if="store.customColors.length > 0" class="custom-color-tags">
            <span v-for="(hex, i) in store.customColors" :key="i" class="color-tag">
              <span class="tag-dot" :style="{ background: hex }" />
              {{ hex }}
              <button class="tag-remove" @click="removeCustomColor(i)">×</button>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 高级自定义 -->
    <div class="divider" />
    <div class="advanced-toggle" @click="showAdvanced = !showAdvanced">
      <span class="adv-label">高级自定义</span>
      <span class="adv-arrow">{{ showAdvanced ? '▾' : '▸' }}</span>
    </div>
    <Transition name="fade">
      <div v-if="showAdvanced" class="advanced-panel">
        <div class="adv-grid">
          <!-- 字体方案 -->
          <div class="adv-group">
            <div class="adv-label">字体方案</div>
            <select v-model="store.fontScheme" class="adv-select">
              <option value="">自动（跟随风格）</option>
              <option value="A">A - 现代无衬线</option>
              <option value="B">B - 人文衬线</option>
              <option value="C">C - 圆润可爱</option>
              <option value="D">D - 科技未来</option>
              <option value="E">E - 手写文艺</option>
              <option value="F">F - 高端商务</option>
              <option value="G">G - 极简留白</option>
            </select>
          </div>
          <!-- 布局密度 -->
          <div class="adv-group">
            <div class="adv-label">布局密度</div>
            <div class="adv-btns">
              <button :class="{ selected: store.layoutDensity === 'sparse' }" @click="store.layoutDensity = store.layoutDensity === 'sparse' ? '' : 'sparse'">稀疏</button>
              <button :class="{ selected: store.layoutDensity === 'normal' }" @click="store.layoutDensity = store.layoutDensity === 'normal' ? '' : 'normal'">适中</button>
              <button :class="{ selected: store.layoutDensity === 'dense' }" @click="store.layoutDensity = store.layoutDensity === 'dense' ? '' : 'dense'">紧凑</button>
            </div>
          </div>
          <!-- 背景样式 -->
          <div class="adv-group">
            <div class="adv-label">背景</div>
            <select v-model="store.bgStyle" class="adv-select">
              <option value="">自动</option>
              <option value="solid">纯色</option>
              <option value="gradient">渐变</option>
              <option value="mesh">网格渐变</option>
              <option value="pattern">几何图案</option>
              <option value="noise">噪点纹理</option>
            </select>
          </div>
          <!-- 页码 -->
          <div class="adv-group">
            <div class="adv-label">页码</div>
            <select v-model="store.pageNumberStyle" class="adv-select">
              <option value="">自动</option>
              <option value="bottom-right">右下角</option>
              <option value="bottom-center">底部居中</option>
              <option value="bottom-left">左下角</option>
              <option value="hidden">不显示</option>
            </select>
          </div>
          <!-- 圆角 -->
          <div class="adv-group">
            <div class="adv-label">圆角</div>
            <div class="adv-btns">
              <button :class="{ selected: store.borderRadius === '0' }" @click="store.borderRadius = store.borderRadius === '0' ? '' : '0'">无</button>
              <button :class="{ selected: store.borderRadius === 'small' }" @click="store.borderRadius = store.borderRadius === 'small' ? '' : 'small'">小</button>
              <button :class="{ selected: store.borderRadius === 'medium' }" @click="store.borderRadius = store.borderRadius === 'medium' ? '' : 'medium'">中</button>
              <button :class="{ selected: store.borderRadius === 'large' }" @click="store.borderRadius = store.borderRadius === 'large' ? '' : 'large'">大</button>
            </div>
          </div>
          <!-- 阴影 -->
          <div class="adv-group">
            <div class="adv-label">阴影</div>
            <div class="adv-btns">
              <button :class="{ selected: store.shadowLevel === 'none' }" @click="store.shadowLevel = store.shadowLevel === 'none' ? '' : 'none'">无</button>
              <button :class="{ selected: store.shadowLevel === 'light' }" @click="store.shadowLevel = store.shadowLevel === 'light' ? '' : 'light'">轻</button>
              <button :class="{ selected: store.shadowLevel === 'medium' }" @click="store.shadowLevel = store.shadowLevel === 'medium' ? '' : 'medium'">中</button>
              <button :class="{ selected: store.shadowLevel === 'heavy' }" @click="store.shadowLevel = store.shadowLevel === 'heavy' ? '' : 'heavy'">重</button>
            </div>
          </div>
          <!-- 内容对齐 -->
          <div class="adv-group">
            <div class="adv-label">内容对齐</div>
            <div class="adv-btns">
              <button :class="{ selected: store.contentAlign === 'left' }" @click="store.contentAlign = store.contentAlign === 'left' ? '' : 'left'">左对齐</button>
              <button :class="{ selected: store.contentAlign === 'center' }" @click="store.contentAlign = store.contentAlign === 'center' ? '' : 'center'">居中</button>
              <button :class="{ selected: store.contentAlign === 'right' }" @click="store.contentAlign = store.contentAlign === 'right' ? '' : 'right'">右对齐</button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 操作 -->
    <div class="actions">
      <button class="btn btn-outline" :disabled="store.streaming" @click="store.goToStep('input')">
        ← 返回
      </button>
      <button
        class="btn btn-primary"
        :disabled="store.loading || store.streaming"
        @click="store.confirmAndGenerate()"
      >
        <span v-if="store.streaming">生成中…</span>
        <span v-else-if="store.loading">处理中…</span>
        <span v-else>
          <span class="btn-icon-text">→</span>
          确认方案，生成演示文稿
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.plan-card { animation-delay: 0.05s; }

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

/* 流式进度 */
.stream-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--amber-glow);
  border: 1px solid rgba(232,168,73,0.15);
  border-radius: var(--radius);
  margin-bottom: 28px;
  position: relative;
  overflow: hidden;
}
.stream-pulse {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--amber);
  animation: pulse 1.5s ease infinite;
  flex-shrink: 0;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}
.stream-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}
.stream-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--amber);
}
.stream-meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
}
.stream-progress {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2px;
  background: rgba(232,168,73,0.1);
}
.stream-progress-bar {
  height: 100%;
  background: var(--amber);
  animation: progress 3s ease infinite;
}
@keyframes progress {
  0% { width: 0%; }
  50% { width: 80%; }
  100% { width: 100%; }
}

/* 方案元信息 */
.plan-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 28px;
}
.meta-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: 20px;
}
.badge-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
}
.badge-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--amber);
}
.mono { font-family: 'JetBrains Mono', monospace; }

/* 章节 */
.section { margin-bottom: 28px; }
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.section-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.section-icon {
  color: var(--amber);
  font-size: 16px;
  font-weight: 800;
}

.edit-btn {
  background: none;
  border: none;
  color: var(--amber-dim);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 6px;
  transition: all 0.2s;
  font-family: 'Outfit', sans-serif;
}
.edit-btn:hover {
  background: var(--amber-glow);
  color: var(--amber);
}
.edit-icon { font-size: 14px; }

.plan-title-display {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  padding: 14px 18px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  line-height: 1.4;
}
.plan-title-display:hover {
  border-color: rgba(232,168,73,0.15);
  background: var(--ink);
}

/* 内联编辑器 */
.inline-editor {
  display: flex;
  gap: 8px;
  align-items: center;
}
.editor-input {
  flex: 1;
}
.btn-sm { padding: 8px 16px; font-size: 13px; }

/* 大纲编辑 - 卡片式 */
.outline-editor { display: flex; flex-direction: column; gap: 10px; }
.outline-card {
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  transition: all 0.2s;
}
.outline-card:hover {
  border-color: rgba(232,168,73,0.12);
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.drag-handle {
  cursor: grab;
  color: var(--text-muted);
  font-size: 16px;
  flex-shrink: 0;
  user-select: none;
}
.drag-handle:active { cursor: grabbing; }
.card-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: var(--amber);
  flex-shrink: 0;
}
.card-title-input {
  flex: 1;
  font-weight: 600;
  font-size: 14px;
  background: transparent !important;
  border: none !important;
  padding: 4px 0 !important;
  box-shadow: none !important;
}
.remove-btn {
  width: 24px; height: 24px;
  background: none;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 6px;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 14px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}
.remove-btn:hover {
  border-color: var(--vermillion);
  color: var(--vermillion);
  background: var(--vermillion-glow);
}

/* 细节编辑 */
.card-details {
  margin-top: 8px;
  padding-left: 32px;
}
.detail-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.detail-bullet {
  color: var(--text-muted);
  font-size: 12px;
  flex-shrink: 0;
}
.detail-input {
  flex: 1;
  font-size: 13px;
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid rgba(255,255,255,0.04) !important;
  border-radius: 0 !important;
  padding: 3px 0 !important;
  box-shadow: none !important;
}
.detail-input:focus {
  border-bottom-color: var(--amber-dim) !important;
}
.detail-remove {
  background: none; border: none;
  color: var(--text-muted); cursor: pointer;
  font-size: 13px; padding: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}
.detail-row:hover .detail-remove { opacity: 1; }
.detail-remove:hover { color: var(--vermillion); }
.detail-add {
  background: none; border: none;
  color: var(--amber-dim); cursor: pointer;
  font-size: 12px; padding: 4px 0;
  font-family: 'Outfit', sans-serif;
  transition: color 0.2s;
}
.detail-add:hover { color: var(--amber); }

.outline-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.outline-action-right { display: flex; gap: 8px; }

/* 大纲展示 - 层级卡片 */
.outline-display { display: flex; flex-direction: column; gap: 8px; }
.outline-card-view {
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.03);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
  transition: all 0.25s;
  animation: itemIn 0.4s var(--ease-out) both;
}
.outline-card-view:hover {
  background: var(--ink);
  border-color: rgba(232,168,73,0.08);
}
.view-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.view-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: var(--amber);
  flex-shrink: 0;
}
.view-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.view-details {
  list-style: none;
  padding-left: 28px;
}
.view-details li {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  position: relative;
  padding-left: 12px;
}
.view-details li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--text-muted);
}

@keyframes itemIn {
  from { opacity: 0; transform: translateX(-8px); }
  to { opacity: 1; transform: translateX(0); }
}

.summary-block {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.8;
  padding: 16px;
  background: var(--ink-light);
  border-left: 3px solid var(--amber-dim);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

/* 参数选择 */
.params-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 8px;
}
.param-group { }
.param-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

/* 页数控制 */
.pages-control {
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.pages-btn {
  width: 44px; height: 44px;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Outfit', sans-serif;
}
.pages-btn:hover {
  background: var(--amber-glow);
  color: var(--amber);
}
.pages-value {
  width: 48px;
  text-align: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  border-left: 1px solid rgba(255,255,255,0.04);
  border-right: 1px solid rgba(255,255,255,0.04);
  line-height: 44px;
}

/* 风格卡片 */
.styles-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.style-card {
  padding: 16px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.style-card:hover {
  border-color: rgba(232,168,73,0.15);
  background: var(--ink);
  transform: translateY(-2px);
}
.style-card.selected {
  border-color: var(--amber);
  background: var(--ink);
  box-shadow: 0 0 0 1px var(--amber), var(--shadow-glow);
}
.style-icon {
  font-size: 22px;
  color: var(--amber);
}
.style-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}
.style-desc {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.3;
}

/* 配色 */
.colors-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.color-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 24px;
  cursor: pointer;
  transition: all 0.25s var(--ease-out);
  font-family: 'Outfit', sans-serif;
}
.color-chip:hover {
  border-color: rgba(255,255,255,0.12);
  background: var(--ink);
}
.color-chip.selected {
  border-color: var(--amber);
  box-shadow: 0 0 0 1px var(--amber);
}
.chip-dot {
  width: 14px; height: 14px;
  border-radius: 50%;
}
.chip-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
.color-chip.selected .chip-name { color: var(--text-primary); }
.color-blue .chip-dot { background: linear-gradient(135deg, #4F46E5, #7C3AED); }
.color-green .chip-dot { background: linear-gradient(135deg, #059669, #34D399); }
.color-red .chip-dot { background: linear-gradient(135deg, #DC2626, #F87171); }
.color-purple .chip-dot { background: linear-gradient(135deg, #7C3AED, #C084FC); }
.color-dark .chip-dot { background: linear-gradient(135deg, #374151, #6B7280); }

.label-hint {
  font-size: 11px;
  font-weight: 400;
  color: var(--text-muted);
  text-transform: none;
  letter-spacing: 0;
}

/* 自定义风格 */
.custom-style-card { border-style: dashed; }
.custom-style-input { margin-top: 10px; }
.custom-style-input input {
  width: 100%;
}

/* 自定义配色 */
.custom-colors { margin-top: 12px; }
.custom-color-input-row {
  display: flex;
  gap: 8px;
}
.custom-color-input {
  flex: 1;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
}
.custom-color-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}
.color-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--text-secondary);
}
.tag-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.tag-remove {
  background: none; border: none;
  color: var(--text-muted); cursor: pointer;
  font-size: 14px; padding: 0 2px;
}
.tag-remove:hover { color: var(--vermillion); }

[data-theme="light"] .color-tag {
  background: #F0ECE5;
  border-color: #E5E1DA;
}

/* ═══ 高级自定义 ═══ */
.advanced-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background 0.2s;
  margin-bottom: 8px;
}
.advanced-toggle:hover { background: rgba(255,255,255,0.03); }
.adv-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
.adv-arrow {
  font-size: 12px;
  color: var(--text-muted);
}
.advanced-panel {
  padding: 0 0 16px;
}
.adv-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}
.adv-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.adv-group .adv-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
}
.adv-select {
  width: 100%;
  padding: 8px 12px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 13px;
  font-family: 'Outfit', sans-serif;
  cursor: pointer;
  outline: none;
  transition: border-color 0.2s;
  appearance: auto;
}
.adv-select:focus { border-color: var(--amber-dim); }
.adv-btns {
  display: flex;
  gap: 4px;
}
.adv-btns button {
  flex: 1;
  padding: 6px 8px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 6px;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'Outfit', sans-serif;
}
.adv-btns button:hover {
  border-color: rgba(232,168,73,0.15);
  color: var(--text-secondary);
}
.adv-btns button.selected {
  background: var(--amber-glow);
  border-color: var(--amber-dim);
  color: var(--amber);
}

[data-theme="light"] .adv-select {
  background: #F8F7F5;
  border-color: #E5E1DA;
  color: #1A1612;
}
[data-theme="light"] .adv-btns button {
  background: #F8F7F5;
  border-color: #E5E1DA;
  color: #5C564E;
}

/* 按钮文本箭头 */
.btn-icon-text {
  font-size: 16px;
  transition: transform 0.25s var(--ease-spring);
}
.btn:hover .btn-icon-text { transform: translateX(3px); }

/* 列表过渡 */
.list-enter-active { transition: all 0.3s var(--ease-out); }
.list-leave-active { transition: all 0.2s var(--ease-out); }
.list-enter-from { opacity: 0; transform: translateX(-10px); }
.list-leave-to { opacity: 0; transform: translateX(10px); }

/* ═══ 数据来源 ═══ */
.sources-section { margin-bottom: 24px; }
.source-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--text-muted);
}
.sources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}
.source-card {
  padding: 16px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: var(--radius-sm);
  transition: all 0.25s;
}
.source-card:hover {
  border-color: rgba(232,168,73,0.1);
  background: var(--ink);
}
.source-card.trusted {
  border-left: 3px solid var(--jade);
}
.source-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.source-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--amber-glow);
  color: var(--amber);
  flex-shrink: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.source-card.trusted .source-badge {
  background: var(--jade-glow);
  color: var(--jade);
}
.source-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.source-summary {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.source-link {
  font-size: 11px;
  color: var(--text-muted);
  text-decoration: none;
  font-family: 'JetBrains Mono', monospace;
  transition: color 0.2s;
}
.source-link:hover { color: var(--amber); }

[data-theme="light"] .source-card {
  background: #F4F1EC;
  border-color: #E5E1DA;
}
[data-theme="light"] .source-card:hover {
  background: #FFFFFF;
}
</style>
