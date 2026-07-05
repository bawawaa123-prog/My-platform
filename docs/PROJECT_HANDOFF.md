# Project Handoff

## 1. 当前进度

- 当前完成到：所有 37 Steps 已完成；近期增强：工单列表筛选后端化、工单消息录入、Audit Log 查询页面、Review API RBAC、待审核 Suggestion 队列、Conversation history 清理（AI Reply 不再自动追加为 ticket message）、时区显示修复（datetime 序列化含 UTC 时区 + 前端统一 formatDateTime）
- 当前日期：2026-07-04
- 当前状态：可运行
- 最近一次变更：AI Reply / Multi-Agent 前端展示分离 — AISuggestion 新增 `source_workflow` 字段（single_agent / multi_agent）；Single-Agent RAG 模块只展示 single_agent suggestion；Multi-Agent 模块独立展示自己的草稿和审核入口；新增 Final Human-Reviewed Reply 独立卡片；修复 Multi-Agent 审核完成后重新进入页面结果丢失问题
- 下一步应执行：PROJECT_IMPLEMENTATION_PLAN 已完成；建议补做 Docker 实机验收或扩展自动化测试

## 2. 已完成内容概述

- 已完成 FastAPI 后端基础分层、认证鉴权、工单 CRUD、消息与审计日志
- 已完成知识库上传、切分、Fake Embedding、本地向量检索、RAG 回复草稿生成
- 已完成 AI 分类、人工审核接口、历史相似工单推荐、LangGraph 单流程与 interrupt 审核流
- 已完成 Multi-Agent 第一版、`audit_trail`、`AgentRunLog`、SimilarCaseAgent、WorkflowAgent
- 已完成 FastMCP tools / resources / prompts 与本地 MCP client 验证
- 已完成前端登录、基础布局、工单列表/创建/详情、审计日志查询页面、知识库上传/详情/搜索
- 已完成前端工单详情页中的 AI 建议审核闭环
- 已完成前端工单详情页中的 Multi-Agent 运行、Agent 输出展示与 `audit_trail` 时间线展示
- 已完成 Dashboard 真实 Analytics 看板：核心指标、分类/优先级分布和 AI 采纳率展示
- 已完成知识库文档异步处理：上传快速返回，后台完成切分、embedding 与索引，前端自动刷新状态
- 已完成可重复执行的演示数据脚本：知识库、历史工单、当前工单与 AI 建议 demo 数据可一键写入
- 已完成后端基础 pytest 与 6 个核心 smoke tests，覆盖 health、登录、工单 CRUD、知识库上传搜索、AI mock 分类和 RAG 回复草稿链路
- 已完成 Docker 化交付基础：后端镜像、前端镜像、Compose 编排、SQLite 默认持久化卷，以及可选 Postgres / Redis profile
- 已完成 Step 37 交付材料：完整 README、架构文档、API 设计文档、演示脚本和简历包装文案
- 已补充项目结构说明文档，覆盖项目目录、主要文件职责、技术栈和运行产物说明
- 已补充 backend/app 函数级说明文档，并为核心后端文件增加中文阅读注释

## 3. 本次 Step 详细记录

### 功能增强 (2026-06-24)：前端工单详情页添加沟通记录录入

#### 目标

在工单详情页的 Messages / Conversation history 区域增加消息录入表单，支持选择发送方类型并输入沟通内容，将新增消息通过后端 API 写入并即时刷新消息列表。

#### 实际完成内容

- 在 `frontend/src/api/tickets.ts` 中新增 `TicketMessageCreatePayload` 类型和 `addTicketMessage` API 函数
- 在 `frontend/src/pages/TicketDetailPage.tsx` 中新增消息录入 UI（sender_type 下拉选择 + textarea + Send 按钮）
- 实现 `handleSendMessage` 处理函数：空内容校验、API 调用、成功清空输入并刷新消息、错误提示
- 遵循已有页面风格、状态管理模式和错误处理模式，未修改无关代码

#### 新增文件

- 无

#### 修改文件

- `frontend/src/api/tickets.ts` — 新增 `TicketMessageCreatePayload` 类型和 `addTicketMessage` 函数
- `frontend/src/pages/TicketDetailPage.tsx` — 新增消息录入表单和发送处理逻辑
- `docs/PROJECT_HANDOFF.md` — 记录本次变更

#### 删除文件

- 无

#### 数据库变化

- 无

#### API 变化

- 新增：前端调用已存在的 `POST /api/tickets/{ticket_id}/messages` 接口（该接口由后端正 Step 07 实现）

#### 前端变化

- 工单详情页 Messages 面板新增消息录入表单（sender_type 选择 + 内容输入 + 发送按钮）
- 发送成功后自动清空输入并刷新消息列表
- 空内容提交和 API 失败均有对应的错误提示

#### AI / RAG / LangGraph / MCP 变化

- 无

#### 验证记录

- 执行 `npm run build`（TypeScript 编译 + Vite 构建），通过，0 错误
- 构建产物：dist/assets/index-BZBqgUOb.js (311.27 kB), dist/assets/index-BmliYFJ3.css (18.51 kB)

#### Phase 2 优化 (2026-06-24)：沟通记录模块 UI 优化

- 成功提示 Message sent successfully 增加 3 秒自动消失（useEffect + setTimeout + isMountedRef guard）
- 新增 `handleClearMessage` 清空函数：一键重置消息内容、错误和成功提示
- 表单与历史记录区域互换位置：录入表单在上，对话历史在下，更符合使用习惯
- 录入区标题改为 "Add communication record"，历史区单独显示 "Conversation history" 小标题
- 按钮样式优化：Send 按钮文字简化为 "Send"，新增 ghost-button 风格的 Clear 按钮，两按钮并排 flex 布局
- 重复验证 `npm run build`，通过，0 错误
- 构建产物：dist/assets/index-CbzzYKx8.js (311.73 kB), dist/assets/index-BmliYFJ3.css (18.51 kB)

#### 功能增强 (2026-06-26)：Multi-Agent resume 工作流闭环

- 补全 `POST /api/ai/tickets/{ticket_id}/multi-agent-process/resume` 端点，与单流程 resume 对称
- 在 `backend/app/schemas/ai.py` 新增 `AIMultiAgentProcessRead` 响应模型
- 在 `backend/app/graphs/ticket_multi_agent_graph.py`：
  - 新增 `resume()` 方法：校验 checkpoint、通过 `Command(resume=...)` 恢复图执行、持久化 AgentRunLog
  - 修复 `_human_review` 节点：resume 时通过 `ReviewService.apply_review_action()` 持久化审核结果到数据库
  - 更新 `_finalize` 节点：输出包含 `reviewed_suggestion`
- 在 `backend/app/graphs/ticket_multi_agent_state.py` 新增 `reviewed_suggestion` 状态字段
- 在 `backend/app/api/ai.py` 新增 resume 路由
- 前端 `frontend/src/api/ai.ts` 新增 `MultiAgentResumePayload`、`AIMultiAgentProcessRead` 类型和 `resumeMultiAgentProcess` API 函数
- 前端 `frontend/src/pages/TicketDetailPage.tsx`：
  - 新增 Multi-Agent 审核状态（isSubmittingMultiAgentReview、multiAgentReviewError/Success 等）
  - 新增三个审核处理函数：handleMultiAgentApprove、handleMultiAgentEdit、handleMultiAgentReject
  - 新增审核 UI：Draft reply 编辑框 + Reject reason 输入框 + Approve/Save edits/Reject 按钮
  - 审核完成后展示 Review Complete 卡片，显示审核状态和最终建议内容
- 验证：后端模块导入无报错，前端 `npm run build` 通过，0 错误
- 构建产物：dist/assets/index-BsB5kA7O.js (315.25 kB), dist/assets/index-BmliYFJ3.css (18.51 kB)

