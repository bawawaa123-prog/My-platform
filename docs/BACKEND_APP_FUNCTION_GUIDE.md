# backend/app 后端函数级说明

## 1. 文档目的

这份文档专门面向 `backend/app` 目录，重点回答两个问题：

- 每个后端文件在整个系统里扮演什么角色。
- 每个文件里最值得优先理解的重要函数或方法是什么。

阅读建议：

- 先看本文件掌握骨架。
- 再打开对应源码文件，对照中文注释和函数说明看实现。

## 2. backend/app 总体分层

```text
api/            HTTP 接口入口
core/           配置、JWT、安全能力
db/             数据库连接与初始化
models/         SQLAlchemy 模型
schemas/        Pydantic 输入输出模型
repositories/   数据访问封装
services/       业务逻辑核心
agents/         单个 Agent 的职责封装
graphs/         LangGraph 工作流编排
mcp/            FastMCP tools/resources/prompts
prompts/        Prompt 模板文件
main.py         FastAPI 应用入口
```

## 3. 入口层

### [backend/app/main.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/main.py)

文件作用：

- 创建 FastAPI 应用。
- 读取配置。
- 加载 CORS。
- 挂载总路由。

重要函数：

- `create_app()`
  - 应用工厂函数。
  - 负责初始化 FastAPI 实例并挂载全局中间件和路由。
  - 是后端启动、测试和部署复用的统一入口。

## 4. API 层

### [backend/app/api/__init__.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/api/__init__.py)

文件作用：

- 聚合所有 API router。
- 把 auth、tickets、knowledge、ai、reviews、analytics、health 统一注册到总路由。

### [backend/app/api/auth.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/api/auth.py)

文件作用：

- 登录鉴权入口。
- Bearer Token 解析。
- 当前用户注入。

重要函数：

- `get_current_user(...)`
  - 解析请求头中的 JWT。
  - 验证 token 是否有效。
  - 根据 token 里的用户 ID 查数据库并返回真实用户对象。
  - 是几乎所有受保护接口都会复用的依赖函数。

- `login(payload, db)`
  - 校验邮箱和密码。
  - 生成访问 token。
  - 返回 `access_token + 当前用户信息`。

- `get_me(current_user)`
  - 返回当前登录用户信息。

### [backend/app/api/health.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/api/health.py)

文件作用：

- 提供服务健康检查。

重要函数：

- `health_check()`
  - 返回 `{"status": "ok"}`。
  - 常用于 Docker healthcheck、服务连通性检查和 smoke test。

### [backend/app/api/tickets.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/api/tickets.py)

文件作用：

- 工单主业务接口入口。

重要函数：

- `create_ticket(...)`
  - 新建工单。
  - 最终调用 `TicketService.create_ticket()`。

- `list_tickets(...)`
  - 查询所有工单列表。

- `get_ticket(ticket_id, ...)`
  - 查询单个工单详情。

- `update_ticket(ticket_id, payload, ...)`
  - 更新工单状态、标题、描述、优先级等字段。

- `list_ticket_messages(ticket_id, ...)`
  - 读取工单消息历史。

- `add_ticket_message(ticket_id, payload, ...)`
  - 为工单追加一条消息。

- `list_similar_tickets(ticket_id, top_k, ...)`
  - 查询历史相似工单。
  - 最终走 `TicketSimilarityService`。

### [backend/app/api/knowledge.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/api/knowledge.py)

文件作用：

- 知识库上传、文档详情、chunk 详情、搜索接口入口。

重要函数：

- `build_knowledge_doc_response(knowledge_doc, chunks_count=...)`
  - 统一把文档模型转换成带 `chunks_count` 的返回结构。

- `upload_knowledge_doc(...)`
  - 接收文件上传。
  - 调用 `KnowledgeService.upload_document()` 把原始文档落库。
  - 再用 `BackgroundTasks` 投递后台处理任务。

- `list_knowledge_docs(...)`
  - 返回知识文档列表。

- `get_knowledge_doc(doc_id, ...)`
  - 返回知识文档详情。

- `list_knowledge_chunks(doc_id, ...)`
  - 返回文档切分后的 chunk 列表。

- `search_knowledge(payload, ...)`
  - 发起语义检索。
  - 最终调用 `KnowledgeService.search_knowledge()`。

