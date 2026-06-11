# AGENTS.md

本文件是给 Codex / AI 编程助手使用的项目执行规范。  
项目名称：**企业智能工单与知识库 Multi-Agent 平台**。

Codex 必须严格按照本文件和 `PROJECT_IMPLEMENTATION_PLAN.md` 执行，不允许跳步、不允许一次性实现多个阶段、不允许大规模重构无关代码。

---

## 1. 项目定位

这是一个用于简历和面试展示的企业级 AI 应用项目，不是普通聊天机器人。

最终目标：

```text
基于 FastAPI + RAG + LangGraph Multi-Agent + FastMCP 的企业智能工单处理平台
```

项目需要体现：

```text
Python 后端工程
企业业务系统建模
RAG 知识库检索
LLM 结构化输出
LangGraph 工作流
Multi-Agent 分工协作
Human-in-the-loop 人工审核
FastMCP 工具开放
审计日志
数据看板
Docker 部署
```

---

## 2. Codex 每次开始前必须阅读的文件

每次新会话开始，Codex 必须先阅读：

1. `AGENTS.md`
2. `PROJECT_IMPLEMENTATION_PLAN.md`
3. `docs/PROJECT_HANDOFF.md`，如果存在
4. 当前步骤涉及的代码文件

如果 `docs/PROJECT_HANDOFF.md` 不存在，说明项目尚未开始或交接文档缺失，应从 `PROJECT_IMPLEMENTATION_PLAN.md` 的 Step 00 开始或根据用户指定步骤继续。

---

## 3. 总执行原则

### 3.1 一次只做一个 Step

必须严格遵守：

```text
每次只实现 PROJECT_IMPLEMENTATION_PLAN.md 中的一个 Step。
```

禁止：

```text
一次实现多个 Step
提前实现后续功能
顺手重构无关文件
为了方便直接推翻已有结构
跳过验收标准
```

如果用户没有明确指定 Step，Codex 必须根据 `docs/PROJECT_HANDOFF.md` 判断下一步。

---

### 3.2 先读代码，再修改

每次动手前必须：

1. 阅读当前 Step 要求。
2. 阅读相关已有代码。
3. 判断当前项目状态。
4. 列出本次计划修改/新增文件。
5. 再进行代码修改。

不要凭空假设文件结构。

---

### 3.3 保持小步迭代

每个 Step 必须做到：

```text
目标明确
改动集中
可运行
可验证
可交接
```

如果发现当前 Step 过大，应拆成更小子任务，但仍然只围绕当前 Step，不提前实现后续 Step。

---

### 3.4 不允许破坏已有功能

修改前必须考虑已有接口和页面是否会被影响。

特别禁止：

```text
删除已存在的可用接口
修改已有 API 返回结构导致前端失效
删除已有测试账号
删除已有 mock 能力
删除 docs/PROJECT_HANDOFF.md
删除单 Agent 流程来替换 Multi-Agent 流程
```

后续升级时应保留旧功能，除非用户明确要求废弃。

---

### 3.5 新实现替换旧实现

如果某个功能或模块已经有了明确的新实现，并且新实现已经完整覆盖旧实现职责，则允许删除或覆盖旧实现，避免项目中长期并存多套重复逻辑，导致代码结构过于繁杂。

执行时必须遵守：

```text
先确认新实现已经覆盖旧实现的核心职责
先确认不会破坏当前 Step 验收范围内的接口、页面和演示链路
删除前要同步清理旧路由、旧 service、旧辅助函数、无用 schema、无用文档引用
交接文档中必须明确记录：删除了什么、为什么可以删除、是否有兼容性影响
如果旧实现仍然承担当前或后续 Step 必需的演示/兼容作用，则不能删除
```

禁止：

```text
新旧实现职责未对齐时仓促删除旧代码
只新增实现但长期保留无用旧实现，导致重复维护
未验证就删除当前仍被接口、前端、工作流或文档依赖的旧实现
```