---

### Step 编号

Step 37

### Step 目标

补齐项目交付材料，让仓库具备完整的 README、架构说明、API 说明、演示脚本和简历包装内容，使项目既能启动，也能被快速理解、演示和用于面试表达。

### 实际完成内容

- 重写 `README.md`，补齐以下交付内容：
  - 项目背景、核心功能、技术栈
  - 系统架构图与关键业务流程
  - 本地启动、Docker Compose、MCP 使用说明
  - API 示例、演示数据说明、验证方式
  - 演示流程、简历包装、未来优化方向
- 新增 `docs/ARCHITECTURE.md`：
  - 补充系统分层、RAG 流程、Multi-Agent 流程、数据模型概览和安全设计
- 新增 `docs/API_DESIGN.md`：
  - 按 Auth / Tickets / Knowledge / AI / Reviews / Analytics / MCP 分组整理接口
- 新增 `docs/DEMO_SCRIPT.md`：
  - 提供 10-15 分钟面试 / 录屏演示脚本、推荐主线案例、现场讲解话术和常见问答
- 在 README 中明确保留并说明 Step 36 的 Docker 状态：
  - 默认 Compose 使用 SQLite + mock 模式
  - `postgres` / `redis` 是可选 profile
  - 当前机器尚未完成真实 `docker compose up --build` 验证，原因是 Docker daemon 未启动
- 本 Step 仅补充交付文档，不修改后端业务逻辑、前端页面或工作流实现

### 新增文件

- `docs/ARCHITECTURE.md`
- `docs/API_DESIGN.md`
- `docs/DEMO_SCRIPT.md`

### 修改文件

- `README.md`
- `docs/PROJECT_HANDOFF.md`

### 删除文件

- 无

### 数据库变化

- 新增表：无
- 修改字段：无
- 需要重新初始化数据库：否

### API 变化

- 新增：无
- 修改：无
- 删除：无

### 前端变化

- 无代码变化
- README 中补充了已实现页面和演示入口说明

### AI / RAG / LangGraph / MCP 变化

- 无产品能力变化
- 仅补充了现有 AI / RAG / LangGraph / MCP 能力的文档化说明与演示话术

### Step 37 后补充任务：项目结构说明文档

- 新增 `docs/PROJECT_STRUCTURE_GUIDE.md`
- 文档内容覆盖：
  - 项目整体结构
  - 根目录、后端、前端、文档、测试、脚本文件用途
  - 重要文件与关键运行信息
  - 第三方依赖、构建产物、上传文件、探针文件的目录级说明
- `README.md` 文档索引已增加该说明文档入口

### Step 37 后补充任务：后端函数说明与源码注释

- 新增 `docs/BACKEND_APP_FUNCTION_GUIDE.md`
- 文档内容覆盖：
  - `backend/app` 分层结构
  - API / service / graph / agent / mcp 的重要函数说明
  - 推荐阅读顺序
- 已为以下核心后端文件补充中文注释：
  - `backend/app/main.py`
  - `backend/app/api/auth.py`
  - `backend/app/api/ai.py`
  - `backend/app/api/knowledge.py`
  - `backend/app/services/ticket_service.py`
  - `backend/app/services/knowledge_service.py`
  - `backend/app/services/rag_service.py`
  - `backend/app/graphs/ticket_agent_graph.py`
  - `backend/app/graphs/ticket_multi_agent_graph.py`
  - `backend/app/mcp/server.py`
- 注释策略以”关键入口、关键流程、关键副作用”为主，避免把所有代码注释得过重

---

### 功能增强 (2026-07-02)：工单列表筛选后端化 + 前端对接

#### 目标

将工单列表筛选从”前端本地 `tickets.filter(...)`”升级为”后端 Query 参数过滤”，支持 status / priority / category 单独和组合过滤，并补充后端 pytest 测试和前端 API 对接。

#### 实际完成内容

- 修复 `ticket_repository.py` 的 `list_filtered` 方法，补充缺失的 `category` 参数（service 层已在传但 repository 未接收）
- 在 `test_tickets.py` 新增 6 个过滤测试：单 status / priority / category 过滤、组合过滤、非法参数 422、无参数基线
- 修改 `frontend/src/api/tickets.ts`，新增 `TicketListFilters` 类型，`listTickets` 支持可选的 `filters` 参数并通过 axios params 传给后端
- 修改 `frontend/src/pages/TicketsPage.tsx`：`useEffect` 依赖筛选条件变化时重新请求后端，删除本地 `filteredTickets` 变量
- 筛选控件保持不变；当筛选值为 `”all”` 时不传对应 Query 参数

#### 新增文件

- 无

#### 修改文件

- `backend/app/repositories/ticket_repository.py` — `list_filtered` 增加 `category` 参数
- `backend/tests/test_tickets.py` — 新增 6 个过滤测试
- `frontend/src/api/tickets.ts` — 新增 `TicketListFilters` 类型，`listTickets` 支持 filters
- `frontend/src/pages/TicketsPage.tsx` — `useEffect` 根据筛选条件重新请求，删除本地过滤逻辑
- `docs/PROJECT_HANDOFF.md` — 记录本次变更

#### 删除文件

- 无

#### 数据库变化

- 无

#### API 变化

- `GET /api/tickets` 已支持 `status` / `priority` / `category` 可选 Query 参数（后端此前已实现，本次补充 category 过滤并补齐测试）

#### 前端变化

- `TicketsPage` 筛选条件变化时发起新请求到 `/api/tickets?status=...&priority=...&category=...`
- 删除 `filteredTickets` 本地过滤变量，页面直接展示后端返回结果
- 筛选控件 UI 不变

#### AI / RAG / LangGraph / MCP 变化

- 无

#### 验证记录

- `python -m pytest tests/test_tickets.py -q`：7 passed（含 1 个原有 + 6 个新增）
- `python -m pytest -q`：12 passed（全部测试通过）
- `npm run build`：TypeScript 编译 + Vite 构建通过，0 错误
- 构建产物：dist/assets/index-D7C5mfYN.js (315.40 kB)

---

### Step 3 (2026-07-03)：审计日志查询接口后端 + 测试 + 前端页面

#### 目标

新增 Audit Log 查询接口后端实现（repository / service / API / schema + 11 个 pytest 测试），新增前端审计日志页面（AuditLogsPage.tsx）并接入后端接口。

#### 实际完成内容

**后端：**
- 修复 `schemas/audit_log.py` 中 `AuditLogRead` 的 `ticket_id` 字段（model 中不存在该字段，改用 `target_type` + `target_id`）
- 修复 API 中 tuple unpacking bug（service 返回 dict 而非 tuple）
- 修复 offset Query 参数 `ge=1` → `ge=0`（与分页接口一致）
- 修复 `AuditLogPage.limit` / `offset` 为 `int | None = None`（当 API 未传参时允许 None）
- 为 `target_id` / `user_id` Query 参数增加 `ge=1` 校验
- 新增 `backend/tests/test_audit_logs.py` 11 个测试：
  - 认证必须（401）
  - 创建工单后生成 audit_log 记录
  - action / target_type+target_id / user_id 过滤
  - limit/offset 分页与 offset 超 total 空页
  - 非法 limit / offset / target_id / user_id 返回 422

**前端：**
- 新增 `frontend/src/api/auditLogs.ts` — `AuditLogRead`、`AuditLogPage`、`AuditLogQueryParams` 类型 + `listAuditLogs` API 函数 + `AUDIT_LOG_ACTIONS` / `AUDIT_LOG_TARGET_TYPES` 常量
- 新增 `frontend/src/pages/AuditLogsPage.tsx`：
  - 四个筛选控件：action（下拉）、target_type（下拉）、target_id（数字输入）、user_id（数字输入）
  - 审计日志表格：ID、Action、Target Type、Target ID、User ID、Created At、Detail（可展开 JSON）
  - 分页（PAGE_SIZE=20、Previous/Next、Showing X-Y of Z）
  - 筛选变化时 offset 自动重置为 0
  - Loading / error / empty 状态
  - Refresh 按钮
