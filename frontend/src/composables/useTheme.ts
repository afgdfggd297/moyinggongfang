import { ref } from 'vue'

const saved = typeof window !== 'undefined' ? localStorage.getItem('theme') : null
const initial: 'dark' | 'light' = saved === 'light' ? 'light' : 'dark'
const themeState = ref<'dark' | 'light'>(initial)

function applyTheme(t: 'dark' | 'light') {
  document.documentElement.setAttribute('data-theme', t)
}

// 初始化
applyTheme(initial)

export function useTheme() {
  function toggle() {
    themeState.value = themeState.value === 'dark' ? 'light' : 'dark'
    localStorage.setItem('theme', themeState.value)
    applyTheme(themeState.value)
  }

  return {
    theme: themeState,
    toggle,
  }
}
