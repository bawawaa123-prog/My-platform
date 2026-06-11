# 企业智能工单与知识库 Multi-Agent 平台：完整实施方案

## 0. 项目定位

项目名称建议：

**Enterprise Support Agent / 企业智能工单与知识库 Multi-Agent 平台**

项目目标：

构建一个面向企业客服、IT 支持、售后支持、HR 内部服务台等场景的智能工单处理系统。系统不仅支持传统工单创建、分类、流转和审核，还要引入企业知识库 RAG、LangGraph Multi-Agent 工作流、Human-in-the-loop 人工审核机制，以及 FastMCP 工具开放层，使其成为一个可以写入简历、可以演示、可以面试深入讲解的 AI 应用工程项目。

最终技术标签：

```text
Python
FastAPI
SQLAlchemy
SQLite / PostgreSQL
Chroma / pgvector
RAG
LLM
LangGraph
Multi-Agent
FastMCP
MCP Tools / Resources / Prompts
Human-in-the-loop
React
TypeScript
Docker
JWT
Audit Trail
Analytics Dashboard
```

项目最终一句话描述：

> 基于 FastAPI + RAG + LangGraph Multi-Agent + FastMCP 的企业智能工单处理平台，支持工单自动分诊、企业知识库检索、历史相似工单推荐、AI 回复草稿生成、风险审核、人工审批、数据看板，以及通过 MCP 协议向外部 AI 客户端开放企业工具能力。

---

## 1. 项目核心价值

本项目不是普通 AI 聊天机器人，而是企业业务系统 + AI Agent 自动化流程。

它要体现以下能力：

1. 企业业务建模能力：用户、角色、工单、知识库、审核、日志、数据看板。
2. Python 后端工程能力：FastAPI 分层架构、数据库模型、接口设计、认证鉴权。
3. RAG 能力：文档上传、解析、切分、向量化、检索、引用来源。
4. LLM 应用能力：结构化输出、回复生成、Mock/真实 LLM 客户端隔离。
5. LangGraph 能力：有状态 Agent 工作流、节点编排、人工中断与恢复。
6. Multi-Agent 能力：Supervisor + 专业 Agent 分工协作。
7. FastMCP 能力：将企业工单、知识库、Agent 流程暴露为 MCP tools/resources/prompts。
8. 企业安全意识：AI 不直接发送回复，必须人工审核；高风险 MCP 工具默认 dry_run；关键操作写审计日志。
9. 可展示能力：前端页面、Agent 执行时间线、AI 建议、审核、数据看板。
10. 可交付能力：Docker 一键启动、README、测试账号、演示数据、简历描述。

---

## 2. 最终系统架构

```text
React + TypeScript 前端
    |
    | HTTP JSON API
    v
FastAPI 后端
    |
    +-- Auth / User / Role
    +-- Ticket API
    +-- Knowledge API
    +-- AI API
    +-- Review API
    +-- Analytics API
    |
    v
业务服务层 services/
    |
    +-- TicketService
    +-- KnowledgeService
    +-- DocumentParser
    +-- EmbeddingService
    +-- VectorStoreService
    +-- RagService
    +-- LLMService
    +-- ReviewService
    +-- AnalyticsService
    |
    v
LangGraph Multi-Agent 工作流
    |
    +-- SupervisorAgent
    +-- TriageAgent
    +-- KnowledgeAgent
    +-- SimilarCaseAgent
    +-- ReplyAgent
    +-- RiskAgent
    +-- WorkflowAgent
    |
    v
数据层
    |
    +-- SQLite / PostgreSQL
    +-- Chroma / pgvector
    +-- Redis 可选
    |
    v
外部模型服务
    |
    +-- OpenAI-compatible LLM
    +-- Mock LLM for local development
```

旁路开放层：

```text
外部 MCP Client / Claude Desktop / Cursor / 自研 AI Client
    |
    v
FastMCP Server
    |
    +-- search_knowledge_base
    +-- get_ticket_detail
    +-- list_open_tickets
    +-- search_similar_tickets
    +-- run_multi_agent_ticket_process
    +-- get_agent_audit_trail
    +-- get_analytics_overview
    |
    v
复用同一套 services 和 LangGraph workflow
```

关键原则：

- FastAPI 面向前端和普通 HTTP API。
- FastMCP 面向外部 AI 客户端。
- LangGraph 负责内部 Agent 工作流。
- Multi-Agent 不直接写复杂数据库逻辑，必须调用 services。
- 所有业务逻辑尽量沉淀在 services，API、MCP、LangGraph 都复用 services。

---

## 3. 推荐最终目录结构