### [backend/app/api/reviews.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/api/reviews.py)

文件作用：

- AI 草稿的人工审核接口入口。

重要函数：

- `approve_suggestion(...)`
  - 把草稿直接批准为最终结果。

- `edit_suggestion(...)`
  - 以人工编辑后的文本替换草稿并通过审核。

- `reject_suggestion(...)`
  - 拒绝草稿并记录拒绝原因。

### [backend/app/api/analytics.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/api/analytics.py)

文件作用：

- 数据看板统计接口入口。

重要函数：

- `get_analytics_overview(...)`
  - 返回总工单数、未结案数、紧急工单数、AI 建议数、AI 采纳率、分类分布、优先级分布。

### [backend/app/api/ai.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/api/ai.py)

文件作用：

- AI 分类、RAG 回复、单流程 LangGraph、Multi-Agent 工作流的统一接口层。

重要函数：

- `classify_ticket(ticket_id, ...)`
  - 触发单次 AI 分类。
  - 结果会写回工单字段。

- `generate_ticket_reply(ticket_id, ...)`
  - 为当前工单生成一份 RAG 回复草稿。

- `list_ticket_suggestions(ticket_id, ...)`
  - 返回该工单已有的 AI 草稿列表。

- `process_ticket(ticket_id, ...)`
  - 直接运行单流程 LangGraph，不中断，跑到最终输出。

- `start_ticket_process(ticket_id, ...)`
  - 运行带 interrupt 的单流程工作流。
  - 在 `human_review` 节点暂停。

- `resume_ticket_process(ticket_id, payload, ...)`
  - 把人工审核动作送回工作流，继续执行到 finalize。

- `start_multi_agent_ticket_process(ticket_id, ...)`
  - 启动固定顺序 Multi-Agent 工作流。
  - 会在人工审核前暂停，并返回各 Agent 的输出和 `audit_trail`。

- `list_ticket_agent_runs(ticket_id, ...)`
  - 查询某张工单的 Agent 运行记录。

- `get_agent_run(run_id, ...)`
  - 查询某次指定运行记录详情。

## 5. core 层

### [backend/app/core/config.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/core/config.py)

文件作用：

- 统一环境变量配置源。

重要函数 / 类：

- `Settings`
  - 定义应用名、数据库地址、JWT、LLM、Embedding、上传目录等配置项。

- `get_settings()`
  - 用 `lru_cache` 缓存配置对象。
  - 保证进程内配置只初始化一次。

### [backend/app/core/security.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/core/security.py)

文件作用：

- 密码哈希和 JWT 处理。

重要函数：

- `verify_password(plain_password, hashed_password)`
  - 校验明文密码和哈希值是否匹配。

- `get_password_hash(password)`
  - 生成密码哈希。

- `create_access_token(subject, expires_delta=None)`
  - 签发 JWT。

- `decode_access_token(token)`
  - 解码 JWT。

- `parse_token_subject(token)`
  - 安全地从 JWT 中解析 `sub` 字段。
  - 失败时返回 `None`，避免直接抛未处理异常。

## 6. db 层

### [backend/app/db/base.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/db/base.py)

文件作用：

- 定义 SQLAlchemy `Base`。
- 定义公共时间戳字段混入类。

重要类：

- `Base`
  - 全部模型的 declarative 基类。

- `TimestampMixin`
  - 提供 `created_at`、`updated_at` 公共字段。

### [backend/app/db/session.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/db/session.py)

文件作用：

- 初始化数据库连接。
- 生成 `SessionLocal`。
- 提供 FastAPI 依赖注入。

重要对象 / 函数：

- `engine`
  - 数据库引擎。
  - SQLite 会附加 `check_same_thread=False`。

- `SessionLocal`
  - 业务层和 API 层使用的数据库会话工厂。

- `get_db()`
  - FastAPI 的数据库依赖函数。

### [backend/app/db/init_db.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/db/init_db.py)

文件作用：

- 初始化数据库。
- 自动补表、补列、补默认用户。

重要函数：

- `init_db()`
  - 执行数据库连通性检查。
  - `create_all()`。
  - 补列、补表、补用户。

- `seed_default_users()`
  - 写入默认测试账号。