- 注册路由 `/audit-logs` 在 `routes/index.tsx`
- 导航栏新增 "Audit Logs" 入口在 `AppLayout.tsx`

#### 新增文件

- `frontend/src/api/auditLogs.ts`
- `frontend/src/pages/AuditLogsPage.tsx`
- `backend/tests/test_audit_logs.py`

#### 修改文件

- `backend/app/schemas/audit_log.py` — `AuditLogRead` 删除 `ticket_id`、`AuditLogPage.limit`/`offset` 改为 `int | None`
- `backend/app/api/audit_logs.py` — 修复 tuple unpacking、offset `ge=0`、target_id/user_id 加 `ge=1`
- `frontend/src/routes/index.tsx` — 新增 `AuditLogsPage` 导入和 `/audit-logs` 路由
- `frontend/src/components/AppLayout.tsx` — 导航栏新增 "Audit Logs"
- `docs/PROJECT_HANDOFF.md` — 记录本次变更

#### 删除文件

- 无

#### 数据库变化

- 无（AuditLog 模型未修改）

#### API 变化

- 新增 `GET /api/audit-logs` — 支持 `action`/`target_type`/`target_id`/`user_id`/`limit`/`offset` Query 参数，返回 `AuditLogPage`

#### 前端变化

- 新增 `/audit-logs` 页面，含筛选、表格、分页、JSON Detail 展开
- 导航栏新增 "Audit Logs" 入口

#### AI / RAG / LangGraph / MCP 变化

- 无

#### 验证记录

- `python -m pytest tests/test_audit_logs.py -q`：11 passed
- `python -m pytest -q`：33 passed（全部 33 个后端测试通过）
- `npm run build`：TypeScript + Vite 构建通过，0 错误
- 构建产物：dist/assets/index-DSNw6pgp.js (321.30 kB)

---

### Step 4 (2026-07-03)：Review API 角色限制 + pytest 测试 + 前端联动

#### 目标

为 Review API 增加角色限制（admin/agent 可审核，viewer 403），补充 11 个 pytest RBAC 测试，前端隐藏 viewer 的审核按钮并处理 403 错误。

#### 后端变更

**检查中发现并修复的 Bug：**
- `backend/app/api/auth.py` 中 `require_reviewer` 的 role 白名单为 `{"admin", "reviewer"}`，应改为 `{"admin", "agent"}`（系统无 `reviewer` 角色）

**已确认正确的后端实现：**
- `backend/app/api/reviews.py` 中 approve / edit / reject 三个接口均已使用 `require_reviewer`
- `require_reviewer` 复用 `get_current_user`，未登录返回 401
- 403 detail 为 "Reviewer role required"
- ReviewService 业务逻辑未修改

#### 新增测试

- `backend/tests/test_reviews.py` — 11 个测试：
  - `test_admin_can_approve_suggestion` — admin approve 返回 200，status=approved
  - `test_admin_can_reject_suggestion` — admin reject 返回 200，status=rejected，reject_reason 正确
  - `test_agent_can_approve_suggestion` — agent approve 返回 200
  - `test_agent_can_edit_suggestion` — agent edit 返回 200，status=edited，final_content 正确
  - `test_viewer_cannot_review_suggestion` — 参数化覆盖 approve/edit/reject，全部返回 403，detail="Reviewer role required"
  - `test_unauthenticated_user_cannot_review_suggestion` — 参数化覆盖三个接口，全部返回 401
  - `test_viewer_rejected_by_rbac_does_not_change_suggestion_status` — 确认 viewer 403 后 suggestion status 仍为 draft，reviewed_by/reviewed_at 为空

#### 前端变更

- `frontend/src/pages/TicketDetailPage.tsx`：
  - 新增 `useAuth` 导入获取当前用户
  - 新增 `const canReview = user?.role === "admin" || user?.role === "agent"`
  - 单 Agent 审核区：`canReview` 时显示完整审核表单 + 按钮；非 `canReview` 时显示"当前角色仅可查看 AI 建议，不能执行审核操作。"
  - Multi-Agent 审核区：同样逻辑，review complete 结果对所有角色可见
  - 三个审核 handler（approve/edit/reject）catch 块增加 403 检测，显示"当前角色无审核权限。"

#### 新增文件

- `backend/tests/test_reviews.py`

#### 修改文件

- `backend/app/api/auth.py` — `require_reviewer` role 白名单 `reviewer` → `agent`
- `frontend/src/pages/TicketDetailPage.tsx` — useAuth + canReview + 条件渲染 + 403 错误处理
- `docs/PROJECT_HANDOFF.md` — 记录本次变更

#### 验证记录

- `python -m pytest tests/test_reviews.py -q`：11 passed
- `python -m pytest tests/test_reviews.py tests/test_ai.py -q`：13 passed
- `python -m pytest -q`：44 passed（全部测试通过）
- `npm run build`：TypeScript + Vite 构建通过，0 错误

---

#### 实际完成内容

- 修复 `ticket_repository.py` 缺少的 `from sqlalchemy import func` 导入（`count_filtered` 需要）
- 在 `ticket_service.py` 新增 `list_tickets_page` 方法，组合 `list_filtered` + `count_filtered`
- 在 `ticket_api.py` 新增 `GET /api/tickets/page` 路由，`limit` 默认 20（1-100），`offset` 默认 0（>=0），路由放在 `/{ticket_id}` 之前
- 保留旧 `GET /api/tickets` 接口不变
- 在 `test_tickets.py` 新增 10 个分页测试：响应结构、limit/offset 生效、过滤+分页组合、offset 超 total 空页、非法 limit/offset/status 422、旧接口不受影响
- 在 `frontend/src/api/tickets.ts` 新增 `TicketPage`、`TicketListPageParams` 类型和 `listTicketsPage` API 函数
- 重写 `frontend/src/pages/TicketsPage.tsx`：使用 `listTicketsPage` 替代全量 `listTickets`，新增 `offset`/`total` 状态，筛选变化时 `offset` 重置为 0，增加 Previous/Next 分页按钮，统计改为 Matching tickets / Open on current page / Current page items
- 在 `frontend/src/styles.css` 新增 `.pagination-bar` / `.pagination-info` 样式

#### 新增文件

- 无

#### 修改文件

- `backend/app/repositories/ticket_repository.py` — 补充 `func` import
- `backend/app/services/ticket_service.py` — 新增 `list_tickets_page` 方法
- `backend/app/api/tickets.py` — 新增 `GET /api/tickets/page` 路由、导入 `TicketPage`
- `backend/tests/test_tickets.py` — 新增 10 个分页测试
- `frontend/src/api/tickets.ts` — 新增 `TicketPage`、`TicketListPageParams` 类型和 `listTicketsPage`
- `frontend/src/pages/TicketsPage.tsx` — 接入分页接口，增加分页控件
- `frontend/src/styles.css` — 新增 `.pagination-bar` 样式
- `docs/PROJECT_HANDOFF.md` — 记录本次变更

#### 删除文件

- 无

#### 数据库变化

- 无

#### API 变化

- 新增 `GET /api/tickets/page` — 返回 `{ items, total, limit, offset }`，支持 `status`/`priority`/`category`/`limit`/`offset` 可选 Query 参数
- 旧 `GET /api/tickets` 接口保持 `list[TicketRead]` 不变

#### 前端变化