```text
enterprise-support-agent/
├── AGENTS.md
├── PROJECT_IMPLEMENTATION_PLAN.md
├── README.md
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── PROJECT_HANDOFF.md
│   ├── API_DESIGN.md
│   ├── ARCHITECTURE.md
│   └── DEMO_SCRIPT.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── tickets.py
│   │   │   ├── knowledge.py
│   │   │   ├── ai.py
│   │   │   ├── reviews.py
│   │   │   └── analytics.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── permissions.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── init_db.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── ticket.py
│   │   │   ├── ticket_message.py
│   │   │   ├── knowledge_doc.py
│   │   │   ├── knowledge_chunk.py
│   │   │   ├── ai_suggestion.py
│   │   │   ├── audit_log.py
│   │   │   ├── ticket_embedding.py
│   │   │   └── agent_run_log.py
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   ├── auth.py
│   │   │   ├── ticket.py
│   │   │   ├── knowledge.py
│   │   │   ├── ai.py
│   │   │   ├── review.py
│   │   │   ├── analytics.py
│   │   │   └── agent.py
│   │   ├── repositories/
│   │   │   ├── user_repository.py
│   │   │   ├── ticket_repository.py
│   │   │   ├── knowledge_repository.py
│   │   │   ├── suggestion_repository.py
│   │   │   └── agent_run_repository.py
│   │   ├── services/
│   │   │   ├── user_service.py
│   │   │   ├── ticket_service.py
│   │   │   ├── knowledge_service.py
│   │   │   ├── document_parser.py
│   │   │   ├── chunking_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── vector_store_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── review_service.py
│   │   │   ├── analytics_service.py
│   │   │   └── audit_service.py
│   │   ├── agents/
│   │   │   ├── base_agent.py
│   │   │   ├── supervisor_agent.py
│   │   │   ├── triage_agent.py
│   │   │   ├── knowledge_agent.py
│   │   │   ├── similar_case_agent.py
│   │   │   ├── reply_agent.py
│   │   │   ├── risk_agent.py
│   │   │   └── workflow_agent.py
│   │   ├── graphs/
│   │   │   ├── ticket_agent_state.py
│   │   │   ├── ticket_agent_graph.py
│   │   │   ├── ticket_multi_agent_state.py
│   │   │   ├── ticket_multi_agent_graph.py
│   │   │   └── nodes/
│   │   │       ├── load_ticket_node.py
│   │   │       ├── supervisor_node.py
│   │   │       ├── triage_node.py
│   │   │       ├── knowledge_node.py
│   │   │       ├── similar_case_node.py
│   │   │       ├── reply_node.py
│   │   │       ├── risk_node.py
│   │   │       ├── workflow_node.py
│   │   │       ├── human_review_node.py
│   │   │       └── finalize_node.py
│   │   ├── mcp/
│   │   │   ├── server.py
│   │   │   ├── resources.py
│   │   │   ├── prompts.py
│   │   │   └── tools/
│   │   │       ├── ticket_tools.py
│   │   │       ├── knowledge_tools.py
│   │   │       ├── agent_tools.py
│   │   │       └── analytics_tools.py
│   │   ├── prompts/
│   │   │   ├── classify_ticket.txt
│   │   │   ├── generate_reply.txt
│   │   │   ├── risk_review.txt
│   │   │   ├── supervisor.txt
│   │   │   └── summarize_ticket.txt
│   │   └── workers/
│   │       └── embedding_worker.py
│   ├── scripts/
│   │   ├── seed_data.py
│   │   └── test_mcp_client.py
│   ├── uploads/
│   │   └── knowledge/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── src/
    │   ├── api/
    │   ├── components/
    │   ├── pages/
    │   ├── routes/
    │   ├── stores/
    │   └── types/
    ├── package.json
    └── Dockerfile
```

---

## 4. 数据模型规划

### 4.1 users

```text
id
email
username
hashed_password
role: admin | agent | viewer
is_active
created_at
updated_at
```

### 4.2 tickets

```text
id
title
content
customer_name
customer_email
category
priority
sentiment
status
assigned_to
source
created_by
ai_summary
recommended_department
created_at
updated_at
closed_at
```

推荐枚举：

```text
category:
- payment
- account
- product
- refund
- invoice
- technical
- hr
- it
- other

priority:
- low
- medium
- high
- urgent

sentiment:
- positive
- neutral
- negative
- angry

status:
- open
- ai_processing
- waiting_review
- in_progress
- resolved
- closed
```

### 4.3 ticket_messages

```text
id
ticket_id
sender_type: customer | agent | ai | system
sender_name
content
created_at
```

### 4.4 knowledge_docs

```text
id
title
file_name
file_type
file_path
content
doc_type
status: uploaded | processing | ready | failed
uploaded_by
error_message
created_at
updated_at
```

### 4.5 knowledge_chunks

```text
id
doc_id
chunk_index
content
metadata_json
embedding_id
created_at
```

### 4.6 ai_suggestions

```text
id
ticket_id
suggestion_type: classification | reply | workflow | risk
suggested_content
reasoning_summary
sources_json
confidence
status: draft | approved | edited | rejected
created_at
reviewed_by
reviewed_at
final_content
reject_reason
```

### 4.7 ticket_embeddings

```text
id
ticket_id
embedding_id
content_hash
created_at
```

### 4.8 audit_logs

```text
id
user_id
action
target_type
target_id
detail_json
created_at
```

### 4.9 agent_run_logs

```text
id
ticket_id
run_type: single_agent | multi_agent
status: running | interrupted | completed | failed
input_json
output_json
audit_trail_json
error_message
created_by
created_at
updated_at
```

---

## 5. API 规划

### 5.1 Auth

```http
POST /api/auth/login
GET  /api/auth/me
```

### 5.2 Tickets

```http
POST   /api/tickets
GET    /api/tickets
GET    /api/tickets/{ticket_id}
PATCH  /api/tickets/{ticket_id}
POST   /api/tickets/{ticket_id}/assign
POST   /api/tickets/{ticket_id}/close
GET    /api/tickets/{ticket_id}/messages
POST   /api/tickets/{ticket_id}/messages
GET    /api/tickets/{ticket_id}/similar
```

### 5.3 Knowledge

```http
POST   /api/knowledge/upload
GET    /api/knowledge/docs
GET    /api/knowledge/docs/{doc_id}
DELETE /api/knowledge/docs/{doc_id}
GET    /api/knowledge/docs/{doc_id}/chunks
POST   /api/knowledge/search
```

### 5.4 AI

```http
POST /api/ai/tickets/{ticket_id}/classify
POST /api/ai/tickets/{ticket_id}/generate-reply
POST /api/ai/tickets/{ticket_id}/process
POST /api/ai/tickets/{ticket_id}/process/start
POST /api/ai/tickets/{ticket_id}/process/resume
POST /api/ai/tickets/{ticket_id}/multi-agent-process/start
POST /api/ai/tickets/{ticket_id}/multi-agent-process/resume
GET  /api/ai/tickets/{ticket_id}/suggestions
GET  /api/ai/tickets/{ticket_id}/agent-runs
GET  /api/ai/agent-runs/{run_id}
```

### 5.5 Reviews

```http
POST /api/reviews/{suggestion_id}/approve
POST /api/reviews/{suggestion_id}/edit
POST /api/reviews/{suggestion_id}/reject
```