- `sync_ticket_ai_columns()`
  - 给旧版 `tickets` 表补 `sentiment`、`ai_summary`、`recommended_department` 字段。

- `sync_ai_suggestion_review_columns()`
  - 给旧版 `ai_suggestions` 表补审核相关字段。

- `sync_ticket_embedding_table()`
  - 在没有 `ticket_embeddings` 表时手动建表。

## 7. models 层

这一层主要是数据结构定义，没有复杂业务函数，但它们都很关键。

- [backend/app/models/user.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/models/user.py)
  - `User`：用户、角色、密码、启用状态。

- [backend/app/models/ticket.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/models/ticket.py)
  - `Ticket`：工单主实体。

- [backend/app/models/ticket_message.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/models/ticket_message.py)
  - `TicketMessage`：工单消息流。

- [backend/app/models/knowledge_doc.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/models/knowledge_doc.py)
  - `KnowledgeDoc`：知识文档主记录。

- [backend/app/models/knowledge_chunk.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/models/knowledge_chunk.py)
  - `KnowledgeChunk`：知识切片。

- [backend/app/models/ai_suggestion.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/models/ai_suggestion.py)
  - `AISuggestion`：AI 草稿和审核结果。

- [backend/app/models/audit_log.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/models/audit_log.py)
  - `AuditLog`：操作审计。

- [backend/app/models/ticket_embedding.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/models/ticket_embedding.py)
  - `TicketEmbedding`：工单 embedding 元信息。

- [backend/app/models/agent_run_log.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/models/agent_run_log.py)
  - `AgentRunLog`：工作流运行记录。

## 8. schemas 层

这一层主要是输入输出模型，没有复杂函数，重点是理解它们服务哪个模块。

- `auth.py`：登录入参和 token 出参。
- `user.py`：用户返回结构。
- `ticket.py`：工单创建、更新、读取、相似工单返回结构。
- `ticket_message.py`：消息创建和读取结构。
- `knowledge.py`：知识文档、chunk、搜索入参和结果结构。
- `review.py`：审核 approve/edit/reject 请求结构。
- `analytics.py`：Dashboard 统计结构。
- `ai.py`：AI 分类、回复草稿、工作流输出、恢复请求结构。
- `agent.py`：Agent 审计条目和运行记录结构。

## 9. repository 层

Repository 的职责是“只做数据访问”，不放复杂业务判断。

- `user_repository.py`
  - 关键作用：按邮箱/ID 查询用户、创建用户。

- `ticket_repository.py`
  - 关键作用：工单列表、ID 查询、保存、查询已解决历史工单。

- `ticket_message_repository.py`
  - 关键作用：按工单查询消息、创建消息。

- `knowledge_repository.py`
  - 关键作用：文档列表、详情、保存、统计 chunk 数。

- `knowledge_chunk_repository.py`
  - 关键作用：chunk 列表、批量创建、按文档删除。

- `suggestion_repository.py`
  - 关键作用：保存草稿、按工单查询草稿、取最新已审核回复。

- `ticket_embedding_repository.py`
  - 关键作用：按工单查询和保存 embedding 元信息。

- `audit_log_repository.py`
  - 关键作用：写入审计日志。

- `agent_run_repository.py`
  - 关键作用：按 run_id、ticket_id 查询或保存工作流运行日志。

## 10. service 层

### [backend/app/services/user_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/user_service.py)

文件作用：

- 用户认证和默认用户写入。

重要方法：

- `authenticate_user(email, password)`
  - 认证登录用户。

- `get_user_by_id(user_id)`
  - 查用户。

- `ensure_default_users()`
  - 初始化默认账号。

### [backend/app/services/audit_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/audit_service.py)

文件作用：

- 统一写审计日志。

重要方法：

- `log_action(...)`
  - 接收用户、动作、目标对象、详情并写入 `AuditLog`。

### [backend/app/services/agent_run_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/agent_run_service.py)

文件作用：

- 统一维护 `AgentRunLog`。

重要方法：

- `upsert_run_log(...)`
  - 创建或更新某次工作流运行记录。

- `list_by_ticket_id(ticket_id)`
  - 按工单查运行历史。

- `get_by_run_id(run_id)`
  - 按运行 ID 查详情。