- TicketsPage 使用 `listTicketsPage` 分页请求，每页 10 条
- 筛选条件变化时 offset 重置为 0
- 新增 Previous / Next 分页按钮，首/末页自动禁用
- 统计面板文案更新为更准确的分页语境

#### AI / RAG / LangGraph / MCP 变化

- 无

#### 验证记录

- `python -m pytest tests/test_tickets.py -q`：17 passed（7 原有 + 10 新增）
- `python -m pytest -q`：22 passed（全部通过）
- `npm run build`：TypeScript + Vite 构建通过，0 错误

---

### Step 5 (2026-07-03)：新增待审核 AI Suggestion 队列接口（后端修复 + 测试 + 前端 PendingReviewsPage）

#### 目标

新增 `GET /api/reviews/pending-suggestions` 接口，返回人工审核待处理的 AI reply suggestion 列表（status=draft, suggestion_type=reply），并补充测试和前端待审核页面。

#### 后端变更

**检查后端实现时发现并修复的 Bug：**
- `backend/app/api/reviews.py`：
  - 缺少 `Query`、`PendingSuggestionRead`、`PendingSuggestionPage` 导入 — 补充
  - `offset` Query 参数 `ge=1` → `ge=0`（offset=0 是合法值）
  - `limit` Query 参数 default `None` → `20`，增加 `le=100` 校验
  - `ticket_id` Query 参数增加 `gt=0` 校验（ticket_id=0 返回 422）
- `backend/app/repositories/suggestion_repository.py`：
  - `list_pending_reply_suggestions` 使用 `.scalars()` 但 SELECT 包含两列 → 改为 `.execute().all()` + tuple unpacking
  - `count_pending_reply_suggestions` 返回 `list(result.all())` → 改用 `func.count()` + `.scalar()`
  - 缺少 `func`、`Ticket` 导入 — 补充

#### 新增测试

- `backend/tests/test_reviews.py` — 新增 10 个测试（共 24 个）：
  1. `test_list_pending_suggestions_requires_auth` — 未登录返回 401
  2. `test_list_pending_suggestions_returns_draft_reply_suggestions` — draft reply 出现在队列中，字段完整
  3. `test_list_pending_suggestions_excludes_reviewed_suggestions` — approved/edited/rejected 不出现
  4. `test_list_pending_suggestions_excludes_non_reply_suggestions` — classification 类型不出现
  5. `test_list_pending_suggestions_filters_by_ticket_id` — ticket_id 过滤有效
  6. `test_list_pending_suggestions_paginates_results` — limit/offset/total 分页正确
  7. `test_list_pending_suggestions_respects_offset` — 不同 offset 返回不同数据
  8. `test_list_pending_suggestions_offset_beyond_total_returns_empty_items` — offset=999 返回 []
  9. `test_list_pending_suggestions_invalid_query_returns_422` — limit=0/101、offset=-1、ticket_id=0 均返回 422
  10. `test_viewer_can_list_pending_suggestions_but_cannot_review` — viewer 可查看队列但不能 approve（403）

#### 前端变更

- **新增** `frontend/src/api/reviews.ts`：
  - `PendingSuggestionRead`、`PendingSuggestionPage`、`PendingSuggestionParams` 类型
  - `listPendingSuggestions(params)` 调用 `GET /reviews/pending-suggestions`
- **新增** `frontend/src/pages/PendingReviewsPage.tsx`：
  - 页面标题 "Pending Reviews / 待审核 AI 回复"
  - 表格展示：ID、Ticket（跳转链接）、Priority、Category、Status、Customer、Suggested Reply（可展开）、Confidence、Created At、Action（View ticket 按钮）
  - 分页：Previous/Next 按钮，显示 Showing X-Y of Z
  - Loading / error / empty 状态，空列表显示"暂无待审核 AI 回复"
  - 无 approve/edit/reject 按钮
  - `SuggestionPreview` 子组件：超过 120 字符可展开/收起
- **修改** `frontend/src/routes/index.tsx`：注册 `/pending-reviews` 路由
- **修改** `frontend/src/components/AppLayout.tsx`：导航栏新增 "Pending Reviews" 入口（Dashboard / Tickets / Pending Reviews / Audit Logs / Knowledge）

#### 新增文件

- `frontend/src/api/reviews.ts`
- `frontend/src/pages/PendingReviewsPage.tsx`

#### 修改文件

- `backend/app/api/reviews.py` — 修复 Query 参数默认值和校验
- `backend/app/repositories/suggestion_repository.py` — 修复 scalars→execute、count 返回类型
- `backend/tests/test_reviews.py` — 新增 10 个 pending-suggestions 测试
- `frontend/src/routes/index.tsx` — 注册 `/pending-reviews` 路由
- `frontend/src/components/AppLayout.tsx` — 导航栏新增 "Pending Reviews"
- `docs/PROJECT_HANDOFF.md` — 记录本次变更

#### 删除文件

- 无

#### 数据库变化

- 无

#### API 变化

- 新增 `GET /api/reviews/pending-suggestions` — 支持 `ticket_id`(gt=0)/`limit`(ge=1,le=100,default=20)/`offset`(ge=0,default=0)，返回 `PendingSuggestionPage`
- 查看队列使用 `get_current_user`（登录即可），审核操作使用 `require_reviewer`（admin/agent 仅限）

#### 前端变化

- 新增 `/pending-reviews` 页面，含待审核队列表格、可展开建议内容、分页
- 导航栏新增 "Pending Reviews" 入口

#### AI / RAG / LangGraph / MCP 变化

- 无

#### 验证记录

- `python -m pytest tests/test_reviews.py -q`：24 passed（11 原有 + 10 新增 + 3 参数化变体）
- `python -m pytest tests/test_reviews.py tests/test_ai.py -q`：26 passed
- `python -m pytest -q`：57 passed（全部 57 个后端测试通过）
- `npm run build`：TypeScript + Vite 构建通过，0 错误
- 构建产物：dist/assets/index-mBI5VIaG.js (326.25 kB), dist/assets/index-DXM2iwGS.css (18.78 kB)

---

### Step 6 (2026-07-03)：审核 AI Suggestion 后追加 ticket message（测试 + 前端消息刷新）

#### 目标

当 admin/agent 执行 approve 或 edit 审核操作时，后端自动追加一条 ticket message 记录审核动作和最终回复内容。补充 6 个 pytest 测试验证消息追加逻辑，并修改前端 TicketDetailPage 在审核完成后自动刷新消息列表。

#### 后端确认

- `backend/app/services/review_service.py` 已正确实现 `_append_review_message` 方法：
  - 复用 `TicketService.add_ticket_message`，sender_type="agent"，内容为审核说明（approve: "AI draft approved. Final reply: {final_content}"; edit: "AI draft edited. Final reply: {final_content}"）
  - `approve_suggestion` 和 `edit_suggestion` 调用 `_append_review_message`
  - `reject_suggestion` 不追加 ticket message
- 确认无循环依赖问题

#### 新增测试

- `backend/tests/test_reviews.py` — 新增 6 个测试（共 30 个）：
  - `test_approve_suggestion_appends_ticket_message` — approve 后 ticket 有一条消息
  - `test_approve_suggestion_with_custom_content_appends_custom_message` — approve 时传 final_content 可在消息内容中体现
  - `test_edit_suggestion_appends_ticket_message_with_final_content` — edit 后 ticket 有一条消息含编辑后内容
  - `test_reject_suggestion_does_not_append_ticket_message` — reject 后 ticket 无新增消息
  - `test_reviewed_suggestion_cannot_append_duplicate_message` — 已审核的 suggestion 再次 approve 不追加重复消息
  - `test_viewer_cannot_append_ticket_message_by_reviewing` — viewer 403 不修改 suggestion 状态也不追加消息