### 5.6 Analytics

```http
GET /api/analytics/overview
GET /api/analytics/ticket-trends
GET /api/analytics/category-distribution
GET /api/analytics/priority-distribution
GET /api/analytics/ai-performance
```

---

## 6. FastMCP 能力规划

### 6.1 Tools

第一批只读工具：

```text
search_knowledge_base(query: str, top_k: int = 5)
get_ticket_detail(ticket_id: int)
list_open_tickets(limit: int = 20)
search_similar_tickets(ticket_id: int, top_k: int = 5)
get_analytics_overview()
```

第二批 Agent 工具：

```text
run_multi_agent_ticket_process(ticket_id: int, dry_run: bool = True)
get_agent_audit_trail(ticket_id: int)
```

安全原则：

- 所有 MCP 写操作默认 `dry_run=True`。
- `dry_run=False` 时必须写 audit_log。
- 不暴露删除数据、直接关闭工单、直接发送客户回复等高风险工具。
- AI 只能生成建议，最终必须走人工审核。

### 6.2 Resources

```text
ticket://{ticket_id}
knowledge-doc://{doc_id}
analytics://overview
```

### 6.3 Prompts

```text
classify_ticket_prompt
generate_reply_prompt
summarize_ticket_prompt
risk_review_prompt
```

### 6.4 Client 测试脚本

```text
backend/scripts/test_mcp_client.py
```

用于：

```text
list_tools
call_tool("search_knowledge_base")
call_tool("get_ticket_detail")
call_tool("run_multi_agent_ticket_process")
```

---

## 7. LangGraph 与 Multi-Agent 规划

### 7.1 单 Agent 工作流

先实现固定流程：

```text
START
  -> load_ticket
  -> classify_ticket
  -> retrieve_knowledge
  -> search_similar_tickets
  -> generate_reply
  -> risk_check
  -> finalize
  -> END
```

然后增加 Human-in-the-loop：

```text
generate_reply
  -> human_review_interrupt
  -> finalize
```

### 7.2 Multi-Agent 工作流

最终流程：

```text
START
  -> load_ticket
  -> supervisor
  -> triage_agent
  -> knowledge_agent
  -> similar_case_agent
  -> reply_agent
  -> risk_agent
  -> workflow_agent
  -> human_review_interrupt
  -> finalize
  -> END
```

第一版 Multi-Agent 可先不做动态路由，而是顺序执行，稳定后再做 supervisor 条件分支。

### 7.3 Agent 职责

#### SupervisorAgent

- 汇总状态。
- 决定当前工单需要哪些 Agent。
- 第一版只做流程汇总和记录，不做复杂自由调度。

#### TriageAgent

- 分类。
- 优先级。
- 情绪。
- 是否需要人工。
- 推荐部门。
- 摘要。

#### KnowledgeAgent

- 生成检索 query。
- 调用 RAG 检索企业知识库。
- 返回来源。

#### SimilarCaseAgent

- 搜索历史相似工单。
- 总结历史处理方案。

#### ReplyAgent

- 综合工单、知识库、历史案例。
- 生成客服回复草稿。
- 生成内部处理建议。
- 标注引用来源和置信度。

#### RiskAgent

- 识别退款、赔付、隐私、法律、权限、低置信度等风险。
- 决定是否必须人工审核。

#### WorkflowAgent

- 推荐下一步状态。
- 推荐派单部门。
- 推荐下一步动作。

### 7.4 audit_trail

每个 Agent 执行后追加：

```json
{
  "agent_name": "KnowledgeAgent",
  "action": "search_knowledge_base",
  "input_summary": "...",
  "output_summary": "...",
  "status": "success",
  "timestamp": "..."
}
```

---

# 8. 从 0 到 1 实施步骤

下面步骤必须按顺序执行。每一步都应独立可验证，每一步完成后必须更新交接文档 `docs/PROJECT_HANDOFF.md`。

---

## Step 00：创建项目根目录与基础文档

### 目标

创建项目根目录，放入项目计划、Codex 约束、README 草稿和 docs 目录，为后续所有步骤建立统一上下文。

### 要完成的功能

- 创建 `enterprise-support-agent/`。
- 创建 `PROJECT_IMPLEMENTATION_PLAN.md`。
- 创建 `AGENTS.md`。
- 创建 `README.md` 初稿。
- 创建 `docs/PROJECT_HANDOFF.md` 初稿。
- 创建 `.gitignore`。
- 创建 `.env.example`。

### 验收标准

- 项目根目录结构清晰。
- README 能说明项目是什么。
- PROJECT_HANDOFF.md 能记录当前步骤、已完成内容、下一步任务。
- `.gitignore` 包含 Python、Node、env、uploads、database、cache 等常见忽略项。
- 不包含任何真实 API Key。

### 建议验证

```bash
ls
cat README.md
cat docs/PROJECT_HANDOFF.md
```

---

## Step 01：初始化 FastAPI 后端最小服务

### 目标

建立可运行的 FastAPI 后端。

### 要完成的功能

- 创建 `backend/`。
- 创建 `backend/app/main.py`。
- 创建 `backend/requirements.txt`。
- 提供 `GET /health`。
- 支持本地启动。
- 添加基础 CORS 配置。

### 验收标准

- 执行后端启动命令可以启动服务。
- 访问 `/health` 返回：

```json
{"status": "ok"}
```

