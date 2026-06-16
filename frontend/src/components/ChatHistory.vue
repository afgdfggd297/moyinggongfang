<script setup lang="ts">
import { ref } from 'vue'
import { usePptStore } from '../stores/ppt'

const store = usePptStore()
const collapsed = ref(false)

function toggle() {
  collapsed.value = !collapsed.value
}

function goHome() {
  store.reset()
}
</script>

<template>
  <aside class="history-sidebar" :class="{ collapsed }">
    <!-- 折叠按钮 -->
    <button class="collapse-btn" @click="toggle" :title="collapsed ? '展开' : '收起'">
      <span class="collapse-icon">{{ collapsed ? '»' : '«' }}</span>
    </button>

    <!-- 展开状态 -->
    <Transition name="sidebar-fade">
      <div v-if="!collapsed" class="sidebar-content">
        <!-- 新建 -->
        <button class="new-btn" @click="goHome">
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
            @click="store.loadPlan(item.planId)"
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
</template>

<style scoped>
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
</style>