- 新增辅助函数：`list_ticket_messages`、`create_draft_reply_suggestion`
- DetachedInstanceError 处理：`suggestion_id` 在内 `with db:` 块捕获

#### 前端变更

- `frontend/src/pages/TicketDetailPage.tsx`：
  - 新增 `loadMessages()` 辅助函数，通过 `listTicketMessages(ticketId)` 刷新消息列表
  - `handleApproveSuggestion` — approve 成功后调用 `void loadMessages()`
  - `handleEditSuggestion` — edit 成功后调用 `void loadMessages()`
  - `handleMultiAgentApprove` — 在 `Promise.all` 中加入 `loadMessages()`
  - `handleMultiAgentEdit` — 在 `Promise.all` 中加入 `loadMessages()`
  - `handleRejectSuggestion` / `handleMultiAgentReject` — 不追加消息，无需刷新

#### 新增文件

- 无

#### 修改文件

- `backend/tests/test_reviews.py` — 新增 6 个 Step 6 测试
- `frontend/src/pages/TicketDetailPage.tsx` — 新增 `loadMessages()`、审核 handler 增加消息刷新
- `docs/PROJECT_HANDOFF.md` — 记录本次变更

#### 删除文件

- 无

#### 数据库变化

- 无（复用工单消息表）

#### API 变化

- 无（复用已有 review 接口，后端逻辑已在 Step 6 之前实现）

#### 前端变化

- 单 Agent 审核：approve/edit 后消息列表自动刷新
- Multi-Agent 审核：approve/edit 后消息列表自动刷新
- reject 不追加消息，因此不需要刷新

#### AI / RAG / LangGraph / MCP 变化

- 无

#### 验证记录

- `python -m pytest tests/test_reviews.py -q`：30 passed（24 原有 + 6 新增）
- `python -m pytest -q`：63 passed（全部后端测试通过）
- `npm run build`：TypeScript + Vite 构建通过，0 错误
- 构建产物：dist/assets/index-BmyZl1eX.js (329.32 kB), dist/assets/index-CzLdNN7M.css (21.33 kB)

---

### Conversation history 清理 (2026-07-04)：AI Reply 不再自动追加为 ticket message

#### 背景

此前 approve / edit AI Suggestion 时，后端 ReviewService 会通过 `_append_review_message` 自动将 final_content 作为 `sender_type="agent"` 的 ticket message 写入 Conversation history，导致：

- Conversation history 混入 AI 审核记录，无法区分真实沟通记录与系统自动追加内容
- 前端用户在 textarea 中编辑内容后点击 "Approve as drafted" 主按钮，后端只保存原始 AI 的 `suggested_content`，忽略用户编辑
- AI Reply 卡片始终显示 `suggested_content`，未区分 Original AI draft 和 Final reviewed reply

#### 变更内容

**后端 — `backend/app/services/review_service.py`：**

- `approve_suggestion`：移除 `_append_review_message` 调用，保留 status/reviewed_by/reviewed_at/final_content/audit_log 保存
- `edit_suggestion`：移除 `_append_review_message` 调用，保留同上的审核逻辑
- 删除 `_append_review_message` 方法（不再使用）
- 清理不再需要的导入：`TicketMessageCreate`、`TicketService`

注意：`final_content` 仍然正确保存到 `ai_suggestions` 表，审核结果未丢失。

**前端 — `frontend/src/pages/TicketDetailPage.tsx`：**

Goal 2 — 区分 Original AI draft 和 Final reviewed reply 显示：
- draft 状态：显示 "Original AI draft" 标签 + `suggested_content`
- approved/edited 状态：显示 "Final reviewed reply" 标签 + `final_content ?? suggested_content`
- 如果 `final_content` 与 `suggested_content` 不同，增加折叠的 "View Original AI draft" 方便对比

Goal 3 — 修复 approve 按钮提交 textarea 内容：
- `handleApproveSuggestion`：读取 `reviewDraftContent.trim()`，传给 `approveSuggestion(id, { final_content })`，空内容时提示错误
- `handleMultiAgentApprove`：读取 `multiAgentReviewDraftContent.trim()`，传给 `resumeMultiAgentProcess(..., { final_content })`，空内容时提示错误
- 按钮文案从 "Approve as drafted" 改为 "Approve current reply"，避免用户误以为仅提交原文

#### 测试更新

**`backend/tests/test_reviews.py`（6 个测试变更）：**
- `test_approve_suggestion_does_not_append_ticket_message` — 验证 approve 后无新增 ticket message
- `test_approve_suggestion_with_custom_content_saves_final_content` — 验证自定义 final_content 正确保存且无 message
- `test_edit_suggestion_does_not_append_ticket_message` — 验证 edit 后无新增 ticket message
- `test_reject_suggestion_does_not_append_ticket_message` — 保持不变（原已正确）
- `test_reviewed_suggestion_cannot_be_reviewed_again` — 简化为只验证 status 变更而非 message 重复
- `test_viewer_review_does_not_affect_suggestion` — 更名为更准确的描述

**`backend/tests/test_ai.py`（2 个测试变更）：**
- `test_multi_agent_resume_approve_completes_run_without_ticket_message` — 验证 approve 后无 message
- `test_multi_agent_resume_edit_saves_final_content_without_ticket_message` — 验证 edit 后无 message

#### 新增文件

- 无

#### 修改文件

- `backend/app/services/review_service.py` — 删除 `_append_review_message` 调用和方法，清理导入
- `frontend/src/pages/TicketDetailPage.tsx` — 修复 AI Reply 卡片显示和 approve 提交内容
- `backend/tests/test_reviews.py` — 6 个测试改为验证不追加 ticket message
- `backend/tests/test_ai.py` — 2 个测试改为验证 Multi-Agent 不追加 ticket message
- `docs/PROJECT_HANDOFF.md` — 记录本次变更

#### 删除文件

- 无

#### 数据库变化

- 无（仅修改业务层逻辑）

#### API 变化

- 无（复用已有 review / multi-agent resume 接口）

#### 前端变化

- AI Reply 卡片根据 status 显示不同标签和内容
- "Approve current reply" 主按钮现在提交 textarea 内容作为 final_content
- Multi-Agent 的 "Approve current reply" 按钮同样提交 textarea 内容

#### AI / RAG / LangGraph / MCP 变化

- ReviewService 不再自动追加 ticket message
- Multi-Agent `_human_review` → `apply_review_action` 链路上层调用不受影响

#### 验证记录

- `python -m pytest -q`：71 passed（全部后端测试通过）
- `npm run build`：TypeScript + Vite 构建通过，0 错误
- 手动验证步骤：
  1. 创建工单 → 生成 AI Reply draft → 在 textarea 输入 "你好" → 点击 "Approve current reply" → 确认 Final reviewed reply 显示 "你好"，Conversation history 无新增记录
  2. 在 "Add communication record" 发一条消息 → 确认消息出现在 Conversation history
  3. 运行 Multi-Agent → 审核通过 → 确认 Conversation history 无自动追加记录

---

### 时区显示修复 (2026-07-04)：所有 datetime 字段序列化含 UTC 时区信息 + 前端统一 formatDateTime

#### 背景

`reviewed_at` 等 datetime 字段在前端显示时比本地时间（UTC+8）少 8 小时。根因是双层的：

- **后端**：SQLite 存储 UTC 时间，但 SQLAlchemy 返回的可能是 naive datetime（无 tzinfo）。Pydantic v2 序列化 naive datetime 时不追加 `+00:00`，导致 JSON 中的时间字符串没有时区后缀。
- **前端**：`new Date("2026-07-04T12:17:00")` 将不带时区的字符串解释为**本地时间**（UTC+8），因此 12:17 UTC 显示为 12:17 CST（本应为 20:17 CST）。

#### 后端变更