### 建议验证

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
curl http://localhost:8000/health
```

---

## Step 02：初始化 React + TypeScript 前端

### 目标

建立可运行的前端项目。

### 要完成的功能

- 创建 `frontend/`。
- 使用 React + TypeScript + Vite。
- 首页显示 `Enterprise Support Agent`。
- 添加基础路由结构。
- 添加 API client 文件夹。

### 验收标准

- 前端能启动。
- 浏览器能看到项目标题。
- 前端目录结构清晰。

### 建议验证

```bash
cd frontend
npm install
npm run dev
```

---

## Step 03：后端分层架构与配置系统

### 目标

搭建后端基础工程结构，避免后续代码堆在 main.py。

### 要完成的功能

- 创建 `app/api/`。
- 创建 `app/core/config.py`。
- 创建 `app/db/session.py`。
- 创建 `app/db/base.py`。
- 创建 `app/models/`、`app/schemas/`、`app/services/`、`app/repositories/`。
- 使用 SQLite 作为第一版默认数据库。
- 配置环境变量读取。

### 验收标准

- `main.py` 只负责创建 app 和注册路由。
- 数据库连接模块可导入。
- 配置从 `.env` 或默认值读取。
- `/health` 不受影响。

### 建议验证

```bash
cd backend
uvicorn app.main:app --reload
curl http://localhost:8000/health
```

---

## Step 04：数据库初始化与基础 Base Model

### 目标

让 SQLAlchemy 模型可以创建数据库表。

### 要完成的功能

- 创建通用 Base。
- 创建数据库初始化函数。
- 暂时使用 `Base.metadata.create_all()`，后期再引入 Alembic。
- 添加 `created_at`、`updated_at` 通用字段工具。
- 创建 `scripts/init_db.py` 或 `app/db/init_db.py`。

### 验收标准

- 启动时或执行脚本能创建 `app.db`。
- 没有业务表时也不报错。
- 数据库初始化逻辑独立于 API 逻辑。

### 建议验证

```bash
cd backend
python -m app.db.init_db
ls app.db
```

---

## Step 05：用户模型、密码哈希与 JWT 登录

### 目标

实现最小可用认证系统。

### 要完成的功能

- 创建 `User` 模型。
- 创建 auth schemas。
- 实现密码哈希。
- 实现 JWT 创建与解析。
- 提供接口：
  - `POST /api/auth/login`
  - `GET /api/auth/me`
- 初始化测试账号：
  - `admin@example.com / admin123`
  - `agent@example.com / agent123`
  - `viewer@example.com / viewer123`

### 验收标准

- 可以登录获得 token。
- 带 token 调用 `/api/auth/me` 能返回当前用户。
- 未登录访问受保护接口返回 401。
- 密码不能明文存储。

### 建议验证

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

---

## Step 06：工单基础模型与 CRUD

### 目标

实现企业工单系统的核心基础能力。

### 要完成的功能

- 创建 `Ticket` 模型。
- 创建 ticket schemas。
- 创建 ticket repository/service。
- 创建接口：
  - `POST /api/tickets`
  - `GET /api/tickets`
  - `GET /api/tickets/{ticket_id}`
  - `PATCH /api/tickets/{ticket_id}`
- 所有接口需要登录。

### 验收标准

- 登录用户可以创建工单。
- 可以查看工单列表。
- 可以查看工单详情。
- 可以修改状态、分类、优先级等字段。
- created_by 能记录创建者。

### 建议验证

```bash
curl -X POST http://localhost:8000/api/tickets \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"付款后订单未更新","content":"客户已付款但订单状态仍显示未支付","customer_name":"张三","customer_email":"test@example.com"}'
```

---

## Step 07：工单消息与审计日志基础

### 目标

为后续 AI 建议、人工审核、流程追踪做基础。

### 要完成的功能

- 创建 `TicketMessage` 模型。
- 创建 `AuditLog` 模型。
- 创建消息接口：
  - `GET /api/tickets/{ticket_id}/messages`
  - `POST /api/tickets/{ticket_id}/messages`
- 创建 `audit_service.py`。
- 工单创建、更新时写入 audit log。

### 验收标准

- 每个工单可以添加消息。
- 工单操作有审计日志。
- 审计日志中包含 user_id、action、target_type、target_id、detail_json。

### 建议验证

```bash
GET /api/tickets/{ticket_id}/messages
POST /api/tickets/{ticket_id}/messages
```

---

## Step 08：知识库文档上传：txt/md

### 目标

实现企业知识库的最小版本。

### 要完成的功能

- 创建 `KnowledgeDoc` 模型。
- 支持上传 `.txt` 和 `.md`。
- 文件保存到 `backend/uploads/knowledge/`。
- 解析文本内容保存到数据库。
- 提供接口：
  - `POST /api/knowledge/upload`
  - `GET /api/knowledge/docs`
  - `GET /api/knowledge/docs/{doc_id}`

### 验收标准

- 可以上传 txt/md 文档。
- 文档状态为 ready。
- 可以查看文档列表。
- 可以查看文档内容或摘要。
- 非 txt/md 文件被拒绝。

### 建议验证

```bash
curl -X POST http://localhost:8000/api/knowledge/upload \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@sample.md" \
  -F "title=支付处理 SOP"
