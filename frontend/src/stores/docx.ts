/** DOCX 状态管理 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as docxApi from '../api/docx'
import type { DocxPlanResponse, DocxOutlineItem, DataSource } from '../api/docx'
import { useHistory } from '../composables/useHistory'

export type DocxStep = 'input' | 'plan' | 'preview' | 'download'

export const useDocxStore = defineStore('docx', () => {
  const { historyList, addEntry, removeEntry } = useHistory()

  // 状态
  const currentStep = ref<DocxStep>('input')
  const planId = ref('')
  const title = ref('')
  const outline = ref<DocxOutlineItem[]>([])
  const suggestedStyle = ref('formal')
  const planSummary = ref('')
  const dataSources = ref<DataSource[]>([])
  const selectedStyle = ref('formal')
  const customStyleDesc = ref('')
  const markdownContent = ref('')
  const loading = ref(false)
  const error = ref('')
  const streaming = ref(false)
  const streamProgress = ref('')

  // 计算属性
  const hasPlan = computed(() => !!planId.value)
  const hasContent = computed(() => !!markdownContent.value)

  // 创建方案
  async function createPlan(text: string, extraInfo?: string, enableSearch?: boolean) {
    loading.value = true
    error.value = ''
    try {
      const result = await docxApi.createDocxPlan({
        text,
        extra_info: extraInfo,
        enable_search: enableSearch,
      })

      planId.value = result.plan_id
      title.value = result.title
      outline.value = result.outline
      suggestedStyle.value = result.suggested_style
      planSummary.value = result.summary
      dataSources.value = result.data_sources || []
      selectedStyle.value = result.suggested_style
      currentStep.value = 'plan'

      addEntry(planId.value, title.value, 'plan')
      console.log('[DOCX Store] 方案创建成功:', result.plan_id)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '方案创建失败'
      error.value = msg
      console.error('[DOCX Store] 方案创建失败:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  // 确认方案并生成内容（流式）
  async function confirmPlanStream() {
    if (!planId.value) return

    loading.value = true
    streaming.value = true
    error.value = ''
    streamProgress.value = '开始生成...'

    try {
      await docxApi.confirmDocxPlanStream(
        {
          plan_id: planId.value,
          style: selectedStyle.value,
          custom_style: customStyleDesc.value,
        },
        {
          onStart: (msg) => {
            streamProgress.value = msg
          },
          onChunk: (chunk, full) => {
            markdownContent.value = full
            streamProgress.value = `已生成 ${Math.floor(full.length / 1024)}KB...`
          },
          onDone: (html, t) => {
            markdownContent.value = html
            title.value = t || title.value
            currentStep.value = 'preview'
            streamProgress.value = '生成完成'
          },
          onError: (msg) => {
            error.value = msg
            streamProgress.value = ''
          },
        }
      )
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '内容生成失败'
      error.value = msg
      console.error('[DOCX Store] 内容生成失败:', e)
    } finally {
      loading.value = false
      streaming.value = false
    }
  }

  // 保存编辑
  async function saveEdit() {
    if (!planId.value || !markdownContent.value) return

    loading.value = true
    error.value = ''
    try {
      await docxApi.editDocxHtml({
        plan_id: planId.value,
        markdown_content: markdownContent.value,
      })
      console.log('[DOCX Store] 编辑保存成功')
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '保存失败'
      error.value = msg
      console.error('[DOCX Store] 保存失败:', e)
    } finally {
      loading.value = false
    }
  }

  // 导出DOCX
  async function exportDocx() {
    if (!planId.value || !markdownContent.value) return

    loading.value = true
    error.value = ''
    try {
      await docxApi.exportDocx({
        plan_id: planId.value,
        markdown_content: markdownContent.value,
      })

      // 触发下载
      const url = docxApi.getDocxDownloadUrl(planId.value)
      const a = document.createElement('a')
      a.href = url
      a.download = `${title.value || '文档'}.docx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)

      currentStep.value = 'download'
      console.log('[DOCX Store] 导出成功')
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '导出失败'
      error.value = msg
      console.error('[DOCX Store] 导出失败:', e)
    } finally {
      loading.value = false
    }
  }

  // 步骤导航
  function goToStep(step: DocxStep) {
    currentStep.value = step
  }

  // 加载方案（从历史记录）
  async function loadPlan(id: string) {
    loading.value = true
    error.value = ''
    try {
      const result = await docxApi.getDocxPlan(id)
      planId.value = result.plan_id
      title.value = result.title
      outline.value = result.outline
      suggestedStyle.value = result.suggested_style
      planSummary.value = result.summary
      dataSources.value = result.data_sources || []
      selectedStyle.value = result.suggested_style
      markdownContent.value = result.markdown_content || ''

      if (markdownContent.value) {
        currentStep.value = 'preview'
      } else {
        currentStep.value = 'plan'
      }

      console.log('[DOCX Store] 方案加载成功:', id)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '方案加载失败'
      error.value = msg
      console.error('[DOCX Store] 方案加载失败:', e)
    } finally {
      loading.value = false
    }
  }

  // 重置
  function reset() {
    currentStep.value = 'input'
    planId.value = ''
    title.value = ''
    outline.value = []
    suggestedStyle.value = 'formal'
    planSummary.value = ''
    dataSources.value = []
    selectedStyle.value = 'formal'
    customStyleDesc.value = ''
    markdownContent.value = ''
    loading.value = false
    error.value = ''
    streaming.value = false
    streamProgress.value = ''
  }

  return {
    currentStep,
    planId,
    title,
    outline,
    suggestedStyle,
    planSummary,
    dataSources,
    selectedStyle,
    customStyleDesc,
    markdownContent,
    loading,
    error,
    streaming,
    streamProgress,
    hasPlan,
    hasContent,
    historyList,
    createPlan,
    confirmPlanStream,
    saveEdit,
    exportDocx,
    goToStep,
    loadPlan,
    removeEntry,
    reset,
  }
})
