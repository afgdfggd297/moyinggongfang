# 墨印工坊 · InkPress Studio

AI 驱动的演示文稿生成工具。输入文字，AI 自动规划方案、联网搜索资料、生成精美的 HTML 幻灯片，支持可视化编辑和一键导出 PPTX。

## ✨ 功能特性

- **智能规划** — 输入主题内容，AI 自动分析并生成结构化的演示方案
- **联网搜索** — 自动 Bing 搜索相关资料，提升内容深度
- **可视化编辑** — 所见即所得的 iframe 预览，支持直接点击修改文字
- **一键导出** — HTML 幻灯片逐页截图，合并为 PPTX 文件
- **水粉首页** — MiMo 风格水墨画揭示效果
- **深色/浅色模式** — 一键切换，自动记忆偏好
- **对话历史** — 本地存储最近 20 条方案记录

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Pinia + Vue Router + Vite |
| 后端 | FastAPI + LangGraph + LangChain |
| LLM | MiMo V2.5（可配置任意 OpenAI 兼容 API） |
| 缓存 | Redis |
| 导出 | html2ppt（逐页截图）+ python-pptx（合并） |
| 浏览器 | Playwright（Chromium） |

## 📁 项目结构

```
lianshou/
├── docker-compose.yml          # Docker 编排
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── run.py                  # 启动入口
│   ├── app/
│   │   ├── main.py             # FastAPI 应用
│   │   ├── core/
│   │   │   ├── config.py       # 统一配置（Settings）
│   │   │   └── langgraph/      # 工作流图 + 节点
│   │   ├── api/v1/ppt.py       # API 路由
│   │   ├── schemas/ppt.py      # Pydantic 模型
│   │   ├── prompts/            # LLM 提示词
│   │   └── services/
│   │       ├── llm_service.py  # LLM 调用
│   │       ├── ppt_export.py   # PPTX 导出
│   │       ├── search_service.py # Bing 搜索
│   │       ├── web_fetch.py    # 网页抓取 + AI 摘要
│   │       └── redis_store.py  # Redis 存储
│   └── .env.example
└── frontend/
    ├── Dockerfile
    ├── nginx.conf              # 生产环境 Nginx 配置
    ├── package.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── main.ts
        ├── App.vue
        ├── router/index.ts
        ├── stores/ppt.ts       # Pinia 状态管理
        ├── composables/        # useTheme, useHistory
        ├── types/ppt.ts
        ├── views/
        │   ├── Home.vue        # 首页（水粉效果）
        │   └── Create.vue      # 创作工作台
        └── components/
            ├── StepInput.vue   # 01 输入
            ├── StepPlan.vue    # 02 方案
            ├── StepPreview.vue # 03 预览
            ├── StepDownload.vue# 04 下载
            └── ChatHistory.vue # 左侧历史栏
```

## 🚀 快速开始

### 开发环境

**后端：**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
playwright install chromium

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 MIMO_API_KEY

python run.py
# 启动于 http://127.0.0.1:8000
```

**前端：**

```bash
cd frontend
npm install
npm run dev
# 启动于 http://localhost:5173
```

### Docker 部署

```bash
# 构建并启动
docker compose up -d --build

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

服务访问：`http://localhost`（前端） / `http://localhost:8000`（后端 API）

## ⚙️ 配置说明

所有配置项通过环境变量或 `.env` 文件管理，详见 `backend/.env.example`。

### LLM 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MIMO_API_KEY` | — | API 密钥（必填） |
| `MIMO_BASE_URL` | `https://token-plan-cn.xiaomimimo.com/v1` | API 地址 |
| `MIMO_LLM_MODEL` | `mimo-v2.5-pro` | 模型名称 |
| `LLM_PLAN_TEMPERATURE` | `0.8` | 方案规划温度 |
| `LLM_HTML_TEMPERATURE` | `0.9` | HTML 生成温度 |

### PPT 导出

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PPT_SLIDE_W` | `13.333` | 幻灯片宽度（英寸） |
| `PPT_SLIDE_H` | `7.5` | 幻灯片高度（英寸） |
| `PPT_PX_W` | `1280` | 截图像素宽度 |
| `PPT_PX_H` | `720` | 截图像素高度 |
| `PPT_SCALE` | `2` | html2ppt 缩放倍数 |
| `PPT_BG_COLOR` | `#ffffff` | 幻灯片背景色 |

### 搜索与 WebFetch

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SEARCH_ENGINE_URL` | `https://cn.bing.com/search` | 搜索引擎 |
| `WEBFETCH_CACHE_MAXSIZE` | `100` | 缓存条数 |
| `WEBFETCH_CACHE_TTL` | `900` | 缓存过期（秒） |

## 📝 工作流程

```
用户输入文本
    ↓
[plan_node] LLM 分析生成方案（标题 + 层级大纲）
    ↓
[用户确认] 选择风格/配色/字体/密度等
    ↓
[html_generate_node] LLM 生成 HTML 幻灯片
    ↓
[预览编辑] iframe 渲染 + contentEditable 修改
    ↓
[导出] html2ppt 逐页截图 → python-pptx 合并 → PPTX
```

## 📄 License

MIT