---

### 3.6 上下文压缩前必须询问用户

如果会话上下文已经接近需要压缩的阶段，Codex 不得直接自行压缩上下文继续执行，而必须先询问用户如何处理当前对话。

必须明确给出以下选项：

```text
1. 压缩上下文背景后继续对话
2. 不压缩上下文背景，继续当前对话
3. 终止当前对话
```

执行要求：

```text
必须先说明当前已接近上下文容量限制
必须让用户明确选择后再继续
如果用户选择压缩上下文，再进行压缩并继续
如果用户选择不压缩，则按当前上下文继续，直到无法继续为止
如果用户选择终止，则停止当前对话
```

禁止：

```text
未告知用户就直接压缩上下文
未给出选项就自行决定继续或终止
把上下文压缩决定隐藏在普通执行说明里，不让用户明确感知
```

---

## 4. 架构约束

### 4.1 后端分层

后端必须遵守分层架构：

```text
api/             只处理 HTTP 请求和响应
schemas/         Pydantic 输入输出模型
models/          SQLAlchemy 数据模型
repositories/    数据库访问
services/        业务逻辑
agents/          单个 Agent 的职责封装
graphs/          LangGraph 编排
mcp/             FastMCP tools/resources/prompts
core/            配置、安全、权限
db/              数据库连接和初始化
```

禁止在 API 层直接写复杂业务逻辑。  
禁止在 Agent 中直接写复杂数据库查询。  
禁止在 MCP tools 中重复写业务逻辑。  

正确方式：

```text
API / MCP / Graph Node
    -> service
    -> repository
    -> database
```

---

### 4.2 业务逻辑复用

FastAPI、LangGraph、FastMCP 必须复用同一套 service 层。

正确结构：

```text
FastAPI endpoint
    -> TicketService

LangGraph node
    -> TicketService

FastMCP tool
    -> TicketService
```

错误结构：

```text
FastAPI 写一套查询
LangGraph 写一套查询
FastMCP 再写一套查询
```

---

### 4.3 Mock 优先，真实服务可替换

本项目必须保证没有真实 API Key 时也能运行。

必须保留：

```text
MockLLMClient
FakeEmbeddingProvider
```

真实大模型和真实 embedding 只能作为可配置实现，不允许成为项目启动的硬依赖。

---

### 4.4 AI 安全边界

企业场景下，AI 不允许直接执行高风险动作。

必须遵守：

```text
AI 只生成建议，不直接发送客户回复
AI 回复必须进入人工审核流程
MCP 写操作默认 dry_run=True
dry_run=False 时必须记录 audit_log
不暴露删除数据、直接关闭工单、直接发送客户消息等高风险 MCP tools
```

---

## 5. LangGraph 约束

### 5.1 先单流程，后 Multi-Agent

开发顺序必须是：

```text
业务系统
-> RAG
-> LangGraph 单 Agent 工作流
-> Human-in-the-loop interrupt
-> Multi-Agent 工作流
```

不要一开始就实现 Multi-Agent。

---

### 5.2 单 Agent 工作流

单 Agent 工作流第一版：

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

加入 interrupt 后：

```text
generate_reply
  -> human_review
  -> finalize
```

---

### 5.3 Multi-Agent 工作流

Multi-Agent 最终流程：

```text
START
  -> load_ticket
  -> supervisor
  -> triage
  -> knowledge
  -> similar_case
  -> reply
  -> risk
  -> workflow
  -> human_review
  -> finalize
  -> END
```

第一版 Multi-Agent 允许固定顺序，不要求复杂动态路由。

---

### 5.4 Agent 职责

每个 Agent 只做一件事：

```text
SupervisorAgent：总调度和汇总
TriageAgent：分类、优先级、情绪、摘要、推荐部门
KnowledgeAgent：知识库检索
SimilarCaseAgent：历史相似工单检索与总结
ReplyAgent：生成客服回复草稿和内部建议
RiskAgent：风险判断
WorkflowAgent：状态流转和派单建议
```