1. **新增 `backend/app/utils/datetime_utils.py`**：
   - `ensure_utc(value)`：Pydantic `BeforeValidator`，naive datetime → 追加 `timezone.utc`，aware datetime 保持不变，None 透传
   - `UTCDatetime`：`Annotated[datetime, BeforeValidator(ensure_utc)]`，可作为 Pydantic schema 字段类型

2. **所有 schema 文件中的 datetime 字段替换为 UTCDatetime**：
   - `schemas/ticket.py`：`TicketRead` — `created_at` / `updated_at` / `closed_at`
   - `schemas/ticket_message.py`：`TicketMessageRead` — `created_at` / `updated_at`
   - `schemas/ai.py`：`AIReplyDraftRead` / `AIMultiAgentPendingReviewRead` / `AIMultiAgentProcessRead` — `created_at` / `updated_at` / `reviewed_at`
   - `schemas/review.py`：`PendingSuggestionRead` / `SuggestionReviewResponse` — `created_at` / `updated_at` / `reviewed_at`
   - `schemas/agent.py`：`AgentRunLogRead` — `created_at` / `updated_at`
   - `schemas/audit_log.py`：`AuditLogRead` — `created_at`
   - `schemas/knowledge.py`：`KnowledgeChunkRead` / `KnowledgeDocRead` — `created_at` / `updated_at`
   - `schemas/user.py`：`UserRead` — `created_at` / `updated_at`

#### 前端变更

1. **新增 `frontend/src/utils/date.ts`**：
   - `parseApiDateTime(value)`：解析 API 返回的 datetime 字符串。如果已是 aware（带 `Z` 或 `+/-HH:MM`），直接 `new Date()`；否则（naive 字符串）先追加 `Z` 再 `new Date()`，确保 JS 将其解释为 UTC 而非本地时间。无效值返回 `null`。
   - `formatDateTime(value)`：统一格式化函数，处理 `null`/空值返回 "Not available"，使用 `Intl.DateTimeFormat("zh-CN")` 按本地时区显示。
   - `parseApiDateTime` 内部检测正则：`/[Z+-]\d{2}:\d{2}$/` 或 `.endsWith("Z")`

2. **删除 6 个页面的本地 `formatDateTime` 定义，统一导入 `formatDateTime`**：
   - `AuditLogsPage.tsx`
   - `KnowledgeDetailPage.tsx`
   - `KnowledgePage.tsx`
   - `PendingReviewsPage.tsx`
   - `TicketDetailPage.tsx`（原特有 null 保护 → 内置在工具函数中）
   - `TicketsPage.tsx`

#### 测试

1. **新增 `backend/tests/test_datetime_utils.py`**（5 个测试）：

   - `test_ensure_utc_preserves_aware_datetime` — aware datetime 时区信息不丢失
   - `test_ensure_utc_adds_utc_to_naive` — naive datetime 自动追加 UTC
   - `test_ensure_utc_handles_none` — None 透传
   - `test_utcdatetime_serializes_with_timezone` — 创建工单返回的 `created_at` 包含 `+00:00` 或 `Z`
   - `test_ticket_list_returns_utc_datetimes` — 工单列表页中 `created_at` / `updated_at` 均含时区信息

#### 新增文件

- `backend/app/utils/__init__.py`
- `backend/app/utils/datetime_utils.py`
- `frontend/src/utils/date.ts`
- `backend/tests/test_datetime_utils.py`

#### 修改文件

- `backend/app/schemas/ticket.py` — datetime → UTCDatetime
- `backend/app/schemas/ticket_message.py` — datetime → UTCDatetime
- `backend/app/schemas/ai.py` — datetime → UTCDatetime
- `backend/app/schemas/review.py` — datetime → UTCDatetime
- `backend/app/schemas/agent.py` — datetime → UTCDatetime
- `backend/app/schemas/audit_log.py` — datetime → UTCDatetime
- `backend/app/schemas/knowledge.py` — datetime → UTCDatetime
- `backend/app/schemas/user.py` — datetime → UTCDatetime
- `frontend/src/pages/AuditLogsPage.tsx` — 移除本地 formatDateTime，导入统一函数
- `frontend/src/pages/KnowledgeDetailPage.tsx` — 同上
- `frontend/src/pages/KnowledgePage.tsx` — 同上
- `frontend/src/pages/PendingReviewsPage.tsx` — 同上
- `frontend/src/pages/TicketDetailPage.tsx` — 同上
- `frontend/src/pages/TicketsPage.tsx` — 同上
- `docs/PROJECT_HANDOFF.md` — 记录本次变更

#### 删除文件

- 无

#### 数据库变化

- 无（仅影响序列化 / 显示层，模型和存储未变）

#### API 变化

- 无（请求/响应结构不变，新增时区后缀 `+00:00`）

#### 验证记录

- `python -m pytest -q`：76 passed（5 个新增时区测试 + 71 个原有，全部通过）
- `npm run build`：TypeScript + Vite 构建通过，0 错误
- 构建产物：dist/assets/index-Da0u8cOD.js (330.16 kB), dist/assets/index-CzLdNN7M.css (21.33 kB)

---

### TimestampMixin 时区修复 (2026-07-04)：utc_now() + Python 级 UTC 默认值

#### 背景

时区显示修复后，AI Reply Suggestion card 中 `reviewed_at` 显示正确（20:47），但 `created_at`/`updated_at` 显示错误（04:46，比预期多 8 小时）。

根因为 **TimestampMixin** 使用 `server_default=func.now()`，这会在数据库层求值。在 SQLite 下 `CURRENT_TIMESTAMP` 虽然返回 UTC，但 SQLAlchemy 读取时获得的是 naive datetime。当 naive datetime 通过 `UTCDatetime` 序列化为 `+00:00` 后缀时，前端 `new Date()` 将其解释为本地时间（UTC+8），导致实际为 UTC 的时间被额外加了 8 小时显示。

而 `reviewed_at` 在 service 层通过 Python 的 `datetime.now(UTC)` 显式生成，虽然后经 SQLite 存储丢失 tzinfo 但被 `UTCDatetime` 修复。根源在于两类时间字段使用了不同的时间来源。

#### 变更内容

**后端 — `backend/app/db/base.py`：**

- 新增 `utc_now()` 函数：`return datetime.now(timezone.utc)`，返回显式 aware UTC datetime
- `TimestampMixin.created_at`：`server_default=func.now()` → `default=utc_now`
- `TimestampMixin.updated_at`：`server_default=func.now(), onupdate=func.now()` → `default=utc_now, onupdate=utc_now`
- 删除不再需要的 `from sqlalchemy import func`

**后端 — `backend/app/models/ticket_embedding.py`：**

- `created_at`：`server_default=func.now()` → `default=utc_now`（从 `base.py` 导入 `utc_now`）
- 删除不再需要的 `from sqlalchemy import func`

**新增测试 `backend/tests/test_datetime_utils.py`（新增 4 个测试，共 9 个）：**

1. `test_utc_now_returns_aware_datetime` — 验证 `utc_now()` 返回 aware UTC datetime
2. `test_suggestion_timestamps_all_utc` — 端到端：创建工单 → 生成 reply → approve → 验证 created_at/updated_at/reviewed_at 全部含 `Z` 后缀，三者均在同一时间窗口内，且 updated_at >= created_at、reviewed_at >= created_at
3. `test_suggestion_list_returns_utc_timestamps` — `GET /api/reviews/pending-suggestions` 返回的 created_at/updated_at 均含 `Z` 后缀

#### 前端变化

- 无（前端 `formatDateTime`/`parseApiDateTime` 已在时区显示修复阶段完成）

#### 新增文件

- 无

#### 修改文件

