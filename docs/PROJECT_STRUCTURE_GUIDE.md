# 项目结构与代码说明

## 1. 文档定位

这份文档基于当前仓库的实际内容整理，目标是帮助你快速回答下面四类问题：

- 这个项目的整体结构是什么。
- 每个主要文件是做什么的。
- 当前代码实际用了哪些技术栈。
- 哪些文件和运行信息最值得优先关注。

说明范围如下：

- 重点覆盖业务源码、配置、脚本、测试和文档文件。
- 对 `node_modules`、`dist`、`__pycache__`、数据库、日志、上传文件等第三方依赖或运行产物，按目录级说明，不逐个展开第三方包文件。

## 2. 项目概览

项目名称：`企业智能工单与知识库 Multi-Agent 平台`

一句话说明：

```text
基于 FastAPI + RAG + LangGraph Multi-Agent + FastMCP 的企业级智能工单处理平台。
```

项目核心闭环：

```text
工单创建
-> AI 分类
-> 知识库检索
-> RAG 回复草稿
-> 人工审核
-> Multi-Agent 协作分析
-> 审计与数据看板
-> MCP 对外开放
```

## 3. 技术栈

- 后端框架：`FastAPI`
- 数据建模与数据库访问：`SQLAlchemy 2.x`
- 配置管理：`pydantic-settings`
- 认证鉴权：`python-jose`、`passlib[bcrypt]`
- 数据库：`SQLite` 默认，`PostgreSQL` 可选
- 文件上传：`python-multipart`
- LLM 层：`MockLLMClient`、`OpenAI-compatible` 接口
- Embedding 层：`FakeEmbeddingProvider`
- RAG 检索：本地 JSON 向量索引 + 余弦相似度
- 工作流：`LangGraph`
- MCP：`FastMCP`
- 前端：`React 18`、`TypeScript`、`Vite`
- 路由：`react-router-dom`
- HTTP 客户端：`axios`
- 部署：`Docker Compose`、`Nginx`
- 测试：`pytest`

## 4. 顶层结构

```text
.
├── backend/                  后端代码、脚本、测试、数据库与上传文件
├── docs/                     项目文档、演示文档、交接文档
├── frontend/                 前端代码与构建配置
├── .env.example              环境变量示例
├── .gitignore                Git 忽略规则
├── AGENTS.md                 Codex 执行规范
├── PROJECT_IMPLEMENTATION_PLAN.md
├── README.md
└── docker-compose.yml
```

## 5. 重要文件与关键信息

### 5.1 最重要的文件

- `AGENTS.md`：项目执行规则，总规范入口。
- `PROJECT_IMPLEMENTATION_PLAN.md`：完整实施计划，定义 Step 00-37。
- `docs/PROJECT_HANDOFF.md`：跨会话交接文档，记录当前完成状态。
- `README.md`：项目介绍、启动方式、演示入口、简历包装。
- `backend/app/main.py`：后端 FastAPI 应用入口。
- `backend/app/api/ai.py`：AI 分类、RAG 草稿、单流程、多 Agent 的 HTTP 入口。
- `backend/app/services/ticket_service.py`：工单主业务服务。
- `backend/app/services/knowledge_service.py`：知识库上传、切分、检索主服务。
- `backend/app/services/rag_service.py`：RAG 回复草稿生成核心。
- `backend/app/graphs/ticket_multi_agent_graph.py`：Multi-Agent 编排核心。
- `backend/app/mcp/server.py`：FastMCP 入口，暴露 tools。
- `frontend/src/pages/TicketDetailPage.tsx`：前端最核心页面，串起 AI 审核和 Multi-Agent 展示。
- `frontend/src/pages/KnowledgePage.tsx`：知识库上传、搜索、异步处理状态展示页面。

### 5.2 当前关键运行信息

- 本地前端地址：`http://localhost:5173`
- 本地后端地址：`http://localhost:8010`
- Docker Compose 前端地址：`http://localhost:5173`
- Docker Compose 后端地址：`http://localhost:8000`
- 健康检查：`/health`
- 默认测试账号：
  - `admin@example.com / admin123`
  - `agent@example.com / agent123`
  - `viewer@example.com / viewer123`