```

---

## Step 09：文档切分 KnowledgeChunk

### 目标

把知识库文档切成可检索片段。

### 要完成的功能

- 创建 `KnowledgeChunk` 模型。
- 上传文档后自动切分。
- 默认 `chunk_size=800`，`overlap=100`。
- 保存 chunk。
- 提供接口：
  - `GET /api/knowledge/docs/{doc_id}/chunks`

### 验收标准

- 文档上传后生成多个 chunk。
- chunk_index 连续。
- chunk 内容长度合理。
- doc 详情返回 chunks_count。

### 建议验证

```bash
GET /api/knowledge/docs/{doc_id}/chunks
```

---

## Step 10：EmbeddingProvider 抽象与 Fake Embedding

### 目标

先不依赖真实 API Key，建立可替换的 embedding 架构。

### 要完成的功能

- 创建 `embedding_service.py`。
- 定义 `EmbeddingProvider` 接口。
- 实现 `FakeEmbeddingProvider`。
- Fake embedding 必须稳定：同一文本每次返回相同向量。
- 支持后续替换 OpenAI-compatible embedding。

### 验收标准

- 业务代码不直接依赖第三方 embedding SDK。
- Fake embedding 可用于本地测试。
- 单元或手动测试能生成向量。

### 建议验证

```bash
python -c "from app.services.embedding_service import get_embedding_provider; print(get_embedding_provider().embed_text('hello')[:5])"
```

---

## Step 11：向量存储与知识库搜索

### 目标

实现知识库语义检索。

### 要完成的功能

- 创建 `vector_store_service.py`。
- 第一版可以使用简单内存/本地 JSON/Chroma。
- 为 knowledge chunks 建立向量索引。
- 提供接口：
  - `POST /api/knowledge/search`
- 输入 query、top_k。
- 返回相关 chunks 和相似度。

### 验收标准

- 上传知识文档后能搜索。
- 搜索结果包含 doc_id、chunk_id、content_preview、score。
- 没有知识库时返回空列表，不崩溃。
- 代码结构后续可替换为 pgvector。

### 建议验证

```bash
curl -X POST http://localhost:8000/api/knowledge/search \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query":"订单支付后未更新怎么办","top_k":5}'
```

---

## Step 12：LLMService 抽象：Mock + OpenAI Compatible

### 目标

统一封装 LLM 调用，避免业务代码直接依赖第三方 SDK。

### 要完成的功能

- 创建 `llm_service.py`。
- 定义 `LLMClient` 接口：
  - `generate_text`
  - `generate_json`
- 实现 `MockLLMClient`。
- 预留 `OpenAICompatibleLLMClient`。
- 配置项：
  - `LLM_PROVIDER`
  - `LLM_API_KEY`
  - `LLM_BASE_URL`
  - `LLM_MODEL`

### 验收标准

- 没有 API Key 时使用 Mock，不影响开发。
- 业务代码只调用 LLMService。
- generate_json 失败时有清晰异常处理。
- 不在代码中硬编码 API Key。

### 建议验证

```bash
python -c "from app.services.llm_service import get_llm_client; print(get_llm_client().generate_text('hello'))"
```

---

## Step 13：AI 工单分类

### 目标

实现 LLM 结构化输出，把新工单自动分诊。

### 要完成的功能

- 创建 prompt：`prompts/classify_ticket.txt`。
- 创建 `TicketClassification` schema：
  - category
  - priority
  - sentiment
  - need_human
  - summary
  - recommended_department
- 实现接口：
  - `POST /api/ai/tickets/{ticket_id}/classify`
- 将分类结果写回 ticket。

### 验收标准

- 调用接口后，ticket 有 category、priority、sentiment、ai_summary、recommended_department。
- LLM 返回异常时不导致服务崩溃。
- Mock LLM 下也能返回可演示数据。
- 分类结果使用枚举约束或校验。

### 建议验证

```bash
POST /api/ai/tickets/{ticket_id}/classify
GET  /api/tickets/{ticket_id}
```

---

## Step 14：RAG 回复草稿生成与 AISuggestion

### 目标

基于知识库检索结果生成 AI 回复草稿。

### 要完成的功能

- 创建 `AISuggestion` 模型。
- 创建 `rag_service.py`：
  - `retrieve_context(query, top_k)`
  - `build_answer_prompt(ticket, chunks)`
  - `generate_ticket_reply(ticket_id)`
- 创建 prompt：`prompts/generate_reply.txt`。
- 实现接口：
  - `POST /api/ai/tickets/{ticket_id}/generate-reply`
  - `GET /api/ai/tickets/{ticket_id}/suggestions`
- 保存 AI 建议。

### 验收标准

- 生成回复草稿。
- suggestion 写入数据库。
- 返回 sources 引用来源。
- 如果知识库没有命中，也要提示低置信度，而不是胡编。
- 不直接发送给客户。

### 建议验证

```bash
POST /api/ai/tickets/{ticket_id}/generate-reply
GET  /api/ai/tickets/{ticket_id}/suggestions
```

---

## Step 15：人工审核流程 Human-in-the-loop 基础版

### 目标

AI 建议必须经过人工审核。

### 要完成的功能

- AISuggestion 增加：
  - reviewed_by
  - reviewed_at
  - final_content
  - reject_reason
- 实现接口：
  - `POST /api/reviews/{suggestion_id}/approve`
  - `POST /api/reviews/{suggestion_id}/edit`
  - `POST /api/reviews/{suggestion_id}/reject`
- 审核行为写 audit log。

### 验收标准

- approve 后 status=approved，final_content=suggested_content。
- edit 后 status=edited，final_content 为人工修改内容。
- reject 后 status=rejected，并记录原因。
- 审核人和时间被记录。
- 未登录不能审核。

### 建议验证

```bash
POST /api/reviews/{suggestion_id}/approve
POST /api/reviews/{suggestion_id}/edit
POST /api/reviews/{suggestion_id}/reject
```

---

## Step 16：历史相似工单推荐

### 目标

复用企业历史处理经验。

### 要完成的功能

- 创建 `TicketEmbedding` 模型或向量存储记录。
- 工单创建或关闭时生成 embedding。
- 实现接口：
  - `GET /api/tickets/{ticket_id}/similar`
- 只返回 resolved/closed 历史工单。

### 验收标准

- 当前工单能查询相似历史工单。
- 返回 ticket_id、title、content_preview、similarity、resolution。
- 不返回当前工单本身。
- 无历史工单时返回空列表。

### 建议验证

```bash
GET /api/tickets/{ticket_id}/similar
```

---

## Step 17：LangGraph 单流程工作流

### 目标

把已有 AI 分类、知识检索、相似工单、回复生成串成可控工作流。

### 要完成的功能

- 添加 LangGraph 依赖。
- 创建：
  - `graphs/ticket_agent_state.py`
  - `graphs/ticket_agent_graph.py`
- 实现节点：
  - load_ticket
  - classify_ticket
  - retrieve_knowledge
  - search_similar_tickets
  - generate_reply
  - risk_check
  - finalize
- 修改：
  - `POST /api/ai/tickets/{ticket_id}/process`

### 验收标准

- 调用 process 后自动完成分类、检索、回复生成。
- 每个节点复用 services，不重复写业务逻辑。
- 工作流失败时返回清晰错误。
- 原有 classify 和 generate-reply 接口仍可用。

### 建议验证

```bash
POST /api/ai/tickets/{ticket_id}/process
```

---

## Step 18：LangGraph interrupt 人工审核

### 目标

让 Agent 生成草稿后暂停，等待人工审核后恢复。

### 要完成的功能

- 添加 human_review_node。
- 使用 LangGraph checkpointer。
- 实现接口：
  - `POST /api/ai/tickets/{ticket_id}/process/start`
  - `POST /api/ai/tickets/{ticket_id}/process/resume`
- start 遇到人工审核节点时返回 pending_review。
- resume 接收 approve/edit/reject。

### 验收标准

- start 能执行到草稿生成并暂停。
- 返回 draft_reply、sources、confidence。
- resume 后执行 finalize。
- 审核结果写入 suggestion 和 audit log。
- 流程状态可以通过 run_id/thread_id 恢复。

### 建议验证

```bash
POST /api/ai/tickets/{ticket_id}/process/start
POST /api/ai/tickets/{ticket_id}/process/resume
```

---

## Step 19：Multi-Agent 第一版：Supervisor/Triage/Knowledge/Reply/Risk

### 目标

把单流程拆成企业岗位分工式 Multi-Agent。

### 要完成的功能

- 创建 `app/agents/`。
- 创建：
  - supervisor_agent.py
  - triage_agent.py
  - knowledge_agent.py
  - reply_agent.py
  - risk_agent.py
- 创建：
  - `graphs/ticket_multi_agent_state.py`
  - `graphs/ticket_multi_agent_graph.py`
- 流程第一版：
  - START -> load_ticket -> supervisor -> triage -> knowledge -> reply -> risk -> human_review -> finalize -> END
- 新增接口：
  - `POST /api/ai/tickets/{ticket_id}/multi-agent-process/start`

### 验收标准

- Multi-Agent 流程可运行。
- 每个 Agent 职责单一。
- Agent 不直接写复杂数据库逻辑，必须调用 services。
- 原 LangGraph 单流程保留，不删除。
- 返回结果中包含每个 Agent 的输出。

### 建议验证

```bash
POST /api/ai/tickets/{ticket_id}/multi-agent-process/start
```

---

## Step 20：Multi-Agent audit_trail 与 AgentRunLog

### 目标

增强企业可解释性和可审计性。

### 要完成的功能

- 在 Multi-Agent state 加入 `audit_trail`。
- 每个 Agent 执行后追加 audit_trail。
- 创建 `AgentRunLog` 模型。
- 保存每次 multi-agent 运行记录。
- 提供接口：
  - `GET /api/ai/tickets/{ticket_id}/agent-runs`
  - `GET /api/ai/agent-runs/{run_id}`

### 验收标准

- 每次 Multi-Agent 执行都有 run log。
- audit_trail 包含 agent_name、action、input_summary、output_summary、status、timestamp。
- 前端后续可展示。
- 不影响已有 AI 流程。

### 建议验证

```bash
GET /api/ai/tickets/{ticket_id}/agent-runs
GET /api/ai/agent-runs/{run_id}
```

---

## Step 21：增加 SimilarCaseAgent

### 目标

让 Multi-Agent 能使用历史工单经验。

### 要完成的功能

- 创建 `similar_case_agent.py`。
- 将图流程改为：
  - START -> load_ticket -> supervisor -> triage -> knowledge -> similar_case -> reply -> risk -> human_review -> finalize -> END
- ReplyAgent 生成回复时综合：
  - 工单内容
  - triage_result
  - knowledge_result
  - similar_case_result

### 验收标准

- Multi-Agent 输出中包含 similar_case_result。
- audit_trail 记录 SimilarCaseAgent。
- 无相似工单时流程仍能继续。
- ReplyAgent 能引用历史案例摘要。

### 建议验证

```bash
POST /api/ai/tickets/{ticket_id}/multi-agent-process/start
```

---

## Step 22：增加 WorkflowAgent

### 目标

让 Multi-Agent 给出流程流转建议。

### 要完成的功能

- 创建 `workflow_agent.py`。
- 图流程改为：
  - START -> load_ticket -> supervisor -> triage -> knowledge -> similar_case -> reply -> risk -> workflow -> human_review -> finalize -> END
- WorkflowAgent 输出：
  - next_status
  - assign_to_department
  - next_action
  - internal_note

### 验收标准

- Multi-Agent 输出中包含 workflow_result。
- 工单可进入 waiting_review。
- workflow_result 可被前端展示。
- audit_trail 记录 WorkflowAgent。

### 建议验证

```bash
POST /api/ai/tickets/{ticket_id}/multi-agent-process/start
```

---

## Step 23：FastMCP 只读工具服务

### 目标

学习并实现 FastMCP Server，将企业能力开放给外部 AI 客户端。

### 要完成的功能

- 添加 FastMCP 依赖。
- 创建 `app/mcp/server.py`。
- 创建 MCP tools：
  - search_knowledge_base
  - get_ticket_detail
  - list_open_tickets
  - search_similar_tickets
  - get_analytics_overview
- tools 复用 services。

### 验收标准

- `python -m app.mcp.server` 能启动 MCP server。
- tools 有清晰 docstring。
- tools 不重复写业务逻辑。
- 不暴露高风险写操作。
- README 增加 MCP 启动方式。

### 建议验证

```bash
cd backend
python -m app.mcp.server
```

---

## Step 24：FastMCP 调用 Multi-Agent 工作流

### 目标

让外部 MCP Client 能触发企业 Multi-Agent 分析。

### 要完成的功能

- 新增 MCP tool：
  - `run_multi_agent_ticket_process(ticket_id: int, dry_run: bool = True)`
- 新增 MCP tool：
  - `get_agent_audit_trail(ticket_id: int)`
- dry_run=True 不修改数据库。
- dry_run=False 可以创建 suggestion，并写 audit log。

### 验收标准

- MCP tool 能返回 triage、knowledge、similar_case、reply、risk、workflow、audit_trail。
- 默认 dry_run=True。
- dry_run=False 记录 audit log。
- 不直接发送客户回复。
- README 说明安全设计。

### 建议验证

```bash
python -m app.mcp.server
# 使用 MCP client 脚本调用
```

---

## Step 25：FastMCP Resources 与 Prompts

### 目标

完整学习 FastMCP 的 tools/resources/prompts。

### 要完成的功能

- 创建 `app/mcp/resources.py`。
- 创建 resources：
  - `ticket://{ticket_id}`
  - `knowledge-doc://{doc_id}`
  - `analytics://overview`
