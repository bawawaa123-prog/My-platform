# Demo Script

## 1. 演示目标

这套脚本用于面试、录屏或现场展示，目标是在 10-15 分钟内让观众理解这不是普通聊天机器人，而是一个带业务闭环、RAG、人工审核、Multi-Agent 和 MCP 的企业级 AI 项目。

## 2. 演示前准备

### 本地启动

后端：

```bash
cd backend
D:\tools\anaconda\envs\py312\python.exe -m pip install -r requirements.txt
D:\tools\anaconda\envs\py312\python.exe -m app.db.init_db
D:\tools\anaconda\envs\py312\python.exe scripts/seed_data.py
D:\tools\anaconda\envs\py312\python.exe -m uvicorn app.main:app --reload --port 8010
```

前端：

```bash
cd frontend
npm install
npm run dev
```

可选 MCP 演示：

```bash
cd backend
D:\tools\anaconda\envs\py312\python.exe -m app.mcp.server
```

### 登录账号

- `admin@example.com / admin123`
- `agent@example.com / agent123`
- `viewer@example.com / viewer123`

## 3. 推荐主线案例

优先使用种子数据中的这张工单：

- `Enterprise renewal charged twice and finance team needs reversal`

原因：

- 主题足够企业化
- 同时能带出 RAG、风险审核、人工审核和 Multi-Agent
- 有知识库命中，也适合讲清 MCP 的价值

## 4. 10-15 分钟演示脚本

### 第 1 段：项目定位，30-60 秒

可以这样开场：

```text
这不是一个聊天机器人 Demo，而是一个企业智能工单平台。
系统核心是把工单流转、知识库检索、AI 回复建议、人工审核、Multi-Agent 分析和 MCP 对外能力放在一个闭环里。
```

### 第 2 段：登录和 Dashboard，1 分钟

操作：

1. 打开 `http://localhost:5173`
2. 用 `admin@example.com / admin123` 登录
3. 进入 Dashboard 展示指标卡和分布图

讲解重点：

- 平台不仅有 AI，还有运营视角
- Dashboard 展示工单总量、优先级分布、分类分布、AI adoption

### 第 3 段：工单列表，1 分钟

操作：

1. 进入 Tickets 页面
2. 指出当前队列中的支付、发票、退款等工单
3. 打开重复扣费那张工单

讲解重点：

- 这是企业真实业务对象，不是单轮对话
- 工单包含客户信息、优先级、状态、推荐部门和消息历史

### 第 4 段：AI 分类，1 分钟

操作：

1. 在 Ticket Detail 页面点击 `AI classify`
2. 展示分类、优先级、情绪、部门建议和 AI summary

讲解重点：

- 分类不是最终动作，只是下游自动化的输入
- 这里的结构化输出后续会被 workflow 和 Multi-Agent 复用

### 第 5 段：RAG 回复草稿，2 分钟

操作：

1. 点击 `Generate reply draft`
2. 展示 AI 回复草稿
3. 展示 `Sources / RAG references`
4. 点击知识文档跳转，展示 chunk 内容

讲解重点：

- 回复是基于知识库检索而来的，不是无依据生成
- 页面可以展示来源 chunk 和分数
- 如果命中弱，系统会保留低置信度信号，提醒人工谨慎审核

### 第 6 段：Human-in-the-loop，2 分钟

操作：

1. 在 Human Review 区域展示 `Approve / Edit / Reject`
2. 先演示 `Save edited approval`
3. 再解释 `Reject` 会记录原因

讲解重点：

- 系统设计上禁止 AI 直接发送客户回复
- 人工审核是安全边界的一部分
- 审核结果会写回 suggestion 状态和审计记录

### 第 7 段：Multi-Agent 时间线，3 分钟

操作：

1. 点击 `Run multi-agent analysis`
2. 展示各个 Agent 卡片：
   `Supervisor / Triage / Knowledge / Similar Case / Reply / Risk / Workflow`
3. 展示 `Audit Trail` 时间线

讲解重点：

- 单个大模型输出很难解释，Multi-Agent 可以拆分职责
- `KnowledgeAgent` 负责知识检索，`SimilarCaseAgent` 负责历史案例，`RiskAgent` 负责风控
- `audit_trail` 让每一步都可以被展示、调试和审计

### 第 8 段：Knowledge 页面，1 分钟

操作：

1. 进入 Knowledge 页面
2. 展示文档列表、状态、搜索框
3. 搜索 `duplicate charge reversal`
4. 打开一个文档详情展示 chunk

讲解重点：

- 知识库处理链路完整：上传、切分、embedding、索引、搜索
- 这是 RAG 数据准备和运维视角的展示面

### 第 9 段：MCP 能力，1-2 分钟

操作：

1. 在终端运行：

```bash
cd backend
D:\tools\anaconda\envs\py312\python.exe scripts/test_mcp_client.py --ticket-id 1
```

2. 展示它会调用：
   `search_knowledge_base`
   `get_ticket_detail`
   `run_multi_agent_ticket_process`

讲解重点：

- 项目不只提供 HTTP API，也能作为 MCP Server 被外部 AI Client 使用
- 这让企业工单能力可以成为 AI 生态里的标准工具
- `dry_run=True` 默认开启，体现安全设计

## 5. 现场讲解要点

### 必讲亮点

- 这是企业业务系统，不是聊天机器人
- RAG 带引用来源
- AI 回复必须人工审核
- Multi-Agent 角色分工明确
- `audit_trail` 可解释
- MCP 可对外开放能力

### 可加分的工程点

- mock LLM 和 fake embedding 让项目在没有真实密钥时也能运行
- FastAPI、LangGraph、FastMCP 共用 service 层
- Docker Compose 已准备好默认 SQLite + mock 模式

## 6. 可能会被问到的问题

### 为什么要做 Multi-Agent，而不是一个 prompt 解决？

建议回答：

```text
企业工单场景里，不同决策点的关注点不同。
把分诊、知识检索、历史案例、回复生成、风险审核拆开后，更容易控制输出、定位问题，也更适合做审计和前端可视化。
```

### 为什么要保留人工审核？

建议回答：

```text
因为企业客服回复涉及退款、赔付、合规和承诺边界。
AI 适合生成建议，但不能绕过人工直接触达客户。
```

### MCP 的价值是什么？

建议回答：

```text
它让工单、知识库和 Multi-Agent 分析能力可以以标准协议被外部 AI Client 调用，
项目就不只是一个 Web 系统，而是一个可复用的 AI 工具平台。
```

## 7. 演示备选方案

如果主案例不合适，可以切换：

- 发票修正工单：更适合讲 Finance 流程和知识库命中
- 延迟激活退款工单：更适合讲 RiskAgent 和人工审核
- SSO 迁移账号问题：更适合讲“无知识库强命中时如何谨慎处理”