- `backend/app/db/base.py` — 新增 `utc_now()`，TimestampMixin 使用 `default=utc_now` 和 `onupdate=utc_now`
- `backend/app/models/ticket_embedding.py` — `created_at` 使用 `default=utc_now`
- `backend/tests/test_datetime_utils.py` — 新增 4 个时区一致性测试
- `docs/PROJECT_HANDOFF.md` — 记录本次变更

#### 删除文件

- 无

#### 数据库变化

- 无（仅影响 Python ORM 层默认值生成，不修改数据库 schema）
- **注意**：已有数据库记录的 `created_at`/`updated_at` 不会自动修复，如遇时间显示异常需重建数据库

#### API 变化

- 无（响应结构不变，但所有 datetime 字段现在统一使用 Python UTC 时间源）

#### 要点总结

- `utc_now()` 返回 `datetime.now(timezone.utc)` 作为唯一的 UTC 时间源
- SQLite 存储后 tzinfo 虽被丢弃，但 `UTCDatetime` 序列化时追加 `+00:00`
- 前端 `parseApiDateTime` 检测到 `Z`/`+00:00` 后缀，`new Date()` 正确按 UTC 解析并显示为本地时间
- `updated_at` 的 `onupdate=utc_now` 在 Python flush 时求值，比 service 中的 `datetime.now(UTC)` 赋值晚约 1 微秒，但所有字段均在同一时间窗口内

#### 验证记录

- `python -m pytest -q`：79 passed（全部后端测试通过）
- `npm run build`：TypeScript + Vite 构建通过，0 错误
- 构建产物：dist/assets/index-Da0u8cOD.js (330.16 kB), dist/assets/index-CzLdNN7M.css (21.33 kB)

---

### AI Reply / Multi-Agent 前端展示分离 (2026-07-04)：source_workflow + TicketDetailPage 重构

#### 背景

原 TicketDetailPage 的 "AI Reply" 模块混用单 Agent 和 Multi-Agent 生成的回复草稿。单 Agent 通过 `generate-reply` 创建 `ai_suggestions`，Multi-Agent 的 ReplyAgent 也走 `rag_service._create_reply_suggestion` 落库到同一张表。前端 `listTicketSuggestions` 返回全部 reply 类型的 suggestion，取 `suggestions[0]` 作为 `latestSuggestion` 展示。结果：

- Multi-Agent 的草稿也出现在 "AI REPLY" 模块
- 退出工单详情页再进入，Multi-Agent 审核完成结果无法恢复（`loadAgentRuns` 只处理 `pending_review` 类型）
- 页面概念混乱，"AI REPLY" 和 "HUMAN REVIEW" 同时承载单 Agent 和 Multi-Agent

#### 变更内容

**后端 — `backend/app/models/ai_suggestion.py`：**

- 新增 `source_workflow` 字段：`Mapped[str] = mapped_column(String(50), nullable=False, default="single_agent", server_default="single_agent")`
- 可选值：`"single_agent"` | `"multi_agent"`

**后端 — `backend/app/schemas/ai.py`：**

- `AIReplyDraftRead` 新增 `source_workflow: str = "single_agent"`

**后端 — `backend/app/schemas/review.py`：**

- `PendingSuggestionRead` 和 `SuggestionReviewResponse` 新增 `source_workflow: str = "single_agent"`

**后端 — `backend/app/services/rag_service.py`：**

- `_create_reply_suggestion` 新增 `source_workflow: str = "single_agent"` 参数，创建 `AISuggestion` 时传入
- `generate_ticket_reply_from_context` 新增 `source_workflow` 参数，透传给 `_create_reply_suggestion`

**后端 — `backend/app/services/review_service.py`：**

- `list_pending_suggestions` 的 dict 中添加 `source_workflow`

**后端 — `backend/app/agents/reply_agent.py`：**

- ReplyAgent 调用 `generate_ticket_reply_from_context` 时传 `source_workflow="multi_agent"`

**前端 — `frontend/src/api/ai.ts`：**

- `AIReplyDraftRead` 新增可选字段 `source_workflow?: string`

**前端 — `frontend/src/pages/TicketDetailPage.tsx`（大规模重构）：**

1. **Single-Agent RAG 模块**（原 AI Reply 重命名）：
   - panel-tag: `AI Reply` → `Single-Agent RAG`
   - title: `Draft and human review` → `Single-agent reply draft`
   - button: `Generate reply draft` → `Generate single-agent draft`
   - 通过 `singleAgentSuggestions`（过滤 `source_workflow === "single_agent"`）展示，不再混入 Multi-Agent suggestion

2. **Final Human-Reviewed Reply 独立模块**（新增）：
   - panel-tag: `Final Review`, title: `Final human-reviewed replies`
   - 分别展示 Single-Agent final reviewed reply（status=approved/edited/rejected）
   - 和 Multi-Agent final reviewed reply（来自 `multiAgentFinalReviewedSuggestion`）
   - 明确标注 `Source: Single-Agent` / `Source: Multi-Agent`
   - 无 final review 时显示 `No final human-reviewed reply yet.`

3. **修复 `loadAgentRuns` 完成状态恢复**：
   - 新增 completed/finalized 识别逻辑：`latestRun.run_type === "multi_agent" && latestRun.status === "completed"` 时，从 `output_json.reviewed_suggestion` 恢复 `multiAgentResumeResult`
   - `multiAgentResult` 仍用于 pending_review 的继续审核

4. **Multi-Agent 模块兼容完成态**：
   - 空状态检查 `!multiAgentResult && !multiAgentResumeResult`
   - Summary grid 支持 `multiAgentResumeResult` 的 fallback 显示
   - Audit trail 从 `multiAgentResult ?? multiAgentResumeResult` 读取

5. **`buildAgentCards` 类型扩展**：接受 `AIMultiAgentPendingReviewRead | AIMultiAgentProcessRead`

#### 前端变化

- Single-Agent RAG 模块改名为 Single-Agent RAG，只展示单 Agent 建议
- Multi-Agent 模块在 pending_review 和 completed 状态都可展示
- 新增 Final Human-Reviewed Reply 卡片，同时展示单 Agent 和多 Agent 的最终审核结果
- Agent timeline 数据源兼容 pending 和 completed 两种 state

#### 数据库变化

- `ai_suggestions` 表新增 `source_workflow` 列（String(50), default="single_agent"）
- 旧数据兼容：`source_workflow` 缺失时按 `"single_agent"` 处理

#### API 变化

- 无（复用已有接口，`listTicketSuggestions`、`listPendingReviewSuggestions` 返回新增 `source_workflow` 字段）

#### AI / RAG / LangGraph / MCP 变化

- 半自动回复（单 Agent）创建的 suggestion 写入 `source_workflow="single_agent"`
- Multi-Agent ReplyAgent 创建的 suggestion 写入 `source_workflow="multi_agent"`

#### 验证记录

- `python -m pytest -q`：79 passed（全部后端测试通过）
- `npm run build`：TypeScript + Vite 构建通过，0 错误
- 构建产物：dist/assets/index-DpDZTJee.js (333.59 kB), dist/assets/index-CzLdNN7M.css (21.33 kB)

---

### source_workflow 数据库字段缺失修复 + 前端布局调整 (2026-07-04)

#### 根本原因

上一轮重构在 `AISuggestion` ORM 模型中新增了 `source_workflow` 列（含 `server_default`），但 MySQL 数据库的 `ai_suggestions` 表是之前用 `CREATE TABLE` 创建的，不含该列。SQLAlchemy 的 `Base.metadata.create_all()` 对已存在的表不执行 ALTER TABLE，因此模型与数据库结构不一致。任何查询 `ai_suggestions` 的 SELECT 语句都会因 MySQL 报 `(1054, "Unknown column 'ai_suggestions.source_workflow'")` 而失败。