### [backend/app/services/chunking_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/chunking_service.py)

文件作用：

- 文档切分。

重要类 / 方法：

- `ChunkingConfig`
  - 控制 `chunk_size` 和 `overlap`。

- `split_text(text)`
  - 把原文切成重叠 chunk。

### [backend/app/services/embedding_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/embedding_service.py)

文件作用：

- Embedding 抽象。

重要类 / 方法：

- `EmbeddingProvider`
  - 统一抽象接口。

- `FakeEmbeddingProvider.embed_text(text)`
  - 用哈希构造稳定伪向量。

- `FakeEmbeddingProvider.build_embedding_id(text)`
  - 为文本生成稳定 embedding_id。

- `OpenAICompatibleEmbeddingProvider`
  - 预留真实 embedding provider 入口，当前未启用真正调用。

- `get_embedding_provider()`
  - 根据配置返回 provider。

### [backend/app/services/vector_store_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/vector_store_service.py)

文件作用：

- 本地 JSON 向量索引读写。

重要方法：

- `rebuild_knowledge_index(chunks)`
  - 按全部 chunk 重建本地向量索引文件。

- `search_knowledge_chunks(query, top_k)`
  - 对 query 向量和 chunk 向量做余弦相似度排序。

- `_cosine_similarity(left, right)`
  - 实现向量相似度计算。

### [backend/app/services/knowledge_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/knowledge_service.py)

文件作用：

- 知识库业务核心。

重要方法：

- `upload_document(...)`
  - 校验文件类型。
  - 保存原文。
  - 创建 `KnowledgeDoc`。

- `process_document(doc_id)`
  - 后台处理文档。
  - 更新状态为 processing / ready / failed。

- `list_documents()`
  - 文档列表。

- `get_document(doc_id)`
  - 单个文档详情。

- `list_chunks(doc_id)`
  - 文档 chunk 列表。

- `get_chunks_count(doc_id)`
  - 统计文档 chunk 数。

- `search_knowledge(query, top_k=5)`
  - 调用向量检索，返回语义命中结果。

- `_create_chunks_for_doc(knowledge_doc)`
  - 真正执行切分、写 chunk、重建向量索引。

- `_handle_processing_failure(...)`
  - 处理失败时删除脏 chunk、回写错误状态。

- `process_knowledge_document_task(doc_id)`
  - 后台任务入口。

### [backend/app/services/llm_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/llm_service.py)

文件作用：

- LLM 抽象层。

重要类 / 方法：

- `LLMClient`
  - 抽象接口，定义 `generate_text()` 和 `generate_json()`。

- `MockLLMClient.generate_text(...)`
  - 返回带 `[MOCK]` 的文本，用于本地演示。

- `MockLLMClient.generate_json(...)`
  - 返回 mock JSON。

- `OpenAICompatibleLLMClient.generate_text(...)`
  - 通过 OpenAI-compatible 接口生成文本。

- `OpenAICompatibleLLMClient.generate_json(...)`
  - 通过 JSON 模式生成结构化输出。

- `get_llm_client()`
  - 按配置返回 mock 或 openai-compatible 实现。

### [backend/app/services/ticket_similarity_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/ticket_similarity_service.py)

文件作用：

- 工单 embedding 和历史相似工单推荐。

重要方法：

- `list_similar_tickets(ticket_id, top_k=5)`
  - 用当前工单作为查询，找出历史已解决/已关闭的相似工单。

- `ensure_ticket_embedding(ticket)`
  - 为工单补 embedding 元信息。

- `_build_resolution_summary(ticket)`
  - 优先从已审核回复、消息记录、AI 摘要中提取历史处理结果。

### [backend/app/services/ticket_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/ticket_service.py)

文件作用：

- 工单业务核心服务。

重要方法：

- `create_ticket(payload, created_by)`
  - 创建工单。
  - 同步创建 embedding 记录。
  - 写审计日志。

- `list_tickets()`
  - 查询工单列表。

- `list_open_tickets(limit=20)`
  - 返回开放状态队列。

- `get_ticket(ticket_id)`
  - 按 ID 查工单，不存在时抛 404。

- `update_ticket(ticket_id, payload, current_user)`
  - 更新工单字段。
  - 如标题/内容/状态变化则刷新 embedding。
  - 写审计日志。

