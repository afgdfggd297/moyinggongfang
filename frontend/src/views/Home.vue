<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import { onMounted, onUnmounted, ref, watch } from 'vue'

const router = useRouter()
const { theme, toggle: toggleTheme } = useTheme()

// 根据主题切换遮罩颜色
const MASK_LIGHT = '252, 250, 248' // 宣纸色
const MASK_DARK = '12, 14, 20'     // 墨色 #0C0E14（与页面背景一致）
const maskColor = ref(MASK_LIGHT)

function startCreate() {
  router.push('/create')
}

// ——— MiMo 风格水墨揭示 ———
const heroRef = ref<HTMLElement>()
const canvasRef = ref<HTMLCanvasElement>()

const MASK = '252, 250, 248' // 宣纸底色
const R_START = 8
const R_END = 128
const R_VARY = 0.45
const LIFETIME = 520
const STAMP_STEP = 12
const MAX_STAMPS = 160

let ctx: CanvasRenderingContext2D | null = null
let w = 0, h = 0, dpr = 1
let stamps: { x: number; y: number; born: number; seed: number; rmax: number }[] = []
let lastX: number | null = null
let lastY: number | null = null
let running = false
let rafId = 0

function resize() {
  if (!heroRef.value || !canvasRef.value || !ctx) return
  const rect = heroRef.value.getBoundingClientRect()
  w = rect.width
  h = rect.height
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  canvasRef.value.width = Math.round(w * dpr)
  canvasRef.value.height = Math.round(h * dpr)
  canvasRef.value.style.width = w + 'px'
  canvasRef.value.style.height = h + 'px'
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  // 先铺满遮罩
  ctx.globalCompositeOperation = 'source-over'
  ctx.fillStyle = 'rgb(' + maskColor.value + ')'
  ctx.fillRect(0, 0, w, h)
}

function addStamp(x: number, y: number) {
  if (stamps.length >= MAX_STAMPS) stamps.shift()
  stamps.push({
    x, y,
    born: performance.now(),
    seed: Math.random() * Math.PI * 2,
    rmax: R_END * (1 - R_VARY + Math.random() * R_VARY),
  })
}

function stampAlong(x: number, y: number) {
  if (lastX === null) {
    addStamp(x, y)
  } else {
    const dx = x - lastX, dy = y - lastY
    const dist = Math.hypot(dx, dy)
    const steps = Math.max(1, Math.ceil(dist / STAMP_STEP))
    for (let i = 1; i <= steps; i++) {
      addStamp(lastX + (dx * i) / steps, lastY + (dy * i) / steps)
    }
  }
  lastX = x
  lastY = y
}

function carveInk(x: number, y: number, r: number, alpha: number, seed: number) {
  if (!ctx) return
  const g = ctx.createRadialGradient(x, y, r * 0.25, x, y, r)
  g.addColorStop(0, 'rgba(0,0,0,' + 0.95 * alpha + ')')
  g.addColorStop(0.55, 'rgba(0,0,0,' + 0.88 * alpha + ')')
  g.addColorStop(1, 'rgba(0,0,0,0)')
  ctx.fillStyle = g
  ctx.beginPath()
  const segs = 32
  for (let i = 0; i <= segs; i++) {
    const a = (i / segs) * Math.PI * 2
    // 不规则毛边 — 模拟水墨晕染
    const wob =
      0.78 +
      0.14 * Math.sin(a * 3 + seed) +
      0.08 * Math.sin(a * 7 + seed * 2.1) +
      0.05 * Math.sin(a * 13 + seed * 0.7)
    const rr = r * wob
    const px = x + Math.cos(a) * rr
    const py = y + Math.sin(a) * rr
    if (i === 0) ctx.moveTo(px, py)
    else ctx.lineTo(px, py)
  }
  ctx.closePath()
  ctx.fill()
}

function loop() {
  if (!ctx) return
  const now = performance.now()
  // 每帧重绘遮罩
  ctx.globalCompositeOperation = 'source-over'
  ctx.fillStyle = 'rgb(' + maskColor.value + ')'
  ctx.fillRect(0, 0, w, h)
  // 用 destination-out 挖洞
  ctx.globalCompositeOperation = 'destination-out'
  for (let i = stamps.length - 1; i >= 0; i--) {
    const t = (now - stamps[i].born) / LIFETIME
    if (t >= 1) { stamps.splice(i, 1); continue }
    const ease = 1 - Math.pow(1 - t, 3) // easeOutCubic
    const r = R_START + (stamps[i].rmax - R_START) * ease
    const alpha = 1 - t * t
    carveInk(stamps[i].x, stamps[i].y, r, alpha, stamps[i].seed)
  }
  if (stamps.length) {
    rafId = requestAnimationFrame(loop)
  } else {
    running = false
  }
}