- 创建 `app/mcp/prompts.py`。
- 创建 prompts：
  - classify_ticket_prompt
  - generate_reply_prompt
  - summarize_ticket_prompt
  - risk_review_prompt
- server.py 注册 resources/prompts。

### 验收标准

- MCP server 可列出 tools/resources/prompts。
- resources 返回结构化数据。
- prompts 是可复用模板。
- README 说明 tool/resource/prompt 区别。

### 建议验证

```bash
python -m app.mcp.server
```

---

## Step 26：FastMCP Client 测试脚本

### 目标

证明项目不仅能写 MCP Server，还能调试 MCP Client。

### 要完成的功能

- 创建 `backend/scripts/test_mcp_client.py`。
- 连接本地 MCP server。
- 执行：
  - list_tools
  - call_tool("search_knowledge_base")
  - call_tool("get_ticket_detail")
  - call_tool("run_multi_agent_ticket_process")
- 输出易读结果。

### 验收标准

- 脚本可以运行。
- 能成功调用至少两个 MCP tools。
- README 有测试说明。
- 不依赖真实 API Key。

### 建议验证

```bash
python -m app.mcp.server
python scripts/test_mcp_client.py
```

---

## Step 27：前端登录与基础布局

### 目标

建立可演示的后台管理界面。

