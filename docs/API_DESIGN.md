# API Design

## 1. 设计原则

- API 层只负责请求与响应，不承载复杂业务逻辑
- 所有 AI、RAG、工单、Analytics 能力都通过 service 层复用
- 返回结构以“演示友好、前端可直接展示”为目标
- AI 建议和 MCP 写操作遵守安全边界，不直接执行高风险动作

## 2. 基础信息

- 本地后端默认地址：`http://localhost:8010`
- Docker Compose 后端默认地址：`http://localhost:8000`
- 鉴权方式：`Authorization: Bearer <token>`
- 健康检查：`GET /health`

## 3. Auth

### `POST /api/auth/login`

说明：用户登录并获取 JWT。

请求体：

```json
{
  "email": "admin@example.com",
  "password": "admin123"
}
```

返回：

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

### `GET /api/auth/me`

说明：返回当前登录用户。

## 4. Tickets

### `POST /api/tickets`

说明：创建工单。

请求体：

```json
{
  "title": "Enterprise renewal charged twice",
  "content": "The customer says the renewal was captured twice this morning.",
  "customer_name": "Lena Foster",
  "customer_email": "lena.foster@example.com",
  "category": "payment",
  "priority": "urgent",
  "source": "manual"
}
```

### `GET /api/tickets`

说明：获取工单列表。

### `GET /api/tickets/{ticket_id}`

说明：获取单个工单详情。

### `PATCH /api/tickets/{ticket_id}`

说明：更新标题、内容、分类、优先级、状态、指派人等字段。

### `GET /api/tickets/{ticket_id}/messages`

说明：获取工单消息记录。

### `POST /api/tickets/{ticket_id}/messages`

说明：追加工单消息。

### `GET /api/tickets/{ticket_id}/similar`

说明：查找已解决 / 已关闭的相似历史工单。

返回重点字段：

```json
[
  {
    "ticket_id": 12,
    "title": "Payment captured but order stayed pending",
    "content_preview": "The customer completed a card payment...",
    "similarity": 0.92,
    "resolution": "Re-ran order sync and restored access."
  }
]
```

## 5. Knowledge

### `POST /api/knowledge/upload`

说明：上传知识库文档，当前支持 `txt/md`。

表单字段：

- `file`
- `title`

### `GET /api/knowledge/docs`

说明：获取知识文档列表与处理状态。

### `GET /api/knowledge/docs/{doc_id}`

说明：获取单个知识文档详情。

### `GET /api/knowledge/docs/{doc_id}/chunks`

说明：获取文档 chunk 列表。

### `POST /api/knowledge/search`

说明：根据自然语言查询知识库。

请求体：

```json
{
  "query": "duplicate charge reversal",
  "top_k": 3
}
```

## 6. AI

### `POST /api/ai/tickets/{ticket_id}/classify`

说明：执行 AI 分类，返回分类、优先级、情绪、摘要和推荐部门。

返回结构：

```json
{
  "category": "payment",
  "priority": "urgent",
  "sentiment": "angry",
  "need_human": true,
  "summary": "Urgent duplicate-charge complaint on an enterprise annual renewal.",
  "recommended_department": "billing"
}
```

### `POST /api/ai/tickets/{ticket_id}/generate-reply`

说明：基于 RAG 生成回复草稿并保存为 `AISuggestion`。

### `GET /api/ai/tickets/{ticket_id}/suggestions`

说明：获取工单 AI 建议列表。

返回重点字段：

```json
[
  {
    "id": 3,
    "ticket_id": 1,
    "suggestion_type": "reply",
    "suggested_content": "We are validating the duplicate annual-renewal capture...",
    "sources_json": [
      {
        "doc_id": 1,
        "chunk_id": 4,
        "chunk_index": 0,
        "content_preview": "Duplicate charges are normally refundable...",
        "score": 0.87
      }
    ],
    "confidence": 0.87,
    "status": "draft"
  }
]
```

### `POST /api/ai/tickets/{ticket_id}/process`

说明：执行单流程 LangGraph 工作流。

### `POST /api/ai/tickets/{ticket_id}/process/start`

说明：执行带人工审核中断的单流程工作流，返回 `pending_review`。

### `POST /api/ai/tickets/{ticket_id}/process/resume`

说明：对中断工作流执行 `approve / edit / reject` 后恢复。

请求体：

```json
{
  "action": "edit",
  "run_id": "<workflow-id>",
  "final_content": "Human-edited final reply"
}
```

### `POST /api/ai/tickets/{ticket_id}/multi-agent-process/start`

说明：执行固定顺序 Multi-Agent 工作流，并在人工审核前暂停。

返回重点字段：

- `supervisor_result`
- `triage_result`
- `knowledge_result`
- `similar_case_result`
- `reply_result`
- `risk_result`
- `workflow_result`
- `audit_trail`

### `GET /api/ai/tickets/{ticket_id}/agent-runs`

说明：获取工单 Multi-Agent 运行记录。

### `GET /api/ai/agent-runs/{run_id}`

说明：获取单次运行详情。

## 7. Reviews

### `POST /api/reviews/{suggestion_id}/approve`

说明：批准 AI 草稿，`final_content = suggested_content`。

### `POST /api/reviews/{suggestion_id}/edit`

说明：保存人工编辑后的最终内容。

请求体：

```json
{
  "final_content": "We confirmed the duplicate capture and opened a billing reversal review."
}
```

### `POST /api/reviews/{suggestion_id}/reject`

说明：拒绝 AI 草稿并记录原因。

请求体：

```json
{
  "reject_reason": "Billing manager review is required before promising refund timing."
}
```

## 8. Analytics

### `GET /api/analytics/overview`

说明：返回运营概览。

返回重点字段：

```json
{
  "total_tickets": 12,
  "open_tickets": 4,
  "resolved_tickets": 6,
  "urgent_tickets": 2,
  "ai_suggestions_count": 5,
  "ai_approved_count": 2,
  "ai_adoption_rate": 0.4,
  "category_distribution": {
    "payment": 4,
    "invoice": 3
  },
  "priority_distribution": {
    "high": 4,
    "urgent": 2
  }
}
```

## 9. MCP Design

MCP 与 HTTP API 并存，但定位不同：

- FastAPI：面向前端页面和传统 HTTP 调用
- FastMCP：面向外部 AI Client / MCP Client

### MCP Tools

- `search_knowledge_base(query, top_k=5)`
- `get_ticket_detail(ticket_id)`
- `list_open_tickets(limit=20)`
- `search_similar_tickets(ticket_id, top_k=5)`
- `get_analytics_overview()`
- `run_multi_agent_ticket_process(ticket_id, dry_run=True)`
- `get_agent_audit_trail(ticket_id)`

### MCP Resources

- `ticket://{ticket_id}`
- `knowledge-doc://{doc_id}`
- `analytics://overview`

### MCP Prompts

- `classify_ticket_prompt`
- `generate_reply_prompt`
- `summarize_ticket_prompt`
- `risk_review_prompt`

## 10. 安全约束

- AI 回复草稿不能直接发送给客户
- 审核行为必须通过 review API
- MCP 写操作默认 `dry_run=True`
- 不暴露删除工单、删除知识库、直接发消息等高风险能力