function start() {
  if (!running) { running = true; rafId = requestAnimationFrame(loop) }
}

// 主题切换时更新遮罩颜色并重绘
watch(theme, (val) => {
  maskColor.value = val === 'dark' ? MASK_DARK : MASK_LIGHT
  if (ctx && w && h) {
    ctx.globalCompositeOperation = 'source-over'
    ctx.fillStyle = 'rgb(' + maskColor.value + ')'
    ctx.fillRect(0, 0, w, h)
    // 清空已有的揭示
    stamps = []
  }
})

// 全局鼠标追踪 — 检测鼠标是否在 hero 区域内
function onGlobalMouseMove(e: MouseEvent) {
  if (!heroRef.value) return
  const rect = heroRef.value.getBoundingClientRect()
  const inHero =
    e.clientX >= rect.left && e.clientX <= rect.right &&
    e.clientY >= rect.top && e.clientY <= rect.bottom
  if (inHero) {
    stampAlong(e.clientX - rect.left, e.clientY - rect.top)
    start()
  }
}

onMounted(() => {
  maskColor.value = theme.value === 'dark' ? MASK_DARK : MASK_LIGHT
  if (!canvasRef.value || !heroRef.value) return
  ctx = canvasRef.value.getContext('2d')
  if (!ctx) return
  resize()
  window.addEventListener('resize', resize)
  // 全局鼠标监听（比 element 事件更可靠）
  document.addEventListener('mousemove', onGlobalMouseMove)
})
onUnmounted(() => {
  window.removeEventListener('resize', resize)
  document.removeEventListener('mousemove', onGlobalMouseMove)
  cancelAnimationFrame(rafId)
})
</script>

<template>
  <div class="home">
    <!-- 顶部导航 -->
    <nav class="home-nav">
      <div class="nav-inner">
        <div class="brand">
          <div class="brand-mark">◈</div>
          <div class="brand-text">
            <span class="brand-name">墨印工坊</span>
            <span class="brand-sub">INKPRESS STUDIO</span>
          </div>
        </div>
        <div class="nav-right">
          <button class="theme-toggle" @click="toggleTheme" :title="theme === 'dark' ? '切换到日间模式' : '切换到夜间模式'">
            <span class="theme-icon">{{ theme === 'dark' ? '☀' : '☾' }}</span>
          </button>
          <button class="btn btn-primary btn-sm" @click="startCreate">开始创作</button>
        </div>
      </div>
    </nav>

    <!-- 英雄区 — 水墨揭示 -->
    <section class="hero" ref="heroRef">
      <!-- 底层：水墨画 -->
      <div class="hero-painting" />
      <!-- 中层：遮罩层 — CSS 动画揭示 + 鼠标交互 -->
      <canvas ref="canvasRef" class="hero-mask" />
      <!-- 顶层：文字内容 -->
      <div class="hero-content">
        <div class="hero-badge">AI 驱动</div>
        <h1 class="hero-title">
          <span class="line1">把想法变成</span>
          <span class="line2">专业的演示文稿</span>
        </h1>
        <p class="hero-desc">
          输入文字，AI 自动规划方案、搜索资料、生成精美的 HTML 幻灯片，<br />
          支持可视化编辑和一键导出 PPTX。
        </p>
        <div class="hero-actions">
          <button class="btn btn-primary btn-lg" @click="startCreate">
            <span>✦</span> 立即创作
          </button>
          <a href="#features" class="btn btn-ghost btn-lg">了解更多 ↓</a>
        </div>
      </div>
    </section>

    <!-- 特性 -->
    <section id="features" class="features">
      <div class="features-inner">
        <h2 class="section-title">核心能力</h2>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">✦</div>
            <h3>智能规划</h3>
            <p>输入主题内容，AI 自动分析并生成结构化的演示方案</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">⟳</div>
            <h3>联网搜索</h3>
            <p>自动搜索相关资料，让生成的内容更有依据和深度</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">◎</div>
            <h3>可视化编辑</h3>
            <p>所见即所得的预览编辑，直接在幻灯片上修改文字</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">↓</div>
            <h3>一键导出</h3>
            <p>HTML 幻灯片直接转为 PPTX，保留视觉效果</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 工作流程 -->
    <section class="workflow">
      <div class="workflow-inner">
        <h2 class="section-title">四步完成</h2>
        <div class="steps">
          <div class="step">
            <div class="step-num">01</div>
            <h3>输入内容</h3>
            <p>描述你的演示主题和要点</p>
          </div>
          <div class="step-arrow">→</div>
          <div class="step">
            <div class="step-num">02</div>
            <h3>确认方案</h3>
            <p>选择风格、配色、调整大纲</p>
          </div>
          <div class="step-arrow">→</div>
          <div class="step">
            <div class="step-num">03</div>
            <h3>预览编辑</h3>
            <p>可视化调整每一页内容</p>
          </div>
          <div class="step-arrow">→</div>
          <div class="step">
            <div class="step-num">04</div>
            <h3>导出下载</h3>
            <p>生成 PPTX 文件</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="home-footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <span class="footer-logo">◈</span>
          <span>墨印工坊</span>
        </div>
        <p class="footer-copy">AI 驱动的演示文稿生成工具</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
  background: var(--ink-deep);
}

