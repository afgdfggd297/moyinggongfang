<script setup lang="ts">
import { usePptStore } from '../stores/ppt'
import { getDownloadUrl } from '../api/ppt'

const store = usePptStore()

function downloadPpt() {
  const url = getDownloadUrl(store.planId)
  window.open(url, '_blank')
}
</script>

<template>
  <div class="card download-card">
    <div class="corner-deco">04</div>

    <!-- 成功动画 -->
    <div class="success-stage">
      <div class="success-rings">
        <div class="ring ring-1" />
        <div class="ring ring-2" />
        <div class="ring ring-3" />
        <div class="success-icon">✓</div>
      </div>

      <h2 class="success-title">演示文稿已就绪</h2>
      <p class="success-sub">所有幻灯片已渲染完成，可随时下载</p>
    </div>

    <!-- 文件信息 -->
    <div class="file-info">
      <div class="file-icon">◈</div>
      <div class="file-meta">
        <span class="file-name">{{ store.title }}</span>
        <span class="file-type">PowerPoint (.pptx)</span>
      </div>
    </div>

    <!-- 操作 -->
    <div class="download-actions">
      <button class="btn btn-primary btn-lg" @click="downloadPpt">
        <span class="dl-icon">↓</span>
        下载 PPT 文件
      </button>
      <button class="btn btn-outline" @click="store.reset()">
        <span>↻</span>
        创建新的演示文稿
      </button>
    </div>

    <!-- 装饰 -->
    <div class="bg-pattern" />
  </div>
</template>

<style scoped>
.download-card {
  text-align: center;
  padding: 60px 40px;
  overflow: hidden;
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

/* 成功动画 */
.success-stage {
  margin-bottom: 40px;
}
.success-rings {
  position: relative;
  width: 100px; height: 100px;
  margin: 0 auto 28px;
}
.ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid transparent;
}
.ring-1 {
  border-top-color: var(--amber);
  animation: spin 2s linear infinite;
}
.ring-2 {
  inset: 10px;
  border-right-color: var(--jade);
  animation: spin 3s linear infinite reverse;
}
.ring-3 {
  inset: 20px;
  border-bottom-color: var(--indigo);
  animation: spin 4s linear infinite;
}
.success-icon {
  position: absolute;
  inset: 30px;
  background: var(--amber);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-deep);
  font-size: 24px;
  font-weight: 800;
  animation: popIn 0.5s var(--ease-spring) 0.3s both;
}
@keyframes popIn {
  from { transform: scale(0); }
  to { transform: scale(1); }
}

.success-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.success-sub {
  font-size: 15px;
  color: var(--text-secondary);
}

/* 文件信息 */
.file-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 20px;
  background: var(--ink-light);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: var(--radius);
  margin-bottom: 36px;
}
.file-icon {
  width: 48px; height: 48px;
  background: var(--amber-glow);
  border: 1px solid rgba(232,168,73,0.15);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: var(--amber);
  flex-shrink: 0;
}
.file-meta {
  display: flex;
  flex-direction: column;
  text-align: left;
}
.file-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
}
.file-type {
  font-size: 13px;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}

/* 操作 */
.download-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.btn-lg {
  padding: 16px 48px;
  font-size: 16px;
}
.dl-icon {
  font-size: 20px;
  font-weight: 800;
}

/* 背景装饰 */
.bg-pattern {
  position: absolute;
  bottom: -60px; right: -60px;
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(232,168,73,0.04) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}
</style>