- 默认开发模式：
  - `LLM_PROVIDER=mock`
  - `EMBEDDING_PROVIDER=fake`

### 5.3 当前最值得知道的实现特点

- AI 只生成建议，不直接发送客户回复。
- 回复建议必须经过 `approve / edit / reject` 人工审核。
- Multi-Agent 流程固定顺序执行，便于演示与审计。
- `audit_trail` 会记录每个 Agent 的输入摘要、输出摘要和执行状态。
- MCP 写操作默认强调 `dry_run=True` 的安全边界。

## 6. 文件用途清单

### 6.1 根目录文件

- `AGENTS.md`：项目执行规范，约束开发步骤、文档更新、架构分层和安全边界。
- `PROJECT_IMPLEMENTATION_PLAN.md`：完整的阶段性实施方案和验收标准。
- `README.md`：项目总说明、启动方式、架构概览、演示建议和简历包装。
- `.env.example`：环境变量示例模板，包含数据库、LLM、Embedding、前端代理等配置示例。
- `.gitignore`：忽略 Python、Node、数据库、缓存、上传文件和构建产物。
- `docker-compose.yml`：编排 backend、frontend、postgres、redis 服务的 Compose 配置。
- `backend-dev.log`：根目录下的后端开发日志占位文件。
- `backend-dev.err.log`：根目录下的后端错误日志占位文件。
- `frontend-dev.log`：根目录下的前端开发日志占位文件。
- `frontend-dev.err.log`：根目录下的前端错误日志占位文件。

### 6.2 文档目录 `docs/`

- `docs/API_DESIGN.md`：按模块整理的 HTTP API 与 MCP 接口设计说明。
- `docs/ARCHITECTURE.md`：架构分层、RAG、Multi-Agent、安全设计的说明文档。
- `docs/DEMO_SCRIPT.md`：面试或录屏时可直接照着讲的演示脚本。
- `docs/PROJECT_HANDOFF.md`：交接文档，记录当前项目进度、验证结果、已知问题和下一步建议。
- `docs/USER_OPERATION_GUIDE.md`：面向使用者/演示者的操作手册。
- `docs/PROJECT_STRUCTURE_GUIDE.md`：本文件，专门解释项目结构、文件职责和重要信息。

### 6.3 后端根目录 `backend/`

- `backend/.dockerignore`：后端镜像构建时的忽略规则。
- `backend/.env`：本地后端私有环境变量文件，不应写入真实密钥到仓库。
- `backend/Dockerfile`：后端镜像构建脚本。
- `backend/requirements.txt`：后端 Python 依赖清单。
- `backend/pytest.ini`：pytest 配置文件。
- `backend/sample.md`：知识库上传/切分测试用的短 Markdown 样例。
- `backend/sample_long.md`：知识库长文档切分测试样例。
- `backend/invalid.pdf`：上传校验的反例样本，用来验证仅支持 txt/md。
- `backend/app.db`：默认 SQLite 数据库文件。
- `backend/backend-dev.out.log`：后端目录内的标准输出日志。
- `backend/backend-dev.err.log`：后端目录内的错误输出日志。

### 6.4 后端应用入口 `backend/app/`

- `backend/app/__init__.py`：后端应用包标记文件。
- `backend/app/main.py`：创建 FastAPI 应用、加载 CORS、挂载总路由。

### 6.5 后端 API 层 `backend/app/api/`

- `backend/app/api/__init__.py`：聚合所有 API router 并统一挂载。
- `backend/app/api/ai.py`：暴露 AI 分类、RAG 回复草稿、单流程工作流、多 Agent 运行和运行记录接口。
- `backend/app/api/analytics.py`：暴露 Dashboard 统计总览接口。
- `backend/app/api/auth.py`：登录、当前用户获取、JWT 用户解析。
- `backend/app/api/health.py`：健康检查接口。
- `backend/app/api/knowledge.py`：知识库上传、文档列表、详情、chunk 列表、语义搜索接口。
- `backend/app/api/reviews.py`：AI 建议审核接口，支持 approve、edit、reject。
- `backend/app/api/tickets.py`：工单 CRUD、消息查询、新增消息、相似工单查询接口。

