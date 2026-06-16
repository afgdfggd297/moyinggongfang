<script setup lang="ts">
import { ref } from 'vue'
import { usePptStore } from '../stores/ppt'

const store = usePptStore()
const userText = ref('')
const extraInfo = ref('')
const focused = ref(false)

async function handleSubmit() {
  if (!userText.value.trim()) {
    alert('请输入PPT内容')
    return
  }
  await store.submitPlan(userText.value, extraInfo.value || undefined)
}
</script>

<template>
  <div class="card input-card">
    <!-- 装饰角标 -->
    <div class="corner-deco">01</div>

    <div class="card-title">
      <span class="icon">✦</span>
      <span>构思内容</span>
    </div>

    <p class="card-desc">
      将您的想法、大纲或素材交给 AI，它会为您规划出专业的演示文稿方案。
    </p>

    <!-- 主输入区 -->
    <div class="input-stage" :class="{ focused }">
      <div class="input-label">
        <span class="label-dot" />
        演示文稿内容
      </div>
      <textarea
        v-model="userText"
        placeholder="在此输入您的 PPT 内容…&#10;&#10;例如：关于人工智能发展趋势的分析报告，包含历史回顾、当前应用、未来展望三个部分…"
        @focus="focused = true"
        @blur="focused = false"
      />
      <div class="input-meta">
        <span class="char-count" :class="{ warn: userText.length > 2000 }">
          {{ userText.length }} 字
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
        :class="{ on: store.enableSearch }"
        @click="store.enableSearch = !store.enableSearch"
      >
        <span class="toggle-knob" />
      </button>
    </div>

    <!-- 操作 -->
    <div class="actions">
      <button
        class="btn btn-primary"
        :disabled="store.loading || !userText.trim()"
        @click="handleSubmit"
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

    <!-- 加载态 -->
    <Transition name="fade">
      <div v-if="store.loading" class="loading-overlay">
        <div class="loading-content">
          <div class="loading-rings">
            <div class="ring r1" />
            <div class="ring r2" />
            <div class="ring r3" />
          </div>
          <div class="loading-text">AI 正在分析您的内容并规划方案</div>
          <div class="loading-hint">通常需要 5-15 秒</div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.input-card {
  animation-delay: 0.05s;
}

/* 角标装饰 */
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
  margin-bottom: 32px;
}

/* 输入区 */
.input-stage, .extra-stage {
  margin-bottom: 24px;
  position: relative;
}
.input-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}
.label-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--amber);
}
.label-dot.dim { background: var(--text-muted); }
.optional {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: none;
  letter-spacing: 0;
  font-weight: 400;
}

.input-stage textarea {
  min-height: 200px;
  transition: all 0.3s var(--ease-out);
}
.input-stage.focused textarea {
  border-color: var(--amber-dim);
  box-shadow: 0 0 0 3px var(--amber-glow);
}
.input-meta {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
.char-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
}
.char-count.warn { color: var(--vermillion); }

.actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
.btn-icon-text {
  font-size: 16px;
  transition: transform 0.25s var(--ease-spring);
}
.btn:hover .btn-icon-text {
  transform: translateX(3px);
}

.btn-loading {
  display: flex;
  align-items: center;
  gap: 10px;
}
.btn-spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(12,14,20,0.2);
  border-top-color: var(--ink-deep);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

/* 加载遮罩 */
.loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(26, 30, 42, 0.85);
  backdrop-filter: blur(8px);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}
.loading-content {
  text-align: center;
}
.loading-rings {
  position: relative;
  width: 80px; height: 80px;
  margin: 0 auto 24px;
}
.ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid transparent;
}
.r1 {
  border-top-color: var(--amber);
  animation: spin 1.2s linear infinite;
}
.r2 {
  inset: 8px;
  border-right-color: var(--jade);
  animation: spin 1.8s linear infinite reverse;
}
.r3 {
  inset: 16px;
  border-bottom-color: var(--indigo);
  animation: spin 2.4s linear infinite;
}
.loading-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.loading-hint {
  font-size: 13px;
  color: var(--text-muted);
}

/* ═══ 搜索开关 ═══ */
.search-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: var(--radius-sm);
  margin-bottom: 24px;
}
.toggle-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.toggle-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.toggle-desc {
  font-size: 12px;
  color: var(--text-muted);
}
.toggle-switch {
  width: 48px; height: 26px;
  border-radius: 13px;
  background: var(--ink-lighter);
  border: 1px solid rgba(255,255,255,0.08);
  cursor: pointer;
  position: relative;
  transition: all 0.3s var(--ease-out);
  flex-shrink: 0;
}
.toggle-switch.on {
  background: var(--amber);
  border-color: var(--amber);
}
.toggle-knob {
  position: absolute;
  top: 2px; left: 2px;
  width: 20px; height: 20px;
  border-radius: 50%;
  background: white;
  transition: transform 0.3s var(--ease-spring);
  box-shadow: 0 1px 4px rgba(0,0,0,0.2);
}
.toggle-switch.on .toggle-knob {
  transform: translateX(22px);
}

[data-theme="light"] .search-toggle-row {
  background: #F8F7F5;
  border-color: #E5E1DA;
}
</style>
