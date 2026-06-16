/** PPT Store - 状态管理，支持流式输出 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { StepType, StyleType, ColorType, DataSource, OutlineItem } from '../types/ppt'
import * as api from '../api/ppt'
import { useHistory } from '../composables/useHistory'

export const usePptStore = defineStore('ppt', () => {
  const { historyList, addEntry, removeEntry } = useHistory()
  // 状态
  const currentStep = ref<StepType>('input')
  const planId = ref('')
  const title = ref('')
  const outline = ref<OutlineItem[]>([])
  const suggestedPages = ref(8)
  const suggestedStyle = ref<StyleType>('business')
  const planSummary = ref('')
  const dataSources = ref<DataSource[]>([])

  // 用户选择
  const selectedPages = ref(8)
  const selectedStyle = ref<StyleType>('business')
  const selectedColors = ref<ColorType[]>(['blue'])
  const customColors = ref<string[]>([])
  const customStyleDesc = ref('')

  // 用户自定义 PPT 元素
  const fontScheme = ref('')
  const layoutDensity = ref('')
  const bgStyle = ref('')
  const pageNumberStyle = ref('')
  const borderRadius = ref('')
  const shadowLevel = ref('')
  const contentAlign = ref('')

  // HTML内容
  const htmlContent = ref('')
  const streamingContent = ref('') // 流式生成的中间内容
  const loading = ref(false)
  const streaming = ref(false) // 是否正在流式生成
  const error = ref('')

  // 搜索开关
  const enableSearch = ref(true)

  // 步骤导航
  function goToStep(step: StepType) {
    currentStep.value = step
    console.log(`[Store] 切换步骤: ${step}`)
  }

  // 步骤1: 提交需求
  async function submitPlan(text: string, extraInfo?: string) {
    loading.value = true
    error.value = ''
    try {
      console.log('[Store] 提交方案:', { text, extraInfo, enableSearch: enableSearch.value })
      const result = await api.createPlan({ text, extra_info: extraInfo, enable_search: enableSearch.value })
      planId.value = result.plan_id
      title.value = result.title
      outline.value = result.outline
      suggestedPages.value = result.suggested_pages
      suggestedStyle.value = result.suggested_style as StyleType
      planSummary.value = result.summary
      dataSources.value = result.data_sources || []
      selectedPages.value = result.suggested_pages
      selectedStyle.value = result.suggested_style as StyleType
      goToStep('plan')
      // 记录历史
      addEntry(planId.value, title.value, 'plan')
      console.log('[Store] 方案创建成功:', result.plan_id)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '方案创建失败'
      error.value = msg
      console.error('[Store] 方案创建失败:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  // 编辑方案
  async function updatePlan(updates: { title?: string; outline?: string[] }) {
    if (!planId.value) return
    try {
      const result = await api.updatePlan(planId.value, updates)
      title.value = result.title
      outline.value = result.outline
      selectedPages.value = result.suggested_pages
      console.log('[Store] 方案已更新')
    } catch (e: unknown) {
      console.error('[Store] 更新方案失败:', e)
    }
  }

  // 步骤2: 确认方案并生成HTML（流式）
  async function confirmAndGenerate() {
    if (!planId.value) {
      error.value = '请先创建方案'
      return
    }
    loading.value = true
    streaming.value = true
    error.value = ''
    streamingContent.value = ''

    try {
      console.log('[Store] 开始流式生成HTML')
      await api.confirmPlanStream(
        {
          plan_id: planId.value,
          pages: selectedPages.value,
          style: selectedStyle.value,
          color_scheme: selectedColors.value.join(','),
          custom_colors: customColors.value,
          custom_style: customStyleDesc.value,
          font_scheme: fontScheme.value,
          layout_density: layoutDensity.value,
          bg_style: bgStyle.value,
          page_number: pageNumberStyle.value,
          border_radius: borderRadius.value,
          shadow_level: shadowLevel.value,
          content_align: contentAlign.value,
        },
        {
          onStart: (message) => {
            console.log('[Store] 流式生成开始:', message)
          },
          onChunk: (_chunk, fullContent) => {
            streamingContent.value = fullContent
          },
          onDone: (html, htmlTitle) => {
            htmlContent.value = html
            title.value = htmlTitle || title.value
            streaming.value = false
            goToStep('preview')
            console.log('[Store] 流式生成完成, 长度:', html.length)
          },
          onError: (msg) => {
            error.value = msg
            streaming.value = false
            console.error('[Store] 流式生成错误:', msg)
          },
        }
      )
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'HTML生成失败'
      error.value = msg
      streaming.value = false
      console.error('[Store] HTML生成失败:', e)
    } finally {
      loading.value = false
    }
  }

  // 步骤3: 保存编辑
  async function saveEdit() {
    if (!planId.value) return
    loading.value = true
    error.value = ''
    try {
      console.log('[Store] 保存编辑, 长度:', htmlContent.value.length)
      await api.editHtml({ plan_id: planId.value, html_content: htmlContent.value })
      console.log('[Store] 编辑保存成功')
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '保存失败'
      error.value = msg
      console.error('[Store] 保存失败:', e)
    } finally {
      loading.value = false
    }
  }

  // 步骤4: 导出PPT
  async function exportPpt() {
    if (!planId.value) return
    loading.value = true
    error.value = ''
    try {
      console.log('[Store] 导出PPT:', { planId: planId.value })
      const result = await api.exportPptx({
        plan_id: planId.value,
        html_content: htmlContent.value,
      })
      goToStep('download')
      console.log('[Store] PPT导出成功:', result)
      return result
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '导出失败'
      error.value = msg
      console.error('[Store] 导出失败:', e)
    } finally {
      loading.value = false
    }
  }

  // 加载历史方案
  async function loadPlan(id: string) {
    try {
      console.log('[Store] 加载方案:', id)
      const result = await api.getPlan(id)
      planId.value = result.plan_id
      title.value = result.title
      outline.value = result.outline
      suggestedPages.value = result.suggested_pages
      suggestedStyle.value = result.suggested_style as StyleType
      planSummary.value = result.summary
      dataSources.value = result.data_sources || []
      htmlContent.value = result.html_content || ''
      selectedPages.value = result.suggested_pages
      selectedStyle.value = result.suggested_style as StyleType

      if (htmlContent.value) {
        goToStep('preview')
      } else {
        goToStep('plan')
      }
      console.log('[Store] 方案加载成功:', id)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载方案失败'
      error.value = msg
      console.error('[Store] 加载方案失败:', e)
    }
  }

  // 重置
  function reset() {
    currentStep.value = 'input'
    planId.value = ''
    title.value = ''
    outline.value = []
    dataSources.value = []
    htmlContent.value = ''
    streamingContent.value = ''
    streaming.value = false
    error.value = ''
    console.log('[Store] 已重置')
  }

  return {
    currentStep,
    planId,
    title,
    outline,
    suggestedPages,
    suggestedStyle,
    planSummary,
    dataSources,
    selectedPages,
    selectedStyle,
    selectedColors,
    customColors,
    customStyleDesc,
    fontScheme,
    layoutDensity,
    bgStyle,
    pageNumberStyle,
    borderRadius,
    shadowLevel,
    contentAlign,
    htmlContent,
    streamingContent,
    loading,
    streaming,
    error,
    enableSearch,
    historyList,
    removeEntry,
    goToStep,
    submitPlan,
    updatePlan,
    confirmAndGenerate,
    saveEdit,
    exportPpt,
    loadPlan,
    reset,
  }
})