### 6.6 后端核心配置 `backend/app/core/`

- `backend/app/core/__init__.py`：核心配置包标记文件。
- `backend/app/core/config.py`：统一读取环境变量，定义数据库、LLM、Embedding、上传目录等设置。
- `backend/app/core/security.py`：密码哈希、JWT 生成、JWT 解码和用户 subject 解析。

### 6.7 后端数据库层 `backend/app/db/`

- `backend/app/db/__init__.py`：数据库包标记文件。
- `backend/app/db/base.py`：SQLAlchemy `Base` 和通用时间戳混入类定义。
- `backend/app/db/init_db.py`：初始化数据库、自动补列、补默认用户、同步嵌入表。
- `backend/app/db/session.py`：创建 SQLAlchemy engine、SessionLocal 和依赖注入 `get_db()`。

### 6.8 后端数据模型 `backend/app/models/`

- `backend/app/models/__init__.py`：集中导入所有模型，便于 `create_all()` 扫描。
- `backend/app/models/agent_run_log.py`：记录 LangGraph/Multi-Agent 运行日志。
- `backend/app/models/ai_suggestion.py`：保存 AI 草稿、审核状态、来源、置信度和最终内容。
- `backend/app/models/audit_log.py`：保存业务审计日志。
- `backend/app/models/knowledge_chunk.py`：保存知识文档切分后的 chunk。
- `backend/app/models/knowledge_doc.py`：保存知识文档主记录、状态、文件路径和原文。
- `backend/app/models/ticket.py`：保存工单主实体。
- `backend/app/models/ticket_embedding.py`：保存工单 embedding 标识和内容哈希。
- `backend/app/models/ticket_message.py`：保存工单消息/对话记录。
- `backend/app/models/user.py`：保存用户、角色、密码和激活状态。

### 6.9 后端 Schema 层 `backend/app/schemas/`

- `backend/app/schemas/__init__.py`：schema 包标记文件。
- `backend/app/schemas/agent.py`：Agent 审计条目和运行日志输出模型。
- `backend/app/schemas/ai.py`：AI 分类、回复草稿、工作流输出、恢复请求等模型。
- `backend/app/schemas/analytics.py`：Dashboard 统计输出模型。
- `backend/app/schemas/auth.py`：登录请求和 token 返回模型。
- `backend/app/schemas/knowledge.py`：知识文档、chunk、搜索请求和搜索结果模型。
- `backend/app/schemas/review.py`：AI 建议审核请求和审核返回模型。
- `backend/app/schemas/ticket.py`：工单创建、更新、详情和相似工单输出模型。
- `backend/app/schemas/ticket_message.py`：工单消息创建和读取模型。
- `backend/app/schemas/user.py`：用户输出模型。

### 6.10 后端 Repository 层 `backend/app/repositories/`

- `backend/app/repositories/__init__.py`：repository 包标记文件。
- `backend/app/repositories/agent_run_repository.py`：`AgentRunLog` 的增删改查。
- `backend/app/repositories/audit_log_repository.py`：`AuditLog` 的写入和查询。
- `backend/app/repositories/knowledge_chunk_repository.py`：知识 chunk 的列表、批量创建和删除。
- `backend/app/repositories/knowledge_repository.py`：知识文档查询、保存、chunk 计数。
- `backend/app/repositories/suggestion_repository.py`：AI suggestion 的查询和保存。
- `backend/app/repositories/ticket_embedding_repository.py`：工单 embedding 记录查询和保存。
- `backend/app/repositories/ticket_message_repository.py`：工单消息查询与创建。
- `backend/app/repositories/ticket_repository.py`：工单主表查询、列表、保存和筛选。
- `backend/app/repositories/user_repository.py`：用户查询与创建。

