<script setup lang="ts">
import { useTheme } from './composables/useTheme'
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'
import { ref, onMounted } from 'vue'

const { theme, toggle: toggleTheme } = useTheme()
const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)

// Restore auth state on app init
onMounted(async () => {
  try {
    await auth.checkAuth()
  } catch (e) {
    // Silently fail — user stays unauthenticated
  }
})

router.beforeEach(() => { loading.value = true })
router.afterEach(() => { setTimeout(() => { loading.value = false }, 300) })
</script>

<template>
  <!-- 全局加载条 -->
  <Transition name="loading-fade">
    <div v-if="loading" class="loading-bar">
      <div class="loading-progress" />
    </div>
  </Transition>

  <router-view v-slot="{ Component }">
    <Transition name="page" mode="out-in">
      <component :is="Component" />
    </Transition>
  </router-view>
</template>

<style scoped>
.loading-bar {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 3px;
  z-index: 9999;
  background: transparent;
}
.loading-progress {
  height: 100%;
  background: linear-gradient(90deg, var(--amber), #F59E0B, var(--amber));
  background-size: 200% 100%;
  animation: loadingSlide 1s ease-in-out infinite;
  border-radius: 0 2px 2px 0;
  box-shadow: 0 0 12px rgba(232,168,73,0.4);
}
@keyframes loadingSlide {
  0% { width: 0%; margin-left: 0; }
  50% { width: 60%; margin-left: 20%; }
  100% { width: 0%; margin-left: 100%; }
}

.loading-fade-enter-active { transition: opacity 0.15s; }
.loading-fade-leave-active { transition: opacity 0.3s 0.2s; }
.loading-fade-enter-from, .loading-fade-leave-to { opacity: 0; }

.page-enter-active { transition: opacity 0.3s ease, transform 0.3s ease; }
.page-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.page-enter-from { opacity: 0; transform: translateY(8px); }
.page-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