禁止一个 Agent 做所有事情。

---

### 5.5 audit_trail

Multi-Agent 每个 Agent 执行后都必须追加 audit_trail：

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

audit_trail 用于前端展示和面试讲解，是项目亮点，不能省略。

---

## 6. FastMCP 约束

### 6.1 FastMCP 定位

FastMCP 不是替代 FastAPI。

```text
FastAPI：给前端和普通 HTTP API 使用
FastMCP：给外部 AI Client / MCP Client 使用
```

二者必须复用 services。

---

### 6.2 MCP Tools 分级

第一批只允许实现只读 tools：

```text
search_knowledge_base
get_ticket_detail
list_open_tickets
search_similar_tickets
get_analytics_overview
```

第二批可以实现 Agent tool：

```text
run_multi_agent_ticket_process(ticket_id, dry_run=True)
get_agent_audit_trail(ticket_id)
```

默认 `dry_run=True`。

---

### 6.3 MCP 不允许暴露的高风险能力

禁止默认暴露：

```text
delete_ticket
delete_knowledge_doc
send_reply_to_customer
close_ticket_directly
approve_ai_reply_without_user
modify_user_role
```

如用户后续明确要求添加，也必须加权限、dry_run、audit_log 和人工确认。

---

### 6.4 MCP Resources 和 Prompts

后续阶段需要实现：

Resources：

```text
ticket://{ticket_id}
knowledge-doc://{doc_id}
analytics://overview
```

Prompts：

```text
classify_ticket_prompt
generate_reply_prompt
summarize_ticket_prompt
risk_review_prompt
```

---

## 7. 数据库与迁移约束

第一版可以使用 SQLite 和 `Base.metadata.create_all()`。

后续如引入 PostgreSQL/Alembic，必须单独作为一个 Step，不允许在无关 Step 中顺手引入。

数据库字段新增必须：

1. 更新 model。
2. 更新 schema。
3. 更新 service/repository。
4. 更新 seed data，如需要。
5. 更新交接文档。

---

## 8. 前端约束

前端以可演示为主，不追求复杂 UI。

必须优先实现：

```text
登录页
Dashboard
工单列表
工单创建
工单详情
知识库上传
知识库搜索
AI 建议审核
Multi-Agent 执行时间线
```

页面要简洁、稳定、适合录屏演示。

前端不得绕过后端业务规则。  
例如 AI 审核必须调用后端 review 接口，而不是前端直接改状态。

---

## 9. 环境变量和密钥

禁止写入真实密钥。

所有密钥必须通过 `.env`：

```text
LLM_PROVIDER
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
DATABASE_URL
SECRET_KEY
```

`.env.example` 只能放示例值。

Mock 模式必须可运行：

```text
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=fake
```

### 9.1 Python 环境约定

后续所有 Python 相关的依赖安装、脚本执行、服务启动和验证，默认统一使用以下 conda 环境：

```text
D:\tools\anaconda\envs\py312
```

推荐显式使用解释器路径：

```text
D:\tools\anaconda\envs\py312\python.exe
```

如需安装依赖，优先使用：

```text
D:\tools\anaconda\envs\py312\python.exe -m pip ...
```

除非用户明确要求使用其他 Python 环境，否则不要切换到系统 Python 或其他虚拟环境。

---

## 10. 每个 Step 的工作流程

每次执行 Step 必须遵守以下流程。

### 10.1 开始前

Codex 必须先输出或内部确认：

```text
当前执行 Step：Step XX - <名称>
本 Step 目标：
本 Step 验收标准：
计划新增/修改文件：
不会修改的范围：
```

### 10.2 修改中

必须：

```text
只改当前 Step 需要的文件
保持已有接口兼容
必要时补充最小测试或验证脚本
```