### 要完成的功能

- 登录页。
- Token 保存。
- Axios 请求拦截器。
- 基础 Layout。
- 左侧导航：
  - Dashboard
  - Tickets
  - Knowledge
- 受保护路由。

### 验收标准

- 可以登录。
- 登录后进入 Dashboard。
- 未登录访问业务页面会跳转登录页。
- 刷新页面后 token 仍生效。

### 建议验证

```bash
npm run dev
```

---

## Step 28：前端工单列表、创建、详情

### 目标

让工单 CRUD 在前端可用。

### 要完成的功能

- 工单列表页。
- 创建工单页。
- 工单详情页。
- 支持筛选状态、优先级、分类。
- 显示基本字段。

### 验收标准

- 前端可以创建工单。
- 可以查看列表和详情。
- 可以修改状态。
- UI 简洁可演示。

### 建议验证

- 浏览器手动创建工单。
- 查看工单详情。

---

## Step 29：前端知识库上传与搜索

### 目标

让 RAG 数据准备流程可视化。

### 要完成的功能

- 知识库文档列表页。
- 上传文档。
- 文档详情页。
- chunk 展示。
- 知识库搜索测试框。

### 验收标准

- 前端可上传 txt/md。
- 可看到文档状态和 chunks_count。
- 可输入 query 搜索知识库。
- 展示搜索结果和 score。

### 建议验证

- 上传支付 SOP 文档。
- 搜索“付款后订单未更新”。

---

## Step 30：前端 AI 建议与人工审核

### 目标

展示 AI 回复草稿和审核流程。

### 要完成的功能

- 工单详情页显示：
  - AI 分类结果
  - AI 回复草稿
  - sources
  - confidence
- 按钮：
  - AI 分类
  - 生成回复草稿
  - approve
  - edit
  - reject

### 验收标准

- 点击按钮能触发后端 AI 接口。
- sources 可展示。
- 审核后状态变化。
- 审核结果可回显。

### 建议验证

- 对一个工单生成回复草稿并 approve/edit/reject。

---

## Step 31：前端 Multi-Agent 执行过程展示

### 目标

把项目最核心亮点可视化。

### 要完成的功能

- 工单详情页新增 “AI Agent 执行过程”。
- 显示：
  - SupervisorAgent
  - TriageAgent
  - KnowledgeAgent
  - SimilarCaseAgent
  - ReplyAgent
  - RiskAgent
  - WorkflowAgent
- 显示 audit_trail 时间线。
- 按钮：
  - 运行 Multi-Agent 分析。

### 验收标准

- 可以从前端启动 Multi-Agent。
- 每个 Agent 输出能展示。
- audit_trail 显示 agent_name、action、output_summary、status、timestamp。
- 页面适合录屏演示。

### 建议验证

- 创建一个支付异常工单。
- 点击运行 Multi-Agent。
- 查看执行时间线和草稿。

---

## Step 32：数据看板 Analytics

### 目标

体现企业管理价值。

### 要完成的功能

后端：

- `GET /api/analytics/overview`
- 返回：
  - total_tickets
  - open_tickets
  - resolved_tickets
  - urgent_tickets
  - ai_suggestions_count
  - ai_approved_count
  - ai_adoption_rate
  - category_distribution
  - priority_distribution

前端：

- 指标卡片。
- 分类分布图。
- 优先级分布图。
- AI 采纳率。

### 验收标准

- Dashboard 有核心指标。
- 有至少两个图表。
- 无数据时不崩溃。
- 指标计算逻辑在 service 层。

### 建议验证

- 创建多条不同分类工单。
- 审核部分 AI 建议。
- 查看 Dashboard。

---

## Step 33：后台任务：文档处理异步化

### 目标

提升工程化程度，避免上传文档时阻塞。

### 要完成的功能

- 使用 FastAPI BackgroundTasks。
- 上传后文档状态：
  - uploaded
  - processing
  - ready
  - failed
- 后台任务解析、切分、embedding、索引。
- 前端显示状态。

### 验收标准