/* ═══ 导航 ═══ */
.home-nav {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 100;
  background: rgba(12, 14, 20, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 40px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand { display: flex; align-items: center; gap: 12px; }
.brand-mark {
  width: 34px; height: 34px;
  background: linear-gradient(135deg, var(--amber), var(--amber-dim));
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; color: var(--ink-deep); font-weight: 800;
}
.brand-text { display: flex; flex-direction: column; }
.brand-name {
  font-family: 'Noto Serif SC', serif;
  font-size: 16px; font-weight: 700;
  color: var(--text-primary); letter-spacing: 2px;
}
.brand-sub {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px; color: var(--text-muted); letter-spacing: 3px;
}
.btn-sm { padding: 8px 20px; font-size: 13px; font-family: 'Outfit', sans-serif; }
.nav-right { display: flex; align-items: center; gap: 12px; }
.theme-toggle {
  width: 34px; height: 34px; border-radius: 50%;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08);
  color: var(--text-secondary); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.3s var(--ease-out);
  font-family: 'Outfit', sans-serif;
}
.theme-toggle:hover { background: rgba(232,168,73,0.12); border-color: rgba(232,168,73,0.25); color: var(--amber); transform: rotate(30deg); }
.theme-icon { font-size: 16px; }

/* ═══ 英雄区 — 水墨揭示 ═══ */
.hero {
  position: relative;
  height: 620px;
  overflow: hidden;
  isolation: isolate;
  background: #fcfaf8;
}
/* 暗色模式英雄区背景 */
[data-theme="dark"] .hero {
  background: #0C0E14;
}
/* 底层：水墨画 */
.hero-painting {
  position: absolute; inset: 0;
  background-image: url('/watercolor-hero.png');
  background-size: cover;
  background-position: center 40%;
  background-repeat: no-repeat;
  z-index: 0;
}
/* 中层：canvas 遮罩 */
.hero-mask {
  position: absolute; inset: 0;
  z-index: 1;
  pointer-events: none;
  display: block;
}
/* 触屏设备：不显示遮罩，直接展示画作 */
@media (hover: none) {
  .hero-mask { display: none;
  }
  .hero-hint { display: none; }
}
/* CSS 自动揭示动画 — 页面加载时画作从中心浮现 */
.hero-reveal {
  position: absolute; inset: 0;
  z-index: 1;
  background: #fcfaf8;
  pointer-events: none;
  animation: revealPainting 2.5s ease-out 0.2s forwards;
}
[data-theme="dark"] .hero-reveal {
  background: #0C0E14;
}
@keyframes revealPainting {
  0% {
    clip-path: circle(100% at 50% 50%);
  }
  100% {
    clip-path: circle(0% at 50% 50%);
  }
}

/* 交互提示 */
.hero-hint {
  position: absolute;
  bottom: 24px; left: 50%;
  transform: translateX(-50%);
  z-index: 3;
  font-size: 13px;
  color: #979696;
  letter-spacing: 1px;
  animation: hintPulse 2.5s ease-in-out infinite;
  pointer-events: none;
}
.hint-icon {
  font-size: 16px;
  margin-right: 4px;
}
@keyframes hintPulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
/* 顶层：文字 */
.hero-content {
  position: relative; z-index: 2;
  max-width: 900px;
  margin: 0 auto;
  padding-top: 100px;
  text-align: center;
}
.hero-badge {
  display: inline-block;
  padding: 6px 16px;
  background: rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 20px;
  font-size: 13px; font-weight: 600;
  color: #26251e;
  margin-bottom: 28px;
}
.hero-title { margin-bottom: 24px; }
.hero-title .line1 {
  display: block;
  font-family: 'Noto Serif SC', serif;
  font-size: 52px; font-weight: 700;
  color: #26251e;
  letter-spacing: 2px; line-height: 1.3;
}
.hero-title .line2 {
  display: block;
  font-size: 52px; font-weight: 800;
  background: linear-gradient(135deg, #C4893A, #E8A849);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -1px; line-height: 1.3;
}
.hero-desc {
  font-size: 17px; color: #504f49;
  line-height: 1.8; margin-bottom: 36px;
}
.hero-actions {
  display: flex; gap: 16px;
  justify-content: center; margin-bottom: 60px;
}
.btn-lg { padding: 14px 36px; font-size: 16px; font-family: 'Outfit', sans-serif; }
.btn-ghost {
  background: transparent;
  border: 1px solid rgba(0,0,0,0.12);
  color: #504f49;
}
.btn-ghost:hover { border-color: var(--amber-dim); color: var(--amber); }

/* ═══ 特性 ═══ */
.features { padding: 80px 40px; }
.features-inner, .workflow-inner { max-width: 1100px; margin: 0 auto; }
.section-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 32px; font-weight: 700;
  color: var(--text-primary);
  text-align: center; margin-bottom: 48px;
}
.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}
.feature-card {
  padding: 28px;
  background: var(--ink-mid);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: var(--radius);
  transition: all 0.3s var(--ease-out);
  font-family: 'Outfit', sans-serif;
}
.feature-card:hover {
  border-color: rgba(232,168,73,0.15);
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.2);
}
.feature-icon { font-size: 28px; margin-bottom: 16px; color: var(--amber); }
.feature-card h3 { font-size: 17px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; }
.feature-card p { font-size: 14px; color: var(--text-secondary); line-height: 1.6; }