### 6.11 后端 Service 层 `backend/app/services/`

- `backend/app/services/__init__.py`：service 包标记文件。
- `backend/app/services/agent_run_service.py`：封装 Agent 运行日志的 upsert、查询与异常抛出。
- `backend/app/services/analytics_service.py`：计算总工单数、未结案数、AI 采纳率和分类分布。
- `backend/app/services/audit_service.py`：统一写入业务审计日志。
- `backend/app/services/chunking_service.py`：按固定 chunk 大小和 overlap 切分知识文档。
- `backend/app/services/embedding_service.py`：Embedding 抽象层，当前实现 `FakeEmbeddingProvider`。
- `backend/app/services/knowledge_service.py`：知识库上传、后台处理、切分、向量索引和搜索核心服务。
- `backend/app/services/llm_service.py`：LLM 抽象层，当前支持 mock 和 openai-compatible 两种模式。
- `backend/app/services/mcp_agent_service.py`：把 Multi-Agent 结果封装成 MCP 侧可用的服务能力。
- `backend/app/services/rag_service.py`：知识检索、上下文置信度计算、回复草稿生成与来源保存。
- `backend/app/services/review_service.py`：AI 草稿人工审核服务，负责 approve/edit/reject。
- `backend/app/services/risk_service.py`：判断回复风险级别和是否必须人工审核。
- `backend/app/services/ticket_service.py`：工单创建、更新、分类、消息、工作流应用等核心业务服务。
- `backend/app/services/ticket_similarity_service.py`：工单 embedding 维护和历史相似工单推荐。
- `backend/app/services/user_service.py`：默认用户种子、认证和用户查询服务。
- `backend/app/services/vector_store_service.py`：本地 JSON 向量索引重建与余弦相似度搜索。

### 6.12 后端 Agent 层 `backend/app/agents/`

- `backend/app/agents/__init__.py`：agent 包标记文件。
- `backend/app/agents/base_agent.py`：所有 Agent 的公共依赖基类。
- `backend/app/agents/knowledge_agent.py`：负责知识检索 query 生成与知识命中结果输出。
- `backend/app/agents/reply_agent.py`：整合 triage、knowledge、similar case 结果，生成回复草稿。
- `backend/app/agents/risk_agent.py`：对回复草稿做风险判断。
- `backend/app/agents/similar_case_agent.py`：检索历史相似工单并生成处理摘要。
- `backend/app/agents/supervisor_agent.py`：规划固定顺序 Multi-Agent 流程。
- `backend/app/agents/triage_agent.py`：负责工单结构化分诊。
- `backend/app/agents/workflow_agent.py`：给出状态流转、推荐部门和下一步动作建议。

### 6.13 后端 Graph 层 `backend/app/graphs/`

- `backend/app/graphs/__init__.py`：graph 包标记文件。
- `backend/app/graphs/ticket_agent_graph.py`：单流程 LangGraph，支持普通执行和 human review interrupt。
- `backend/app/graphs/ticket_agent_state.py`：单流程工作流的状态定义。
- `backend/app/graphs/ticket_multi_agent_graph.py`：Multi-Agent LangGraph，负责固定顺序执行、interrupt 和审计轨迹。
- `backend/app/graphs/ticket_multi_agent_state.py`：Multi-Agent 工作流状态定义。

### 6.14 后端 MCP 层 `backend/app/mcp/`

- `backend/app/mcp/__init__.py`：MCP 包标记文件。
- `backend/app/mcp/prompts.py`：注册 MCP prompts，把本地 prompt 模板转换为可复用提示。
- `backend/app/mcp/resources.py`：注册 `ticket://`、`knowledge-doc://`、`analytics://overview` 资源。
- `backend/app/mcp/server.py`：启动 FastMCP 服务并注册 tools、resources、prompts。

### 6.15 后端 Prompt 模板 `backend/app/prompts/`

