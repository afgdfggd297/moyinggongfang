# PPT 生成器项目进度文档

## 项目概述
基于 LangChain + LangGraph 的 AI PPT 生成器，支持流式输出、交互式编辑和导出。

## 技术栈
- **后端**: FastAPI + LangGraph 1.2.4 + LangChain 1.4.6 (OpenAI兼容API - MiMo)
- **前端**: Vue 3 + TypeScript + Vite + Pinia + Axios
- **PPT导出**: python-pptx (HTML → PPTX)
- **AI模型**: MiMo v2.5 Pro (小米)
- **流式输出**: SSE (Server-Sent Events)

## 工作流程
1. 用户输入文字/文本/计划
2. Agent 1 (plan_node): 思考方案 → 返回给前端（标题、大纲、建议页数、风格）
3. 用户选择页数和风格 → 人工确认方案
4. Agent 2 (html_generate_node): **SSE流式**生成打印友好HTML PPT（注入示例文件）
5. 返回HTML给前端渲染，用户可编辑HTML代码
6. 用户修改确认 → 发回后端保存
7. 用户确认导出 → HTML2PPT转换 → 前端下载PPTX

## 项目结构
```
E:\lianshou\
├── PROGRESS.md                     # 进度文档
├── backend/
│   ├── .env                        # 环境配置（MiMo API Key）
│   ├── requirements.txt            # Python依赖
│   ├── run.py                      # 启动入口
│   └── app/
│       ├── main.py                 # FastAPI应用入口
│       ├── core/
│       │   ├── config.py           # 配置模块
│       │   ├── logging.py          # 日志配置
│       │   └── langgraph/
│       │       ├── state.py        # PPTState 状态定义
│       │       ├── nodes.py        # plan_node, html_generate_node
│       │       ├── edges.py        # 路由逻辑
│       │       └── graph.py        # 工作流图编译
│       ├── prompts/
│       │   ├── plan_prompt.py      # 方案规划提示词
│       │   └── html_prompt.py      # HTML生成提示词（含示例注入）
│       ├── schemas/
│       │   └── ppt.py              # Pydantic数据模型
│       ├── services/
│       │   ├── llm_service.py      # LLM调用服务（支持流式）
│       │   └── ppt_export.py       # HTML→PPTX导出服务
│       └── api/v1/
│           └── ppt.py              # API路由（含SSE流式端点）
└── frontend/                       # Vue 3 + TypeScript 前端
    ├── package.json
    ├── vite.config.ts              # Vite配置（含API代理）
    └── src/
        ├── main.ts                 # 入口
        ├── App.vue                 # 根组件
        ├── style.css               # 全局样式
        ├── types/ppt.ts            # TypeScript类型定义
        ├── api/ppt.ts              # API服务（含SSE流式调用）
        ├── stores/ppt.ts           # Pinia状态管理（含流式状态）
        └── components/
            ├── StepInput.vue       # 步骤1: 输入内容
            ├── StepPlan.vue        # 步骤2: 确认方案（含流式进度）
            ├── StepPreview.vue     # 步骤3: 预览编辑
            └── StepDownload.vue    # 步骤4: 下载PPT
```

## API 接口
| 方法 | 路径 | 说明 | 流式 |
|------|------|------|------|
| POST | /api/v1/ppt/plan | 提交需求，获取AI方案 | ❌ |
| POST | /api/v1/ppt/confirm-plan | 确认方案，生成HTML | ❌ |
| POST | /api/v1/ppt/confirm-plan/stream | 确认方案，**流式**生成HTML | ✅ SSE |
| POST | /api/v1/ppt/edit | 用户编辑后提交HTML | ❌ |
| POST | /api/v1/ppt/export | 导出PPTX文件 | ❌ |
| GET | /api/v1/ppt/download/{plan_id} | 下载PPTX文件 | ❌ |
| GET | /api/v1/ppt/html/{plan_id} | 获取HTML内容 | ❌ |

## 进度追踪

### 阶段一：项目基础搭建 ✅
- [x] 后端项目结构 + 依赖配置
- [x] 前端项目结构 (Vue 3 + TypeScript)
- [x] 配置模块（参考qiniu项目MiMo API配置）
- [x] LLM服务封装（含重试机制）

### 阶段二：LangGraph 工作流 ✅
- [x] 状态定义 (PPTState)
- [x] 方案规划节点 (plan_node)
- [x] HTML生成节点 (html_generate_node) - 注入示例HTML
- [x] 条件边和路由逻辑
- [x] 图编译

### 阶段三：API 接口 ✅
- [x] POST /api/v1/ppt/plan - 提交需求，获取方案
- [x] POST /api/v1/ppt/confirm-plan - 确认方案（页数+风格）
- [x] POST /api/v1/ppt/confirm-plan/stream - **SSE流式生成HTML**
- [x] POST /api/v1/ppt/edit - 用户编辑后提交
- [x] POST /api/v1/ppt/export - 导出PPTX
- [x] GET /api/v1/ppt/download/{plan_id} - 下载文件

### 阶段四：前端页面 ✅
- [x] Vue 3 + TypeScript 重构
- [x] Pinia 状态管理
- [x] 步骤1: 输入页面
- [x] 步骤2: 方案选择页面（含流式进度显示）
- [x] 步骤3: HTML预览+编辑页面
- [x] 步骤4: PPT下载页面

### 阶段五：流式输出 ✅
- [x] LLM服务支持流式调用 (call_stream)
- [x] 后端SSE流式端点 (/confirm-plan/stream)
- [x] 前端SSE客户端 (fetch + ReadableStream)
- [x] Pinia store 流式状态管理
- [x] 流式进度UI显示

### 阶段六：测试与优化 ⏳
- [ ] 后端API测试
- [ ] 前端页面测试
- [ ] Playwright E2E测试
- [ ] 打印友好HTML样式优化
- [ ] PPT导出质量验证

## 当前状态
✅ **代码开发完成** - 阶段六：等待测试

## 启动方式

### 后端
```bash
cd E:\lianshou\backend
pip install -r requirements.txt
python run.py
# 后端运行在 http://localhost:8000
```

### 前端
```bash
cd E:\lianshou\frontend
npm install
npm run dev
# 前端运行在 http://localhost:5173
# API自动代理到 http://localhost:8000
```

## 关键设计说明

### 流式输出架构
```
前端 (Vue)                    后端 (FastAPI)              LLM (MiMo)
    │                              │                          │
    │  POST /confirm-plan/stream   │                          │
    │ ─────────────────────────>   │                          │
    │                              │  call_stream()           │
    │                              │ ─────────────────────>   │
    │  SSE: data: {"type":"chunk"} │                          │
    │ <─────────────────────────   │  <─────────────────────  │
    │  (实时渲染进度)               │                          │
    │                              │                          │
    │  SSE: data: {"type":"done"}  │                          │
    │ <─────────────────────────   │                          │
```

### 打印友好HTML PPT
- 每个幻灯片固定 1280×720 像素
- 使用 `page-break-after: always` 实现分页
- 包含 `@page { size: 1280px 720px; margin: 0; }` 打印规则
- 包含 `@media print` 样式适配

### 示例文件注入
- 生成HTML时自动读取 `C:\Users\30976\Desktop\timeanlysis\presentation.html`
- 将示例的CSS样式和结构作为参考注入提示词
- 确保生成的HTML遵循相同的打印友好格式
