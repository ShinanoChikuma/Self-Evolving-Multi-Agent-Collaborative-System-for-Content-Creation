# EcRoom — 自进化多智能体内容创作系统

基于 CrewAI 的多 Agent 协作内容生成系统，支持记忆学习与自进化。

## 架构

```
用户输入 → Planner → Writer → Critic → Editor → 终稿
                ↑         ↑        ↑        ↑
            ┌──────────────────────────────────┐
            │  RAG 检索  │  记忆系统  │  知识库  │
            └──────────────────────────────────┘
                              ↓
                       Evolution Agent（离线分析反馈，优化 Prompt）
```

**流水线：**
- **Planner**（temperature 0.4）— 需求拆解为结构化创作计划，检索历史案例和用户偏好
- **Writer**（temperature 0.85）— 按大纲生成初稿
- **Critic** — 四维度审稿（需求符合度 / 结构完整度 / 文风统一性 / 事实风险）
- **Editor** — 根据审稿意见精准改写，交付终稿

**辅助系统：**
- **Memory** — 从高分反馈中学习用户偏好（语气、内容类型、受众），注入 Planner 上下文
- **RAG** — ChromaDB + 本地嵌入模型，检索历史高分案例作为创作参考
- **Evolution** — 离线分析反馈趋势，自动优化各 Agent 的 system prompt 和工作流配置

## 技术栈

| 层 | 技术 |
|---|---|
| 编排框架 | CrewAI（Sequential Process） |
| LLM | DeepSeek API（flash / pro 双模式） |
| RAG | ChromaDB + sentence-transformers |
| 后端 | Python HTTP Server（标准库，零依赖） |
| 前端 | 原生 HTML/CSS/JS，无框架 |
| 配置 | YAML 驱动 Agent 角色与 Task 定义 |
| 存储 | 本地 JSON 文件（runs / feedback / memory / templates） |

## 关键设计

- **Agent 与 LLM 解耦**：每个 Agent 使用独立的 API Key 和 model 实例，支持不同 Agent 走不同模型
- **配置即代码**：`config/agents.yaml` 和 `config/tasks.yaml` 驱动整个流水线，改配置无需改 Python
- **双模式**：快速模式（flash）和专家模式（pro），前端可切换
- **自进化闭环**：用户反馈 → Evolution Agent 分析 → 自动更新 agents.yaml → 重建 Agent 实例，无需重启
- **迭代修改**：支持对已有稿件发起多轮修改，保留修改链追溯

## 目录

```text
config/          YAML 配置（Agent 角色 / Task 流程）
src/agents/      Agent 实现（Planner/Writer/Critic/Editor/Evolution/Memory）
src/crew/        CrewAI 编排器 + 自定义 Tool（RAG/KB/Memory/WebSearch/YouTube/GitHub）
src/llm/         DeepSeek API 客户端
src/rag/         嵌入模型 + ChromaDB 检索器
src/db.py        本地 JSON 数据库
src/server.py    HTTP API 服务
static/          前端 SPA
data/            运行时数据目录
```

## 启动

```bash
cp .env.example .env   # 编辑填入 DeepSeek API Key
pip install -r requirements.txt
python app.py           # 默认 http://127.0.0.1:8010
```