- `backend/app/prompts/classify_ticket.txt`：工单分类用 prompt 模板。
- `backend/app/prompts/generate_reply.txt`：RAG 回复草稿生成用 prompt 模板。
- `backend/app/prompts/risk_review.txt`：风险审查用 prompt 模板。
- `backend/app/prompts/summarize_ticket.txt`：工单摘要用 prompt 模板。

### 6.16 后端脚本 `backend/scripts/`

- `backend/scripts/seed_data.py`：写入演示用户、知识文档、历史工单、当前工单和 AI 建议数据。
- `backend/scripts/test_mcp_client.py`：本地 MCP client 验证脚本，用于调用本项目 MCP server。

### 6.17 后端测试 `backend/tests/`

- `backend/tests/conftest.py`：测试隔离环境、测试数据库和公共 fixture 定义。
- `backend/tests/test_ai.py`：验证 mock 分类和 RAG 回复草稿生成。
- `backend/tests/test_auth.py`：验证登录和当前用户接口。
- `backend/tests/test_health.py`：验证健康检查接口。
- `backend/tests/test_knowledge.py`：验证知识库上传与搜索流程。
- `backend/tests/test_tickets.py`：验证工单 CRUD、消息与基础链路。

### 6.18 前端根目录 `frontend/`

- `frontend/.dockerignore`：前端镜像构建忽略规则。
- `frontend/Dockerfile`：前端生产镜像构建脚本。
- `frontend/index.html`：Vite 前端宿主 HTML。
- `frontend/nginx.conf`：生产环境静态资源与反向代理配置。
- `frontend/package.json`：前端依赖、脚本和元数据。
- `frontend/package-lock.json`：npm 依赖锁文件。
- `frontend/tsconfig.json`：TypeScript 总配置。
- `frontend/tsconfig.app.json`：应用代码的 TypeScript 配置。
- `frontend/tsconfig.node.json`：Node/Vite 配置文件的 TypeScript 配置。
- `frontend/vite.config.ts`：Vite 开发服务器与 `/api` 代理配置源文件。
- `frontend/vite.config.js`：由 TypeScript 编译产出的 Vite 配置 JS 文件。
- `frontend/vite.config.d.ts`：Vite 配置的类型声明产物。
- `frontend/tsconfig.app.tsbuildinfo`：应用代码的 TypeScript 增量编译缓存。
- `frontend/tsconfig.node.tsbuildinfo`：Node 配置的 TypeScript 增量编译缓存。
- `frontend/frontend-dev.out.log`：前端目录内的标准输出日志。
- `frontend/frontend-dev.err.log`：前端目录内的错误输出日志。

### 6.19 前端应用入口 `frontend/src/`

- `frontend/src/App.tsx`：挂载路由和认证上下文。
- `frontend/src/main.tsx`：React 启动入口。
- `frontend/src/styles.css`：全局样式与页面视觉实现。
- `frontend/src/vite-env.d.ts`：Vite 环境变量类型声明。

### 6.20 前端 API 层 `frontend/src/api/`

- `frontend/src/api/ai.ts`：AI 分类、回复草稿、审核、多 Agent 与运行记录的类型和请求封装。
- `frontend/src/api/analytics.ts`：Dashboard 统计接口类型和请求封装。
- `frontend/src/api/auth.ts`：登录和当前用户接口封装。
- `frontend/src/api/client.ts`：axios 实例、token 注入和 401 处理器。
- `frontend/src/api/knowledge.ts`：知识库文档、chunk、上传和搜索接口封装。
- `frontend/src/api/tickets.ts`：工单、消息、状态更新相关的类型和请求封装。

### 6.21 前端组件 `frontend/src/components/`

- `frontend/src/components/AppLayout.tsx`：后台主布局，包含侧边栏、顶部栏和内容出口。
- `frontend/src/components/ProtectedRoute.tsx`：登录态校验和未授权跳转。

### 6.22 前端页面 `frontend/src/pages/`

