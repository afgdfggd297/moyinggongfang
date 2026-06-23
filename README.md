# 墨印工坊 · InkPress Studio

AI 驱动的演示文稿生成工具。输入文字，AI 自动规划方案、联网搜索资料、生成精美的 HTML 幻灯片，支持可视化编辑和一键导出 PPTX。

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Vue](https://img.shields.io/badge/vue-3.4+-green)

---

## ✨ 功能特性

### 🎯 智能方案规划
- 输入主题内容，AI 自动分析并生成结构化的演示方案
- 支持 3~30 页自定义页数
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

### 📄 DOCX 文档生成
- 输入文字内容，AI 自动规划文档结构
- 支持多种文档风格（正式、学术、技术、创意、报告）
- 流式生成 Markdown 内容，pandoc 转换为 HTML 实时预览
- 导出为标准 DOCX 文件（pypandoc，支持全部 Markdown 语法）
- 自动生成目录

### 🔐 用户系统
- 用户注册 / 登录（JWT 认证）
- 个人仪表盘：方案管理、统计数据
- 方案持久化存储（PostgreSQL）
- 方案重命名、删除、复制

### 📋 模板库
- 5 种内置系统模板（商务、学术、创意、极简、科技）
- 模板分类浏览和搜索
- 一键使用模板创建方案

### 🎨 首页水粉效果
- MiMo 风格水墨画揭示效果（Canvas 遮罩 + 鼠标交互）
- 深色/浅色模式自适应
- 浮动动画 + 响应式布局

---

## 🛠 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3 + TypeScript | Composition API + `<script setup>` |
| 状态管理 | Pinia | 全局 PPT 状态 + SSE 流式处理 + Auth 状态 |
| 路由 | Vue Router | `/` 首页 + `/create` 创作台 + `/login` 登录 + `/dashboard` 仪表盘 + `/templates` 模板库 |
| 构建 | Vite | 开发热重载 + 生产构建 |
| UI 框架 | 自定义 CSS | 深色/浅色主题系统 |
| 后端 | FastAPI | 异步 API + SSE 流式输出 |
| 工作流 | LangGraph | plan_node → html_generate_node |
| LLM | OpenAI 兼容 API | MiMo V2.5 / 任意兼容模型 |
| 缓存 | Redis | 方案缓存（快速访问） |
| 数据库 | PostgreSQL 16 | 持久化存储（用户、方案、模板） |
| ORM | SQLAlchemy 2.0 | 异步 ORM + asyncpg |
| 认证 | JWT + bcrypt | python-jose + passlib |
| 导出 | html2ppt + python-pptx | 逐页截图 → PPTX 合并 |
| DOCX 导出 | pypandoc | Markdown → DOCX（pandoc 引擎） |
| 浏览器 | Playwright | Chromium 无头截图 |
| 搜索 | Bing 中国 | 自动抓取 + 解析 |
| 网页抓取 | requests + html2text | 五阶段 WebFetch 流水线 |

---

## 📁 项目结构

```
lianshou/
├── README.md                   # 项目说明
├── PROGRESS.md                 # 开发进度记录
├── docker-compose.yml          # Docker 四容器编排（Redis + PostgreSQL + Backend + Frontend）
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
│       ├── main.py             # FastAPI 应用 + CORS + 路由注册 + DB 初始化
│       ├── core/
│       │   ├── config.py       # 统一配置（Settings + .env 加载）
│       │   ├── logging.py      # 日志配置
│       │   ├── security.py     # JWT + 密码哈希 + 认证依赖
│       │   ├── exceptions.py   # 统一异常处理
│       │   └── langgraph/
│       │       ├── state.py    # PPTState 数据流
│       │       ├── graph.py    # 工作流图编译
│       │       ├── nodes.py    # plan_node + html_generate_node
│       │       ├── edges.py    # 条件边
│       │       ├── docx_state.py # DocxState 数据流（新增）
│       │       ├── docx_graph.py # DOCX 工作流图编译（新增）
│       │       └── docx_nodes.py # docx_plan_node + docx_content_node（新增）
│       ├── api/v1/
│       │   ├── ppt.py          # PPT API（plan/update/confirm/stream/edit/export）
│       │   ├── docx.py         # DOCX API（plan/confirm/stream/edit/export）
│       │   ├── auth.py         # 认证 API（register/login/me）
│       │   ├── templates.py    # 模板 API（list/detail/create）
│       │   └── dashboard.py    # 仪表盘 API（stats/plans/rename/delete/duplicate）
│       ├── db/
│       │   ├── database.py     # SQLAlchemy 异步引擎 + 会话
│       │   ├── models.py       # ORM 模型（User, Plan, Template）
│       │   ├── crud.py         # CRUD 操作
│       │   └── seed_templates.py # 模板种子数据
│       ├── schemas/
│       │   ├── ppt.py          # PPT 请求/响应模型
│       │   ├── auth.py         # 认证请求/响应模型
│       │   └── template.py     # 模板/仪表盘请求/响应模型
│       ├── prompts/
│       │   ├── plan_prompt.py  # 方案规划提示词
│       │   ├── html_prompt.py  # HTML 生成提示词
│       │   ├── docx_plan_prompt.py # DOCX 方案规划提示词
│       │   ├── docx_content_prompt.py # DOCX 内容生成提示词
│       │   └── regenerate_slide_prompt.py # 单页重生成提示词
│       └── services/
│           ├── llm_service.py  # LLM 调用（同步/异步/流式/JSON）
│           ├── ppt_export.py   # PPTX 导出
│           ├── docx_export.py  # DOCX 导出（pypandoc）
│           ├── slide_utils.py  # 幻灯片拆分/替换工具
│           ├── redis_store.py  # Redis 方案缓存
│           ├── search_service.py # Bing 搜索
│           └── web_fetch.py    # WebFetch 流水线
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
        ├── App.vue             # 路由容器 + 页面过渡动画 + Auth 初始化
        ├── style.css           # 全局样式（深色/浅色主题变量）
        ├── config.ts           # 前端全局配置（超时、常量）
        ├── router/index.ts     # Vue Router 配置 + 路由守卫
        ├── stores/
        │   ├── ppt.ts          # PPT 状态管理
        │   ├── docx.ts         # DOCX 状态管理（新增）
        │   └── auth.ts         # 认证状态管理
        ├── types/ppt.ts        # TypeScript 类型定义
        ├── api/
        │   ├── ppt.ts          # PPT API
        │   ├── docx.ts         # DOCX API（新增）
        │   ├── auth.ts         # 认证 API
        │   ├── dashboard.ts    # 仪表盘 API
        │   └── templates.ts    # 模板 API
        ├── composables/
        │   ├── useTheme.ts     # 深色/浅色模式
        │   └── useHistory.ts   # 对话历史
        ├── views/
        │   ├── Home.vue        # 首页（水粉效果 + Auth 导航）
        │   ├── Create.vue      # PPT 创作工作台
        │   ├── CreateDocx.vue  # DOCX 创作工作台（新增）
        │   ├── Login.vue       # 登录/注册页
        │   ├── Dashboard.vue   # 仪表盘
        │   └── Templates.vue   # 模板库
        └── components/
            ├── StepInput.vue   # 01 输入
            ├── StepPlan.vue    # 02 方案
            ├── StepPreview.vue # 03 预览
            ├── StepDownload.vue# 04 下载
            └── ChatHistory.vue # 左侧历史栏
```

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

**前置条件：** 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

```bash
# 克隆仓库
git clone <repo-url>
cd lianshou

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 MIMO_API_KEY

# 构建并启动（包含 Redis + PostgreSQL + Backend + Frontend）
docker compose up -d --build

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

服务访问：
- 前端：http://localhost
- 后端 API：http://localhost:8000/docs（Swagger 文档）
- PostgreSQL：localhost:5432
- Redis：localhost:6379

### 方式二：本地开发

**前置条件：** Python 3.11+、Node.js 18+、Redis、PostgreSQL

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

# 启动 Redis
docker run -d -p 6379:6379 redis:7-alpine redis-server --requirepass deepresearch

# PostgreSQL（使用现有容器或本地安装）
# 默认连接: postgresql+asyncpg://nlit:nlit@localhost:54432/nlit

# 启动后端（自动创建数据库表）
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

### 数据库配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://nlit:nlit@localhost:54432/nlit` | PostgreSQL 连接地址 |
| `SECRET_KEY` | `inkpress-secret-key-change-in-production` | JWT 签名密钥 |

### LLM 配置

| 变量 | 默认值 | 必填 | 说明 |
|------|--------|------|------|
| `MIMO_API_KEY` | — | ✅ | API 密钥 |
| `MIMO_BASE_URL` | `https://token-plan-cn.xiaomimimo.com/v1` | | API 地址 |
| `MIMO_LLM_MODEL` | `mimo-v2.5-pro` | | 模型名称 |

### 基础设施

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `REDIS_URL` | `redis://:deepresearch@127.0.0.1:6379/0` | Redis 连接地址 |
| `UPLOAD_DIR` | `./uploads` | PPTX 文件输出目录 |

---

## 📝 API 接口

### 认证

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 | ❌ |
| POST | `/api/v1/auth/login` | 用户登录 | ❌ |
| GET | `/api/v1/auth/me` | 获取当前用户 | ✅ |
| PUT | `/api/v1/auth/me` | 更新用户信息 | ✅ |

### PPT 生成

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/ppt/plan` | 提交需求，获取方案 | 可选 |
| POST | `/api/v1/ppt/update-plan` | 编辑方案 | 可选 |
| POST | `/api/v1/ppt/confirm-plan` | 确认方案，生成HTML | 可选 |
| POST | `/api/v1/ppt/confirm-plan/stream` | 流式生成HTML | 可选 |
| POST | `/api/v1/ppt/edit` | 保存编辑 | 可选 |
| POST | `/api/v1/ppt/export` | 导出PPTX | 可选 |
| GET | `/api/v1/ppt/download/{plan_id}` | 下载文件 | 可选 |
| GET | `/api/v1/ppt/plan/{plan_id}` | 获取方案 | 可选 |

### 模板

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/templates` | 模板列表 | ❌ |
| GET | `/api/v1/templates/categories` | 分类列表 | ❌ |
| GET | `/api/v1/templates/{id}` | 模板详情 | ❌ |
| POST | `/api/v1/templates` | 创建模板 | ✅ |

### 仪表盘

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/dashboard/stats` | 统计数据 | ✅ |
| GET | `/api/v1/dashboard/recent` | 最近方案 | ✅ |
| GET | `/api/v1/dashboard/plans` | 方案列表 | ✅ |
| DELETE | `/api/v1/dashboard/plans/{plan_id}` | 删除方案 | ✅ |
| PUT | `/api/v1/dashboard/plans/{plan_id}/title` | 重命名方案 | ✅ |
| POST | `/api/v1/dashboard/plans/{plan_id}/duplicate` | 复制方案 | ✅ |

### DOCX 文档生成

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/docx/plan` | 提交需求，获取文档方案 | 可选 |
| POST | `/api/v1/docx/confirm` | 确认方案，生成内容 | 可选 |
| POST | `/api/v1/docx/confirm/stream` | 流式生成内容 | 可选 |
| POST | `/api/v1/docx/edit` | 保存编辑 | 可选 |
| POST | `/api/v1/docx/export` | 导出DOCX | 可选 |
| GET | `/api/v1/docx/download/{plan_id}` | 下载文件 | 可选 |
| GET | `/api/v1/docx/html/{plan_id}` | 获取HTML预览 | 可选 |
| GET | `/api/v1/docx/plan/{plan_id}` | 获取方案 | 可选 |

---

## 🏗️ 数据存储架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend   │────▶│   Backend   │────▶│   Redis     │
│  (Vue 3)     │◀────│  (FastAPI)  │◀────│  (缓存层)   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ PostgreSQL  │
                    │ (持久化层)  │
                    └─────────────┘
```

- **Redis**：方案快速缓存，24小时 TTL
- **PostgreSQL**：用户、方案、模板持久化存储
- **双写策略**：写入 Redis 同步，写入 PostgreSQL 异步
- **读取策略**：Redis 优先，缓存未命中时回退到 PostgreSQL

---

## 📄 License

[MIT](LICENSE)