报错链路：`listTicketSuggestions` → `list_reply_suggestions_by_ticket_id` → SQLAlchemy SELECT 包含 `source_workflow` → MySQL 报 1054 → ORM `OperationalError` → API 层 `except Exception as exc` 将原始 SQL 错误暴露给前端。

#### 新增/修改文件

**新增 — `scripts/sql/add_source_workflow_to_ai_suggestions.sql`**：
- MySQL 迁移 SQL 脚本，内容：`ALTER TABLE ai_suggestions ADD COLUMN source_workflow VARCHAR(50) NOT NULL DEFAULT 'single_agent'`
- 注释中包含 SQLite 兼容版本

**修改 — `backend/app/db/init_db.py`**：
- 新增 `sync_ai_suggestion_source_workflow()` 函数
- 遵循项目已有的 `sync_*` 模式：使用 `inspect(engine)` 检查列是否存在，存在则跳过，否则执行 `ALTER TABLE`
- 在 `init_db()` 中调用，同步时机在 `sync_ai_suggestion_review_columns()` 之后

**修改 — `backend/app/api/ai.py`**：
- 新增 `import logging` + `logger = logging.getLogger(__name__)`
- 5 个 `except Exception as exc` 处理块改为 `logger.error(..., exc_info=True)` 记录完整异常栈，返回通用错误消息（如 `"Multi-agent workflow start failed. Please try again later."`），不再暴露原始 SQL/DB 细节给用户

**修改 — `frontend/src/pages/TicketDetailPage.tsx`**：
- Final Review 面板从 AI Agent Timeline 上方移到 Ticket Detail + Workflow 卡片下方（Single-Agent RAG 和 AI Classification 前面）
- 删除了旧位置的重复 Final Review 面板
- 最终页面顺序：Ticket Detail → Workflow Status → Final Review → Single-Agent RAG + AI Classification → AI Agent Timeline → Messages

#### 数据库变化

- `ai_suggestions` 新增 `source_workflow VARCHAR(50) NOT NULL DEFAULT 'single_agent'`
- 旧数据自动获得 `source_workflow = 'single_agent'`

#### API 变化

- 所有 AI 相关 endpoint 在异常时不再暴露原始 SQL/DB 错误的详细信息给前端，改为通用错误消息；完整错误栈写入 server log

#### 验证记录

- `python -m app.db.init_db`：成功，输出 `Initialized database for: mysql+pymysql://...`
- MySQL 验证：`DESCRIBE ai_suggestions` 显示 `source_workflow varchar(50) NO DEFAULT 'single_agent'`
- `python -m pytest -q`：79 passed（全部后端测试通过）
- `npm run build`：TypeScript + Vite 构建通过，0 错误
- 构建产物：dist/assets/index-D2vwLwHb.js (333.59 kB)（JS 体积增加 ~3.43 kB 来自 Final Review 模块搬迁）

#### 手动验证步骤

1. `D:\tools\anaconda\envs\py312\python.exe -m app.db.init_db` — 确保 migration 执行
2. 启动后端：`D:\tools\anaconda\envs\py312\python.exe -m uvicorn app.main:app --reload --port 8010`
3. 启动前端：`npm run dev`
4. 登录系统，进入任意工单详情页，确认不再出现 `Unknown column 'ai_suggestions.source_workflow'` 错误
5. 确认页面布局：Final Review 面板在 Ticket Detail 下方、Single-Agent RAG 上方
6. 点击 "Generate single-agent draft"，确认正常生成草稿
7. 点击 "Run multi-agent analysis"，确认 Multi-Agent 工作流正常启动

## 4. 验证记录

### 执行过的命令

```bash
Get-ChildItem -Path docs -Force | Select-Object Name,Mode,Length
Get-Item README.md | Select-Object Name,Length
Get-Content -Path README.md -Encoding utf8
Get-Content -Path docs\ARCHITECTURE.md -Encoding utf8
Get-Content -Path docs\API_DESIGN.md -Encoding utf8
Get-Content -Path docs\DEMO_SCRIPT.md -Encoding utf8
Get-Content -Path docs\PROJECT_STRUCTURE_GUIDE.md -Encoding utf8
Get-Content -Path docs\BACKEND_APP_FUNCTION_GUIDE.md -Encoding utf8
```

### 验证结果

- 成功：`README.md` 已重写并包含 Step 37 要求的核心交付内容
- 成功：`docs/ARCHITECTURE.md`、`docs/API_DESIGN.md`、`docs/DEMO_SCRIPT.md` 已创建
- 成功：`docs/PROJECT_STRUCTURE_GUIDE.md` 已新增，覆盖项目结构、主要文件职责和技术栈说明
- 成功：`docs/BACKEND_APP_FUNCTION_GUIDE.md` 已新增，覆盖 `backend/app` 重要函数级说明
- 成功：核心后端文件已补充中文注释，便于后续源码阅读
- 成功：文档内容已人工检查，覆盖启动说明、架构图、演示脚本和简历包装
- 未验证：本 Step 未涉及业务代码改动，因此未重新执行 `pytest`、前端构建或 Docker 启动命令
- 关联说明：Step 36 的 Docker 真实启动限制仍然存在，原因仍是本机 Docker daemon 未启动

## 5. 当前已知问题

- 当前代码层面的 Compose 配置已完成，但本机 Docker daemon 未运行，因此还缺一次真实容器启动验收
- 如需切换到 `postgres` profile，需要在根目录 `.env` 中将 `DATABASE_URL` 覆盖为：
  - `postgresql+psycopg://app:app@postgres:5432/enterprise_support_agent`
- 当前测试仍以后端 smoke tests 为主，尚未覆盖：
  - Multi-Agent 工作流
  - MCP server / MCP client 回归
  - Analytics 统计接口
- 已覆盖的测试包括：health、login、工单 CRUD（含分页和筛选）、知识库上传搜索、AI mock 分类和 RAG 回复草稿链路、Review API RBAC、Pending Suggestions 队列查询（24 个 review 测试 + 57 个总测试）
- 当前未加入前端 lint、组件测试或浏览器端 e2e 测试
- 当前知识检索仍基于 fake embedding + 本地 JSON 向量索引，适合演示，但语义命中质量仍偏基础
- 当前 Multi-Agent 使用 `InMemorySaver`，仅适合同一后端进程内演示；服务重启后暂停态不会保留

## 6. 下一步 Codex Prompt

```text
PROJECT_IMPLEMENTATION_PLAN.md 已全部完成。

要求：
1. 严格遵守 AGENTS.md。
2. 下一轮如果继续迭代，请先确认是要做收尾增强还是新需求开发。
3. 开始前先阅读 PROJECT_IMPLEMENTATION_PLAN.md、AGENTS.md 和 docs/PROJECT_HANDOFF.md。
4. 优先补做以下收尾项之一：
   - 在 Docker daemon 正常运行环境中完成真实 `docker compose up --build` 验证
   - 为 Multi-Agent / MCP / Analytics 增加自动化测试
   - 补充前端 lint、组件测试或 e2e 测试
5. 保留现有业务闭环、RAG、人工审核、Multi-Agent、MCP 和演示数据能力。
6. 完成后继续更新 docs/PROJECT_HANDOFF.md。
```

## 7. 项目启动方式

### 后端

```bash
cd backend
D:\tools\anaconda\envs\py312\python.exe -m pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
D:\tools\anaconda\envs\py312\python.exe -m app.db.init_db
D:\tools\anaconda\envs\py312\python.exe scripts/seed_data.py
D:\tools\anaconda\envs\py312\python.exe -m uvicorn app.main:app --reload --port 8010
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### Docker Compose

```bash
docker compose up --build
docker compose --profile postgres --profile redis up --build
```

### 测试账号

- admin@example.com / admin123
- agent@example.com / agent123
- viewer@example.com / viewer123