- `frontend/src/pages/DashboardPage.tsx`：展示统计卡、分类分布、优先级分布和 AI adoption。
- `frontend/src/pages/HomePage.tsx`：保留的早期受保护页面，占位说明当前工作区已接通。
- `frontend/src/pages/KnowledgeDetailPage.tsx`：展示知识文档原文、状态、chunk 和处理结果。
- `frontend/src/pages/KnowledgePage.tsx`：知识库上传、搜索、列表和异步处理状态展示页。
- `frontend/src/pages/LoginPage.tsx`：登录页，内置演示账号提示。
- `frontend/src/pages/TicketCreatePage.tsx`：新建工单页面。
- `frontend/src/pages/TicketDetailPage.tsx`：工单详情、AI 分类、RAG 草稿审核、Multi-Agent 结果与审计时间线页面。
- `frontend/src/pages/TicketsPage.tsx`：工单列表页，支持状态、优先级、分类筛选。

### 6.23 前端路由与状态 `frontend/src/routes/`、`frontend/src/stores/`

- `frontend/src/routes/index.tsx`：定义登录页、Dashboard、Tickets、Knowledge 等路由结构。
- `frontend/src/stores/auth.tsx`：认证上下文、token 持久化、自动恢复登录态与登出逻辑。

## 7. 运行产物与辅助文件说明

这些文件不是核心业务源码，但在理解项目现状时也很重要。

### 7.1 依赖与构建产物

- `frontend/node_modules/`：前端第三方依赖目录，不建议纳入业务说明逐文件展开。
- `frontend/dist/`：前端构建产物目录，包含 `index.html`、JS、CSS 静态资源。
- `backend/app/__pycache__/`、`backend/app/*/__pycache__/`、`backend/tests/__pycache__/`：Python 字节码缓存。
- `backend/.pytest_cache/`：pytest 运行缓存目录。

### 7.2 数据与上传产物

- `backend/data/knowledge_vector_store.json`：本地知识向量索引文件，由 `VectorStoreService` 生成。
- `backend/uploads/knowledge/`：知识库上传目录，包含种子文档和手工上传后的文本文件。
- `backend/uploads/knowledge/seed_demo_payment_incident_sop.md`：支付类 SOP 种子知识文档。
- `backend/uploads/knowledge/seed_demo_invoice_correction_policy.md`：发票修正规则种子知识文档。
- `backend/uploads/knowledge/seed_demo_refund_review_playbook.md`：退款审核流程种子知识文档。
- `backend/uploads/knowledge/*.txt`、`backend/uploads/knowledge/*.md`：运行时保存的真实上传文件，多为 UUID 命名。

### 7.3 探针与临时验证文件

- `backend/test_step35_probe.db`：Step 35 测试或探针阶段遗留的 SQLite 文件。
- `backend/test_step35_probe2.db`：另一份测试探针数据库。
- `backend/test_data_probe2/vector.json`：本地向量检索探针数据文件。
- `backend/test_uploads_probe2/5f9915fb62cb42e1a5f49ff25c4d36ef.txt`：探针阶段保留的上传样本。

## 8. 最推荐优先阅读的顺序

如果你要快速理解项目，建议按下面顺序看代码：

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `backend/app/main.py`
4. `backend/app/api/ai.py`
5. `backend/app/services/ticket_service.py`
6. `backend/app/services/knowledge_service.py`
7. `backend/app/services/rag_service.py`
8. `backend/app/graphs/ticket_multi_agent_graph.py`
9. `backend/app/mcp/server.py`
10. `frontend/src/pages/TicketDetailPage.tsx`
11. `frontend/src/pages/KnowledgePage.tsx`
12. `docs/PROJECT_HANDOFF.md`

## 9. 一句话总结

这个仓库已经形成了比较完整的企业 AI 工单系统骨架：

- 后端分层清楚。
- AI、RAG、审核、Multi-Agent、MCP 都有独立模块。
- 前端已经把工单、知识库、AI 审核、执行时间线串成可演示页面。
- 文档、脚本、测试、种子数据也已经具备面试展示和二次接手的基础。
