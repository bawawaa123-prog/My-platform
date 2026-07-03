# Project Handoff

## 1. 当前进度

- 当前完成到：Step 37 - README、架构图、演示脚本、简历包装（全部 37 Steps 已完成）
- 当前日期：2026-07-03
- 当前状态：可运行
- 最近一次变更：审计日志查询接口后端 + 测试 + 前端页面（2026-07-03）
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
  - 人工审核 approve / edit / reject 细分路径
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