- `list_ticket_messages(ticket_id)`
  - 查询消息历史。

- `add_ticket_message(ticket_id, payload, current_user)`
  - 新增工单消息并写审计日志。

- `classify_ticket(ticket_id, current_user)`
  - 尝试用 LLM 生成结构化分类结果。
  - 失败时退回本地规则分类。
  - 把分类结果写回工单字段。

- `get_system_user()`
  - 返回系统管理员用户，用于工作流内部自动动作。

- `get_user_by_id(user_id)`
  - 按 ID 查用户。

- `apply_workflow_recommendation(...)`
  - 根据 WorkflowAgent 的建议更新工单状态和部门。

- `serialize_ticket(ticket)`
  - 把模型统一转成前后端一致的 JSON 结构。

- `_generate_ticket_classification(ticket)`
  - 按 prompt 调 LLM 生成结构化分类。

- `_build_fallback_classification(ticket)`
  - 本地规则兜底分类器。

### [backend/app/services/rag_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/rag_service.py)

文件作用：

- RAG 回复生成核心。

重要类 / 方法：

- `RetrievedContext`
  - 封装知识命中结果、置信度和低置信度说明。

- `retrieve_context(query, top_k=5)`
  - 发起知识检索。
  - 按命中分数计算置信度。

- `build_ticket_search_query(ticket)`
  - 把工单信息拼成检索 query。

- `build_answer_prompt(ticket, context, supplemental_context=None)`
  - 构造回复生成 prompt。

- `generate_ticket_reply(ticket)`
  - 标准 RAG 回复生成入口。

- `generate_ticket_reply_from_context(ticket, context, supplemental_context=None)`
  - 允许外部直接传入上下文，用于 ReplyAgent 复用。

- `deserialize_knowledge_hits(items)`
  - 把序列化的知识命中结果恢复成 `KnowledgeSearchItem`。

- `_create_reply_suggestion(...)`
  - 统一创建 `AISuggestion`。
  - 无论是普通 RAG 还是 Multi-Agent，都最终走这里落库。

- `_build_reasoning_summary(...)`
  - 为草稿生成一段可展示的 reasoning summary。

- `_build_fallback_reply(...)`
  - LLM 失败时生成保守回复。

### [backend/app/services/review_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/review_service.py)

文件作用：

- AI 草稿人工审核核心服务。

重要方法：

- `approve_suggestion(...)`
  - 直接批准草稿。

- `edit_suggestion(...)`
  - 保存编辑后内容并标记为 edited。

- `reject_suggestion(...)`
  - 拒绝草稿并记录理由。

- `apply_review_action(...)`
  - 为工作流统一封装审核动作路由。

- `_get_reviewable_suggestion(suggestion_id)`
  - 保证只允许审核 `draft` 状态的 suggestion。

### [backend/app/services/risk_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/risk_service.py)

文件作用：

- 风险判断。

重要类 / 方法：

- `RiskCheckResult`
  - 封装风险等级、是否必须人工审核、理由列表。

- `evaluate_ticket_reply(ticket, reply_suggestion)`
  - 结合优先级、情绪、类别、置信度和敏感词生成风险结论。

### [backend/app/services/analytics_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/analytics_service.py)

文件作用：

- 数据看板计算。

重要方法：

- `get_overview()`
  - 统计工单数、解决数、紧急数、AI 建议数、AI 采纳率和分布数据。

### [backend/app/services/mcp_agent_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/mcp_agent_service.py)

文件作用：

- 把 Multi-Agent 能力包装成 MCP 可调用服务。

重要方法：

- `run_multi_agent_ticket_process(ticket_id, dry_run=True)`
  - dry_run 时走 `preview()`，只返回结果不保留副作用。
  - dry_run=False 时会真正创建运行记录并写审计日志。

- `get_agent_audit_trail(ticket_id)`
  - 返回最新一次 multi-agent 运行的 `audit_trail`。

## 11. agents 层

### [backend/app/agents/base_agent.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/agents/base_agent.py)

文件作用：

- 提供所有 Agent 共用的 service 依赖。

### [backend/app/agents/supervisor_agent.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/agents/supervisor_agent.py)

重要方法：