### 10.3 完成后

必须提供：

```text
本 Step 完成内容
新增/修改文件
如何验证
验证结果
已知问题
下一步建议
```

并且必须更新：

```text
docs/PROJECT_HANDOFF.md
```

---

## 11. 交接文档规范

`docs/PROJECT_HANDOFF.md` 是跨会话交接核心文档。  
每完成一步，必须更新它。  
如果文件不存在，必须创建。

推荐模板如下：

```markdown
# Project Handoff

## 1. 当前进度

- 当前完成到：Step XX - <步骤名称>
- 当前日期：
- 当前状态：可运行 / 部分可运行 / 阻塞
- 下一步应执行：Step XX+1 - <步骤名称>

## 2. 已完成内容概述

- ...
- ...
- ...

## 3. 本次 Step 详细记录

### Step 编号

Step XX

### Step 目标

...

### 实际完成内容

...

### 新增文件

- ...

### 修改文件

- ...

### 删除文件

- 无 / ...

### 数据库变化

- 新增表：
- 修改字段：
- 需要重新初始化数据库：是 / 否

### API 变化

- 新增：
- 修改：
- 删除：

### 前端变化

- ...

### AI / RAG / LangGraph / MCP 变化

- ...

## 4. 验证记录

### 执行过的命令

```bash
...
```

### 验证结果

- 成功：
- 失败：
- 未验证原因：

## 5. 当前已知问题

- ...

## 6. 下一步 Codex Prompt

```text
请继续执行 PROJECT_IMPLEMENTATION_PLAN.md 中的 Step XX+1：<步骤名称>。

要求：
1. 严格遵守 AGENTS.md。
2. 只完成本 Step，不要提前实现后续功能。
3. 开始前先阅读 PROJECT_IMPLEMENTATION_PLAN.md、AGENTS.md 和 docs/PROJECT_HANDOFF.md。
4. 列出计划修改文件。
5. 完成后更新 docs/PROJECT_HANDOFF.md。
```

## 7. 项目启动方式

### 后端

```bash
cd backend
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm run dev
```

### 测试账号

- admin@example.com / admin123
- agent@example.com / agent123
- viewer@example.com / viewer123
```

---

## 12. 验证优先级

每个 Step 至少要有一种验证方式。

优先级：

1. 自动化测试。
2. curl/API 手动测试。
3. 浏览器手动测试。
4. 导入模块 smoke test。

如果无法验证，必须在交接文档中说明原因。

---

## 13. 错误处理要求

API 错误必须返回清晰信息。

禁止：

```text
直接抛出未捕获异常
返回模糊的 500
吞掉异常不记录
```

LLM 或 Embedding 调用失败时：

```text
返回可理解错误
不导致服务崩溃
必要时 fallback 到 mock 或低置信度结果
```

---

## 14. 代码风格

Python：

```text
使用类型标注
函数职责单一
业务逻辑放 services
数据库操作放 repositories
Pydantic schema 和 SQLAlchemy model 分离
```

前端：

```text
React + TypeScript
API 请求集中在 src/api
页面组件保持清晰
不要在页面里写复杂业务规则
```

Prompt：

```text
Prompt 放 backend/app/prompts/
不要把长 prompt 硬编码在 service 函数里
```

---

## 15. 禁止事项

Codex 不得：

```text
一次性实现完整项目
跳过当前 Step
删除已有项目文档
把真实 API Key 写入代码
让 AI 直接发送客户回复
让 MCP 默认执行高风险写操作
破坏 Mock 模式
大规模重构无关代码
把所有逻辑写在 main.py
把所有 Agent 合并成一个大函数
删除旧单 Agent 流程以替换 Multi-Agent 流程
```

---

## 16. 当遇到不确定时

如果遇到不确定，不要乱猜大改。

处理方式：