/* ═══ 工作流程 ═══ */
.workflow { padding: 40px 40px 80px; }
.steps { display: flex; align-items: center; justify-content: center; gap: 16px; }
.step {
  text-align: center; padding: 24px;
  background: var(--ink-mid);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: var(--radius); min-width: 180px;
  transition: all 0.3s var(--ease-out);
}
.step:hover {
  transform: translateY(-4px);
  border-color: rgba(232,168,73,0.15);
  box-shadow: 0 8px 30px rgba(0,0,0,0.2);
}
.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 32px; font-weight: 800;
  color: rgba(232,168,73,0.2); margin-bottom: 8px;
}
.step h3 { font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px; }
.step p { font-size: 13px; color: var(--text-muted); }
.step-arrow { font-size: 20px; color: var(--text-muted); }

/* ═══ 页脚 ═══ */
.home-footer { padding: 40px; border-top: 1px solid rgba(255,255,255,0.04); }
.footer-inner { max-width: 1100px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; }
.footer-brand { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; color: var(--text-secondary); }
.footer-logo { color: var(--amber); font-size: 18px; }
.footer-copy { font-size: 13px; color: var(--text-muted); }

/* ═══ 暗色模式 — 画作反色 + 文字适配 ═══ */
.hero-painting {
  filter: invert(1) brightness(0.7) contrast(1.1);
}
[data-theme="dark"] .hero .hero-badge { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.1); color: #E8A849; }
[data-theme="dark"] .hero .hero-title .line1 { color: #E8E2D6; }
[data-theme="dark"] .hero .hero-title .line2 {
  background: linear-gradient(135deg, #E8A849, #F59E0B);
  -webkit-background-clip: text; background-clip: text;
}
[data-theme="dark"] .hero .hero-desc { color: #9A9488; }
[data-theme="dark"] .hero .btn-ghost { border-color: rgba(255,255,255,0.12); color: #9A9488; }
[data-theme="dark"] .hero .btn-ghost:hover { border-color: var(--amber-dim); color: var(--amber); }
[data-theme="dark"] .hero .preview-window { background: var(--ink-mid); border-color: rgba(255,255,255,0.06); box-shadow: 0 20px 60px rgba(0,0,0,0.4); }
[data-theme="dark"] .hero .preview-chrome { background: var(--ink-light); border-bottom-color: rgba(255,255,255,0.04); }
[data-theme="dark"] .hero-hint { color: #6B665E; }

/* ═══ 日间模式 ═══ */
[data-theme="light"] .hero-painting {
  filter: none;
}
[data-theme="light"] .home { background: #fcfaf8; }
[data-theme="light"] .home-nav { background: rgba(252,250,248,0.92); border-bottom-color: rgba(0,0,0,0.06); }
[data-theme="light"] .step { background: #fff; border-color: rgba(0,0,0,0.06); }
[data-theme="light"] .step h3 { color: #26251e; }
[data-theme="light"] .step p { color: #979696; }
[data-theme="light"] .section-title { color: #26251e; }
[data-theme="light"] .home-footer { border-top-color: rgba(0,0,0,0.06); }
[data-theme="light"] .footer-brand { color: #504f49; }
[data-theme="light"] .footer-copy { color: #979696; }
</style>
