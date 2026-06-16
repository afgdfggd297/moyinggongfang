import { ref, watchEffect } from 'vue'

export interface HistoryEntry {
  planId: string
  title: string
  time: string
  step: string
}

const STORAGE_KEY = 'ppt_history'
const MAX_ITEMS = 20

function load(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function save(list: HistoryEntry[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

const historyList = ref<HistoryEntry[]>(load())

export function useHistory() {
  function addEntry(planId: string, title: string, step: string) {
    // 去重
    const existing = historyList.value.find(h => h.planId === planId)
    if (existing) {
      existing.title = title
      existing.step = step
      existing.time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    } else {
      historyList.value.unshift({
        planId,
        title: title || '未命名方案',
        step,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      })
    }
    // 限制数量
    if (historyList.value.length > MAX_ITEMS) {
      historyList.value = historyList.value.slice(0, MAX_ITEMS)
    }
    save(historyList.value)
  }

  function removeEntry(planId: string) {
    historyList.value = historyList.value.filter(h => h.planId !== planId)
    save(historyList.value)
  }

  function clearAll() {
    historyList.value = []
    save(historyList.value)
  }

  return {
    historyList,
    addEntry,
    removeEntry,
    clearAll,
  }
}