1. 查看 `PROJECT_IMPLEMENTATION_PLAN.md`。
2. 查看 `docs/PROJECT_HANDOFF.md`。
3. 查看已有代码。
4. 做最小合理实现。
5. 在交接文档中记录假设。
6. 如果必须用户确认，在最终回复中明确说明。

---

## 17. 当前推荐执行顺序

必须按以下顺序：

```text
Step 00：创建项目根目录与基础文档
Step 01：初始化 FastAPI 后端最小服务
Step 02：初始化 React + TypeScript 前端
Step 03：后端分层架构与配置系统
Step 04：数据库初始化与基础 Base Model
Step 05：用户模型、密码哈希与 JWT 登录
Step 06：工单基础模型与 CRUD
Step 07：工单消息与审计日志基础
Step 08：知识库文档上传：txt/md
Step 09：文档切分 KnowledgeChunk
Step 10：EmbeddingProvider 抽象与 Fake Embedding
Step 11：向量存储与知识库搜索
Step 12：LLMService 抽象：Mock + OpenAI Compatible
Step 13：AI 工单分类
Step 14：RAG 回复草稿生成与 AISuggestion
Step 15：人工审核流程 Human-in-the-loop 基础版
Step 16：历史相似工单推荐
Step 17：LangGraph 单流程工作流
Step 18：LangGraph interrupt 人工审核
Step 19：Multi-Agent 第一版：Supervisor/Triage/Knowledge/Reply/Risk
Step 20：Multi-Agent audit_trail 与 AgentRunLog
Step 21：增加 SimilarCaseAgent
Step 22：增加 WorkflowAgent
Step 23：FastMCP 只读工具服务
Step 24：FastMCP 调用 Multi-Agent 工作流
Step 25：FastMCP Resources 与 Prompts
Step 26：FastMCP Client 测试脚本
Step 27：前端登录与基础布局
Step 28：前端工单列表、创建、详情
Step 29：前端知识库上传与搜索
Step 30：前端 AI 建议与人工审核
Step 31：前端 Multi-Agent 执行过程展示
Step 32：数据看板 Analytics
Step 33：后台任务：文档处理异步化
Step 34：种子数据与演示数据
Step 35：测试与质量检查
Step 36：Docker Compose 一键启动
Step 37：README、架构图、演示脚本、简历包装
```

---

## 18. Codex 每次最终回复格式

每次完成任务后，最终回复必须包含：

```markdown
## 完成情况

完成了 Step XX：<名称>

## 修改文件

- ...
- ...

## 验证方式

```bash
...
```

## 验证结果

- ...

## 交接文档

已更新 docs/PROJECT_HANDOFF.md

## 下一步

建议继续 Step XX+1：<名称>
```

如果没有更新交接文档，必须说明原因。

---

## 19. 当前项目最重要的简历亮点

开发时必须保护这些亮点：

1. 企业工单业务闭环。
2. RAG 检索企业知识库并返回引用来源。
3. AI 回复进入人工审核，不直接发送。
4. LangGraph 编排可控工作流。
5. Multi-Agent 角色分工明确。
6. audit_trail 记录每个 Agent 的执行过程。
7. FastMCP 对外暴露企业工具能力。
8. MCP 写操作 dry_run 默认开启。
9. 数据看板展示企业价值。
10. Docker 和 README 保证可交付。

---

## 20. 给新会话的启动提示词模板

如果开启新 Codex 会话，可以直接使用：

```text
请先阅读 AGENTS.md、PROJECT_IMPLEMENTATION_PLAN.md 和 docs/PROJECT_HANDOFF.md。

然后根据 PROJECT_HANDOFF.md 判断当前项目完成到哪一步，并继续执行下一步。

要求：
1. 严格遵守 AGENTS.md。
2. 一次只完成一个 Step。
3. 不要提前实现后续功能。
4. 开始前列出计划新增/修改文件。
5. 完成后给出验证方式。
6. 完成后必须更新 docs/PROJECT_HANDOFF.md。
```