- `run(ticket=...)`
  - 当前版本不做动态调度。
  - 负责声明固定顺序流程、说明会经过哪些 Agent、必须人工审核。

### [backend/app/agents/triage_agent.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/agents/triage_agent.py)

重要方法：

- `run(ticket_id=...)`
  - 调用 `TicketService.classify_ticket()` 完成结构化分诊。

### [backend/app/agents/knowledge_agent.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/agents/knowledge_agent.py)

重要方法：

- `run(ticket_id=...)`
  - 基于工单字段构造知识检索 query。
  - 返回命中的知识片段、置信度和低置信度说明。

### [backend/app/agents/similar_case_agent.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/agents/similar_case_agent.py)

重要方法：

- `run(ticket_id=...)`
  - 查询历史相似工单。

- `_build_historical_summary(similar_tickets)`
  - 把多条相似案例整理成一句可读摘要。

### [backend/app/agents/reply_agent.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/agents/reply_agent.py)

重要方法：

- `run(ticket_id, triage_result, knowledge_result, similar_case_result)`
  - 把 triage、knowledge、similar_case 合并成 RAG 生成所需上下文。
  - 最终创建回复草稿。

- `_build_supplemental_context(...)`
  - 生成额外上下文文本，喂给 `RagService`。

### [backend/app/agents/risk_agent.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/agents/risk_agent.py)

重要方法：

- `run(ticket_id, reply_result)`
  - 取回复草稿做风险分析。

### [backend/app/agents/workflow_agent.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/agents/workflow_agent.py)

重要方法：

- `run(ticket_id, triage_result, risk_result)`
  - 生成 `next_status`、推荐部门、下一步动作、内部备注。
  - 最后通过 `TicketService.apply_workflow_recommendation()` 修改工单状态。

## 12. graphs 层

### [backend/app/graphs/ticket_agent_state.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/graphs/ticket_agent_state.py)

文件作用：

- 定义单流程 LangGraph 的状态字段。

### [backend/app/graphs/ticket_agent_graph.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/graphs/ticket_agent_graph.py)

文件作用：

- 单流程 LangGraph 编排核心。

重要方法：

- `invoke(ticket_id)`
  - 直接跑完单流程图。

- `start(ticket_id, thread_id=None)`
  - 运行带 interrupt 的图，停在 `human_review`。

- `resume(...)`
  - 将审核动作送回中断工作流。

- `get_pending_review(workflow_id)`
  - 从 checkpoint 中恢复待审核上下文。

- `_build_graph(include_human_review)`
  - 构建普通图和 interrupt 图。

- `_load_ticket(state)`
  - 加载工单详情。

- `_classify_ticket(state)`
  - 运行 AI 分类。

- `_retrieve_knowledge(state)`
  - 检索知识库。

- `_search_similar_tickets(state)`
  - 查询历史相似工单。

- `_generate_reply(state)`
  - 生成回复草稿。

- `_risk_check(state)`
  - 运行风险判断。

- `_human_review(state)`
  - 发出 interrupt，等待人工审核。

- `_finalize(state)`
  - 汇总最终工作流输出。

### [backend/app/graphs/ticket_multi_agent_state.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/graphs/ticket_multi_agent_state.py)

文件作用：

- 定义 Multi-Agent 图状态。

### [backend/app/graphs/ticket_multi_agent_graph.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/graphs/ticket_multi_agent_graph.py)

文件作用：

- Multi-Agent 工作流编排核心。

重要方法：

- `preview(ticket_id)`
  - 供 MCP `dry_run=True` 使用。
  - 运行整张图后清理 suggestion、audit_log、工单状态变化。

- `start(ticket_id, created_by_user_id=None, thread_id=None)`
  - 正式运行 Multi-Agent，并把结果写入 `AgentRunLog`。

- `get_pending_review(workflow_id)`
  - 从 checkpoint 取回暂停在人工审核前的所有 Agent 结果。

- `_build_graph()`
  - 构建固定顺序多 Agent 图。

- `_cleanup_preview_side_effects(...)`
  - 清理 preview 模式运行留下的副作用。

- `_load_ticket(state)`
  - 读取工单。

- `_supervisor(state)`
  - 运行 SupervisorAgent，并追加 audit_trail。