- 上传接口快速返回。
- 后台任务完成后状态变 ready。
- 失败时写 error_message。
- 不引入 Celery，保持第一版简单。

### 建议验证

- 上传文档后刷新列表观察状态变化。

---

## Step 34：种子数据与演示数据

### 目标

让项目可以快速演示。

### 要完成的功能

- 创建 `backend/scripts/seed_data.py`。
- 生成：
  - 测试用户
  - 支付 SOP 文档
  - 发票规则文档
  - 退款规则文档
  - 历史已解决工单
  - 当前待处理工单
- 支持重复执行不产生大量重复数据。

### 验收标准

- 执行脚本后项目有可演示数据。
- Multi-Agent 能基于这些数据产生合理结果。
- README 有 seed 命令。

### 建议验证

```bash
python scripts/seed_data.py
```

---

## Step 35：测试与质量检查

### 目标

让项目看起来更工程化。

### 要完成的功能

- 添加基础 pytest。
- 测试：
  - health
  - login
  - ticket CRUD
  - knowledge upload
  - AI mock classification
  - RAG search
- 前端可选添加基础 lint。

### 验收标准

- 后端测试可运行。
- 核心接口至少有 smoke tests。
- Mock LLM/Embedding 保证测试不依赖外部 API。

### 建议验证

```bash
cd backend
pytest
```

---

## Step 36：Docker Compose 一键启动

### 目标

实现完整部署闭环。

### 要完成的功能

- backend Dockerfile。
- frontend Dockerfile。
- docker-compose.yml。
- 包含：
  - backend
  - frontend
  - postgres 可选
  - redis 可选
- `.env.example` 完整。
- README 写清启动命令。

### 验收标准

- `docker-compose up --build` 能启动项目。
- 前端能访问后端。
- health 正常。
- 不需要真实 API Key 也能跑 mock 模式。

### 建议验证

```bash
docker-compose up --build
```

---

## Step 37：README、架构图、演示脚本、简历包装

### 目标

让项目成为可以投简历的作品。

### 要完成的功能

README 包含：

- 项目背景。
- 核心功能。
- 技术栈。
- 系统架构。
- RAG 流程。
- LangGraph Multi-Agent 流程。
- FastMCP 使用说明。
- Human-in-the-loop 设计。
- 数据模型说明。
- API 示例。
- 本地启动。
- Docker 启动。
- 测试账号。
- 演示流程。
- 简历描述。
- 未来优化方向。

docs 中增加：

- `ARCHITECTURE.md`
- `API_DESIGN.md`
- `DEMO_SCRIPT.md`

### 验收标准

- 新人只看 README 可以启动项目。
- 面试官可以快速理解项目价值。
- 有完整简历描述。
- 有演示脚本可按步骤展示项目。

---

# 9. 推荐开发节奏

如果时间有限，优先做到：

```text
最小可展示版本：
Step 00 - Step 15

简历可用版本：
Step 00 - Step 22 + Step 27 - Step 32

完整强竞争力版本：
Step 00 - Step 37
```

最核心的简历亮点必须保留：

1. 工单系统不是聊天机器人。
2. RAG 有引用来源。
3. AI 回复必须人工审核。
4. LangGraph 编排流程。
5. Multi-Agent 有明确角色分工。
6. audit_trail 可追踪每个 Agent 行为。
7. FastMCP 暴露企业工具能力。
8. Docker/README/seed data 保证可演示。

---

# 10. 每一步完成后的交接要求

每完成一步，必须更新 `docs/PROJECT_HANDOFF.md`，至少包括：

```text
当前完成到 Step XX
本步骤目标
本步骤完成内容
新增/修改文件列表
数据库模型变化
新增/修改 API
运行和验证命令
验证结果
已知问题
下一步应执行的 Step
下一步 Codex Prompt
```

这可以保证新会话能快速接手，不需要重新理解整个项目。

---

# 11. 最终简历描述模板

```text
企业智能工单与知识库 Multi-Agent 平台

项目描述：
设计并实现一个面向企业客服/IT 支持场景的智能工单处理平台，支持工单创建、企业知识库 RAG 检索、历史相似工单推荐、AI 回复草稿生成、人工审核、状态流转和数据看板。系统基于 LangGraph 构建 Supervisor 多 Agent 工作流，将工单分诊、知识检索、历史案例分析、回复生成、风险审核和流程建议拆分为多个专业 Agent 协作完成，并通过 FastMCP 将核心能力暴露为标准 MCP tools，支持外部 AI 客户端调用。

技术栈：
Python、FastAPI、SQLAlchemy、SQLite/PostgreSQL、Chroma/pgvector、React、TypeScript、RAG、LangGraph、Multi-Agent、FastMCP、JWT、Docker

项目亮点：
- 基于 FastAPI 设计企业工单系统后端，完成用户认证、工单管理、知识库管理、AI 建议审核、审计日志和数据看板等模块；
- 构建企业知识库 RAG 流程，对 FAQ/SOP 文档进行上传、解析、切分、向量化和语义检索，并在 AI 回复中返回引用来源；
- 使用 LangGraph 构建可控的 Multi-Agent 工作流，由 Supervisor Agent 协调 Triage、Knowledge、Similar Case、Reply、Risk、Workflow 等专业 Agent；
- 引入 audit_trail 记录每个 Agent 的输入摘要、输出摘要和执行状态，提升多 Agent 决策过程的可解释性和可审计性；
- 通过 Human-in-the-loop 审核机制，确保 AI 只生成回复草稿，不直接发送客户回复，降低企业自动化风险；
- 使用 FastMCP 封装 search_knowledge_base、get_ticket_detail、run_multi_agent_ticket_process 等 MCP tools，使企业工单处理能力可被外部 AI 客户端标准化调用；
- 设计 dry_run、审计日志、只读/写操作分级等安全机制，控制 MCP 工具调用风险；
- 使用 Docker Compose 完成前后端和依赖服务的一键启动，并提供种子数据和演示脚本。
```
