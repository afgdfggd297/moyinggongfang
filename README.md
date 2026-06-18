# 墨印工坊 · InkPress Studio

AI 驱动的演示文稿生成工具。输入文字，AI 自动规划方案、联网搜索资料、生成精美的 HTML 幻灯片，支持可视化编辑和一键导出 PPTX。

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Vue](https://img.shields.io/badge/vue-3.4+-green)

---

## ✨ 功能特性

### 🎯 智能方案规划
- 输入主题内容，AI 自动分析并生成结构化的演示方案
- 支持 3~15 页自定义页数
- 4 种预设风格（商务、学术、简约、创意）+ 自定义风格描述
- 支持多选配色方案 + 自定义 HEX 颜色
- 7 种字体方案（A~G）
- 高级定制：布局密度、背景样式、页码、圆角、阴影、对齐方式

### 🔍 联网搜索
- 自动 Bing 中国搜索相关资料
- WebFetch 五阶段流水线：URL 校验 → 抓取缓存 → HTML→Markdown → 智能路由 → AI 摘要
- 受信站点快速通道（GitHub、StackOverflow 等 80+ 域名直接返回 Markdown）
- 版权合规摘要（引用限制 125 字符，自动改写）

### 📊 可视化编辑
- 所见即所得的 iframe 预览
- 支持直接点击文字进行修改
- 深色/浅色模式预览切换

### 📥 一键导出
- HTML 幻灯片逐页截图（html2ppt + Playwright Chromium）
- python-pptx 合并为标准 PPTX 文件
- 可配置幻灯片尺寸、缩放倍数、背景色

### 🎨 首页水粉效果
- MiMo 风格水墨画揭示效果（Canvas 遮罩 + 鼠标交互）
- 深色/浅色模式自适应
- 浮动动画 + 响应式布局

---

## 🛠 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3 + TypeScript | Composition API + `<script setup>` |
| 状态管理 | Pinia | 全局 PPT 状态 + SSE 流式处理 |
| 路由 | Vue Router | `/` 首页 + `/create` 创作台 |
| 构建 | Vite | 开发热重载 + 生产构建 |
| UI 框架 | 自定义 CSS | 深色/浅色主题系统 |
| 后端 | FastAPI | 异步 API + SSE 流式输出 |
| 工作流 | LangGraph | plan_node → html_generate_node |
| LLM | OpenAI 兼容 API | MiMo V2.5 / 任意兼容模型 |
| 缓存 | Redis | 方案存储（TTL 管理） |
| 导出 | html2ppt + python-pptx | 逐页截图 → PPTX 合并 |
| 浏览器 | Playwright | Chromium 无头截图 |
| 搜索 | Bing 中国 | 自动抓取 + 解析 |
| 网页抓取 | requests + html2text | 五阶段 WebFetch 流水线 |

---

## 📁 项目结构

```
lianshou/
├── README.md                   # 项目说明
├── PROGRESS.md                 # 开发进度记录
├── docker-compose.yml          # Docker 三容器编排
├── .gitignore
│
├── backend/                    # FastAPI 后端
│   ├── Dockerfile              # Docker 镜像（Python + Node.js + Playwright）
│   ├── .dockerignore
│   ├── .env.example            # 环境变量模板
│   ├── requirements.txt        # Python 依赖
│   ├── run.py                  # 启动入口
│   ├── resources/
│   │   └── template.html       # HTML 模板
│   └── app/
│       ├── main.py             # FastAPI 应用 + CORS + 路由注册
│       ├── core/
│       │   ├── config.py       # 统一配置（Settings + .env 加载）
│       │   ├── logging.py      # 日志配置
│       │   └── langgraph/
│       │       ├── state.py    # PPTState 数据流
│       │       ├── graph.py    # 工作流图编译
│       │       ├── nodes.py    # plan_node + html_generate_node
│       │       └── edges.py    # 条件边
│       ├── api/v1/
│       │   └── ppt.py          # API 路由（plan/update/confirm/stream/edit/export）
│       ├── schemas/
│       │   └── ppt.py          # Pydantic 请求/响应模型
│       ├── prompts/
│       │   ├── plan_prompt.py  # 方案规划提示词（7 种字体方案 A~G）
│       │   └── html_prompt.py  # HTML 生成提示词（自定义选项）
│       └── services/
│           ├── llm_service.py  # LLM 调用（同步/异步/流式/JSON）
│           ├── ppt_export.py   # PPTX 导出（html2ppt + python-pptx）
│           ├── redis_store.py  # Redis 方案存储
│           ├── search_service.py # Bing 中国搜索
│           └── web_fetch.py    # 五阶段 WebFetch 流水线
│
└── frontend/                   # Vue 3 前端
    ├── Dockerfile              # Docker 镜像（Node 构建 + Nginx 托管）
    ├── .dockerignore
    ├── nginx.conf              # Nginx 配置（静态文件 + API/SSE 代理）
    ├── package.json
    ├── vite.config.ts          # Vite 配置 + 开发代理
    ├── index.html
    └── src/
        ├── main.ts             # 应用入口
        ├── App.vue             # 路由容器 + 页面过渡动画
        ├── style.css           # 全局样式（深色/浅色主题变量）
        ├── router/index.ts     # Vue Router 配置
        ├── stores/ppt.ts       # Pinia 状态管理（SSE 流式处理）
        ├── types/ppt.ts        # TypeScript 类型定义
        ├── api/ppt.ts          # API 封装（fetch + SSE）
        ├── composables/
        │   ├── useTheme.ts     # 深色/浅色模式（localStorage 持久化）
        │   └── useHistory.ts   # 对话历史（localStorage，最多 20 条）
        ├── views/
        │   ├── Home.vue        # 首页（水粉效果 + Canvas 遮罩）
        │   └── Create.vue      # 创作工作台（4 步流程 + 侧边栏）
        └── components/
            ├── StepInput.vue   # 01 输入（文本框 + 搜索开关）
            ├── StepPlan.vue    # 02 方案（大纲编辑 + 风格/配色/字体/高级设置）
            ├── StepPreview.vue # 03 预览（iframe + contentEditable 编辑）
            ├── StepDownload.vue# 04 下载（成功动画）
            └── ChatHistory.vue # 左侧历史栏（可收起 + 删除）
```

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

**前置条件：** 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

```bash
# 克隆仓库
git clone https://github.com/afgdfggd297/moyinggongfang.git
cd moyinggongfang

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 MIMO_API_KEY

# 构建并启动
docker compose up -d --build

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

服务访问：
- 前端：http://localhost
- 后端 API：http://localhost:8000/docs（Swagger 文档）

### 方式二：本地开发

**前置条件：** Python 3.11+、Node.js 18+、Redis

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 配置环境变量
cp .env.example .env
# 编辑 .env，至少填入 MIMO_API_KEY

# 启动 Redis（确保 6379 端口可用）
# Windows: redis-server
# Linux: sudo systemctl start redis
# Docker: docker run -d -p 6379:6379 redis:7-alpine redis-server --requirepass deepresearch

# 启动后端
python run.py
# 启动于 http://127.0.0.1:8000
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 启动于 http://localhost:5173
```

---

## ⚙️ 配置说明

所有配置项通过环境变量或 `.env` 文件管理。复制 `backend/.env.example` 为 `backend/.env` 后按需修改。

### LLM 配置

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `MIMO_API_KEY` | — | ✅ | API 密钥 |
| `MIMO_BASE_URL` | `https://token-plan-cn.xiaomimimo.com/v1` | | API 地址（支持任意 OpenAI 兼容 API） |
| `MIMO_LLM_MODEL` | `mimo-v2.5-pro` | | 模型名称 |
| `LLM_TOTAL_TIMEOUT` | `120` | | LLM 总超时（秒） |
| `MAX_LLM_CALL_RETRIES` | `3` | | LLM 最大重试次数 |
| `LLM_PLAN_TEMPERATURE` | `0.8` | | 方案规划温度（0.0~1.0，越高越有创意） |
| `LLM_HTML_TEMPERATURE` | `0.9` | | HTML 生成温度 |
| `LLM_STREAM_TEMPERATURE` | `0.9` | | 流式输出温度 |

### PPT 导出

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PPT_SLIDE_W` | `13.333` | 幻灯片宽度（英寸，16:9 为 13.333×7.5） |
| `PPT_SLIDE_H` | `7.5` | 幻灯片高度（英寸） |
| `PPT_PX_W` | `1280` | 截图像素宽度 |
| `PPT_PX_H` | `720` | 截图像素高度 |
| `PPT_SCALE` | `2` | html2ppt 缩放倍数（2 = Retina） |
| `PPT_TIMEOUT` | `60` | html2ppt 单页超时（秒） |
| `PPT_HTML2PPT_BIN` | `""` | html2ppt 路径，留空自动查找 PATH |
| `PPT_BG_COLOR` | `#ffffff` | 幻灯片背景色 |

### 搜索与 WebFetch

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SEARCH_ENGINE_URL` | `https://cn.bing.com/search` | 搜索引擎 URL |
| `SEARCH_TIMEOUT` | `10` | 搜索请求超时（秒） |
| `SEARCH_MAX_RESULTS` | `5` | 单次搜索最大结果数 |
| `SEARCH_QUERY_MAX_LEN` | `80` | 搜索关键词最大长度（字符） |
| `WEBFETCH_MAX_URL_LENGTH` | `2000` | URL 最大长度 |
| `WEBFETCH_MAX_RESPONSE_MB` | `10` | 最大响应体积（MB） |
| `WEBFETCH_CACHE_MAXSIZE` | `100` | LRU 缓存条数 |
| `WEBFETCH_CACHE_TTL` | `900` | 缓存过期时间（秒） |
| `WEBFETCH_MAX_MARKDOWN_KB` | `100` | Markdown 最大长度（KB） |
| `WEBFETCH_SUMMARY_MAX_CHARS` | `8000` | 摘要输入截断字符数 |
| `WEBFETCH_SUMMARY_TEMPERATURE` | `0.4` | 摘要 LLM 温度 |
| `WEBFETCH_SUMMARY_MAX_TOKENS` | `1500` | 摘要最大输出 token |

### 基础设施

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `REDIS_URL` | `redis://:deepresearch@127.0.0.1:6379/0` | Redis 连接地址 |
| `UPLOAD_DIR` | `./uploads` | PPTX 文件输出目录 |
| `CORS_ORIGINS` | `["http://localhost:3000", ...]` | 允许的前端域名 |

---

## 📝 工作流程

```
用户输入文本
    ↓
┌─────────────────────────────────────┐
│  plan_node                          │
│  • 可选：Bing 搜索 + WebFetch 摘要  │
│  • LLM 分析生成结构化方案           │
│  • 输出：标题 + 层级大纲 + 摘要     │
└─────────────────────────────────────┘
    ↓
用户确认方案
    ↓
┌─────────────────────────────────────┐
│  自定义选项                          │
│  • 风格：商务/学术/简约/创意/自定义  │
│  • 配色：多选 + 自定义 HEX          │
│  • 字体：7 种方案（A~G）            │
│  • 高级：密度/背景/页码/圆角/阴影   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  html_generate_node                 │
│  • LLM 生成完整 HTML 幻灯片        │
│  • 支持 SSE 流式输出                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  预览与编辑                          │
│  • iframe 渲染 HTML                 │
│  • contentEditable 直接修改文字     │
│  • 保存修改回写                     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  导出 PPTX                          │
│  • Playwright 逐页截图              │
│  • python-pptx 合并为 PPTX         │
│  • 下载文件                         │
└─────────────────────────────────────┘
```

---

## 🐛 常见问题

### Playwright 启动失败
```bash
# 确保安装了 Chromium
playwright install chromium

# Windows 可能需要安装依赖
playwright install-deps
```

### html2ppt 找不到
```bash
# 全局安装
npm install -g html2ppt

# 或在 .env 中指定路径
PPT_HTML2PPT_BIN=D:\nodejs\node_global\html2ppt.cmd
```

### Redis 连接失败
```bash
# 检查 Redis 是否运行
redis-cli ping

# Docker 方式启动 Redis
docker run -d -p 6379:6379 redis:7-alpine redis-server --requirepass deepresearch
```

### 前端代理 404
检查 `vite.config.ts` 中的 proxy target 是否为 `http://127.0.0.1:8000`（不要用 localhost，避免 IPv6 问题）。

---

## 📄 License

[MIT](LICENSE)