- `_triage(state)`
  - 运行 TriageAgent，并追加 audit_trail。

- `_knowledge(state)`
  - 运行 KnowledgeAgent，并追加 audit_trail。

- `_similar_case(state)`
  - 运行 SimilarCaseAgent，并追加 audit_trail。

- `_reply(state)`
  - 运行 ReplyAgent，并追加 audit_trail。

- `_risk(state)`
  - 运行 RiskAgent，并追加 audit_trail。

- `_workflow(state)`
  - 运行 WorkflowAgent，并追加 audit_trail。

- `_human_review(state)`
  - 对外抛出 interrupt，等待人工审核动作。

- `_finalize(state)`
  - 汇总最终工作流返回结构。

- `_append_audit_entry(...)`
  - 统一创建标准化 audit_trail 记录。

## 13. MCP 层

### [backend/app/mcp/server.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/mcp/server.py)

文件作用：

- FastMCP Server 主入口。

重要函数：

- `search_knowledge_base(query, top_k=5)`
  - MCP 版知识检索。

- `get_ticket_detail(ticket_id)`
  - MCP 版工单详情读取。

- `list_open_tickets(limit=20)`
  - MCP 版开放工单列表。

- `search_similar_tickets(ticket_id, top_k=5)`
  - MCP 版相似工单查询。

- `get_analytics_overview()`
  - MCP 版 Dashboard 统计。

- `run_multi_agent_ticket_process(ticket_id, dry_run=True)`
  - MCP 版 Multi-Agent 工作流入口。

- `get_agent_audit_trail(ticket_id)`
  - MCP 版审计轨迹查询。

- `main()`
  - 启动 FastMCP server。

### [backend/app/mcp/resources.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/mcp/resources.py)

文件作用：

- 注册 MCP resources。

重要函数：

- `register_resources(mcp)`
  - 注册 `ticket://{ticket_id}`、`knowledge-doc://{doc_id}`、`analytics://overview`。

### [backend/app/mcp/prompts.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/mcp/prompts.py)

文件作用：

- 注册 MCP prompts。

重要函数：

- `register_prompts(mcp)`
  - 注册分类、回复、摘要、风险审查四类 prompt。

- `_load_prompt_template(file_name)`
  - 从 `backend/app/prompts/` 读取模板。

## 14. prompts 层

这一层没有 Python 函数，但很重要。

- [backend/app/prompts/classify_ticket.txt](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/prompts/classify_ticket.txt)
  - 工单分类 prompt 模板。

- [backend/app/prompts/generate_reply.txt](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/prompts/generate_reply.txt)
  - RAG 回复草稿生成 prompt 模板。

- [backend/app/prompts/risk_review.txt](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/prompts/risk_review.txt)
  - 风险审查 prompt 模板。

- [backend/app/prompts/summarize_ticket.txt](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/prompts/summarize_ticket.txt)
  - 工单摘要 prompt 模板。

## 15. 推荐阅读顺序

如果你准备真正读后端代码，建议按这个顺序：

1. [backend/app/main.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/main.py)
2. [backend/app/api/ai.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/api/ai.py)
3. [backend/app/services/ticket_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/ticket_service.py)
4. [backend/app/services/knowledge_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/knowledge_service.py)
5. [backend/app/services/rag_service.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/services/rag_service.py)
6. [backend/app/graphs/ticket_agent_graph.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/graphs/ticket_agent_graph.py)
7. [backend/app/graphs/ticket_multi_agent_graph.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/graphs/ticket_multi_agent_graph.py)
8. [backend/app/mcp/server.py](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/mcp/server.py)
9. [backend/app/agents/](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/agents)
10. [backend/app/repositories/](/E:/Bawa_Data/Xiangmu/My-platform/backend/app/repositories)

## 16. 最后一句话

如果把 `backend/app` 看成一条链路，那么它的核心阅读逻辑其实很清楚：

```text
API 收请求
-> Service 做业务
-> Repository 读写数据库
-> Graph / Agent 编排 AI 流程
-> MCP 把同一套能力对外开放
```

你后续如果愿意，我还能继续帮你做两件事：

- 把 `backend/app` 每个文件再拆成“逐函数源码讲解版”。
- 继续把剩余还没加注释的后端文件补上中文阅读注释。
