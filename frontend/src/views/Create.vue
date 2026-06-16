<script setup lang="ts">
import { usePptStore } from '../stores/ppt'
import StepInput from '../components/StepInput.vue'
import StepPlan from '../components/StepPlan.vue'
import StepPreview from '../components/StepPreview.vue'
import StepDownload from '../components/StepDownload.vue'
import ChatHistory from '../components/ChatHistory.vue'
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'

const store = usePptStore()
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
      </div>
    </nav>

    <!-- 主体布局 -->
    <div class="app-body">
      <ChatHistory />

      <main class="main-stage">
        <div class="content-area">
          <div class="card-area">
            <Transition name="slide" mode="out-in">
              <StepInput v-if="isActive('input')" key="input" />
              <StepPlan v-else-if="isActive('plan')" key="plan" />
              <StepPreview v-else-if="isActive('preview')" key="preview" />
              <StepDownload v-else-if="isActive('download')" key="download" />
            </Transition>
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
[data-theme="light"] .theme-toggle { background: rgba(0,0,0,0.04); border-color: rgba(0,0,0,0.08); }
[data-theme="light"] .topbar { background: rgba(244,241,236,0.9); border-bottom-color: rgba(0,0,0,0.06); }
[data-theme="light"] .brand-name { color: #1A1612; }
[data-theme="light"] .brand-sub { color: #9A9488; }

.app-body { flex: 1; display: flex; justify-content: center; min-height: calc(100vh - 56px); padding: 36px 32px 80px; }
.main-stage { width: 100%; display: flex; justify-content: center; }
.content-area { display: flex; gap: 28px; align-items: flex-start; width: 100%; max-width: 1200px; }
.card-area { flex: 1; min-width: 0; max-width: 1100px; }

.steps-rail { width: 64px; flex-shrink: 0; position: sticky; top: 92px; padding-top: 40px; }
.rail-label { font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: var(--text-muted); text-align: center; margin-bottom: 20px; }
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
[data-theme="light"] .rail-arrow { color: rgba(0,0,0,0.1); }
[data-theme="light"] .rail-dot { background: #F0ECE5; border-color: rgba(0,0,0,0.08); }

.slide-enter-active { animation: slideIn 0.4s var(--ease-out) both; }
.slide-leave-active { animation: slideOut 0.25s var(--ease-out) both; }
@keyframes slideIn { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideOut { from { opacity: 1; transform: translateY(0); } to { opacity: 0; transform: translateY(-8px); } }
.fade-enter-active { transition: opacity 0.3s; }
.fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.global-error { position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%); background: var(--vermillion); color: white; padding: 14px 24px; border-radius: var(--radius); font-size: 14px; font-weight: 500; display: flex; align-items: center; gap: 10px; box-shadow: 0 8px 30px rgba(212,93,76,0.4); cursor: pointer; z-index: 200; animation: errorIn 0.4s var(--ease-spring) both; }
.error-icon { width: 20px; height: 20px; background: rgba(255,255,255,0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; }
@keyframes errorIn { from { opacity: 0; transform: translateX(-50%) translateY(20px) scale(0.9); } to { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); } }
</style>
