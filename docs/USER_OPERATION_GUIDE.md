# 用户操作手册

## 1. 文档用途

这是一份面向项目使用者、演示者和第一次接触本系统的同学的小白操作手册。

你可以用它来完成以下事情：

- 第一次启动并进入系统
- 理解每个页面的作用
- 知道每个按钮、输入框、下拉框分别做什么
- 学会如何完整演示一条“企业工单 + RAG + AI 审核 + Multi-Agent”的业务闭环
- 在系统报错时快速排查最常见问题

本手册主要覆盖当前前端已经实现的页面：

- 登录页
- Dashboard 数据看板
- Tickets 工单列表
- Create Ticket 新建工单
- Ticket Detail 工单详情
- Knowledge 知识库页
- Knowledge Detail 知识文档详情页

---

## 2. 项目是什么

这个项目不是普通聊天机器人，而是一个企业智能工单平台。

它把企业常见的客服 / IT 支持 / 财务支持场景串成了一条完整业务链路：

1. 用户创建工单
2. 系统对工单做 AI 分类
3. 系统检索知识库生成回复草稿
4. 人工审核 AI 草稿
5. Multi-Agent 对工单做更完整的协作分析
6. Dashboard 展示整体业务数据和 AI 采纳情况

系统重点亮点：

- AI 回复不是直接发送，而是必须经过人工审核
- 知识库检索带来源引用，不是无依据瞎生成
- Multi-Agent 拆分为多个职责明确的 Agent
- `audit_trail` 可以展示每一步 Agent 执行过程

---

## 3. 使用前准备

### 3.1 访问地址

前端地址：

```text
http://localhost:5173/
```

后端接口默认本地代理到：

```text
http://localhost:8010/
```

### 3.2 演示账号

可直接使用以下测试账号：

- `admin@example.com / admin123`
- `agent@example.com / agent123`
- `viewer@example.com / viewer123`

推荐默认使用：

```text
admin@example.com / admin123
```

原因：

- 权限完整
- 最适合演示后台功能

### 3.3 推荐演示数据

如果你已经执行过 `backend/scripts/seed_data.py`，系统中会有以下几类适合演示的数据：

- 支付类工单
- 发票类工单
- 退款类工单
- 账号 / 访问类工单
- 已处理的历史工单
- 知识库文档

最推荐的演示工单：

```text
Enterprise renewal charged twice and finance team needs reversal
```

因为这张工单最容易带出：

- 工单分类
- RAG 回复草稿
- 风险审核
- 人工审核
- Multi-Agent 分析

---

## 4. 页面总览

登录后系统主要由以下区域组成：

### 4.1 左侧侧边栏

包含：

- `Dashboard`
- `Tickets`
- `Knowledge`
- 当前登录用户信息
- `Sign out`

作用：

- 负责页面导航和退出登录

### 4.2 顶部工作区区域

包含：

- 页面标题
- `Hide sidebar / Expand sidebar`
- `Authenticated session`

作用：

- 显示当前工作区状态
- 控制左侧侧边栏隐藏或展开

### 4.3 主内容区域

会随着你选择不同菜单，显示不同页面内容。

---

## 5. 登录页操作说明

访问地址：

```text
http://localhost:5173/
```

### 5.1 页面作用

登录系统，进入企业后台操作台。

### 5.2 页面元素说明

#### `Email`

作用：

- 输入登录邮箱

默认值：

```text
admin@example.com
```

#### `Password`

作用：

- 输入登录密码

默认值：

```text
admin123
```

#### `Sign in`

作用：

- 提交登录请求
- 登录成功后进入系统主界面

点击后可能出现的结果：

- 成功：跳转到首页 Dashboard
- 失败：显示登录失败提示

#### `Demo accounts`

作用：

- 展示可用测试账号
- 方便演示时快速切换

### 5.3 小白操作步骤

1. 打开 `http://localhost:5173/`
2. 在 `Email` 中确认是 `admin@example.com`
3. 在 `Password` 中确认是 `admin123`
4. 点击 `Sign in`
5. 进入系统首页

### 5.4 演示时怎么讲

可以这样介绍：

```text
首先登录系统。这里不是一个聊天窗口，而是一个企业运营后台，后面所有工单、知识库、AI 审核和 Multi-Agent 都在这个操作台里完成。
```

---

## 6. 公共导航和公共按钮说明

登录后，大部分页面都有这些通用控件。

### 6.1 左侧 `Dashboard`

作用：

- 进入数据总览页

适合做什么：

- 演示整体业务指标
- 演示 AI adoption

### 6.2 左侧 `Tickets`

作用：

- 进入工单列表页

适合做什么：

- 筛选工单
- 进入详情页
- 演示 AI 和 Multi-Agent 主流程

### 6.3 左侧 `Knowledge`

作用：

- 进入知识库页面

适合做什么：

- 上传文档
- 搜索知识
- 展示 RAG 的来源基础

### 6.4 `Hide sidebar`

作用：

- 隐藏左侧侧边栏

适合做什么：

- 屏幕较小时让主内容区域更宽
- 演示时专注右侧主内容

### 6.5 `Expand sidebar`

作用：

- 重新展开左侧侧边栏

### 6.6 `Sign out`

作用：

- 退出当前登录状态
- 返回登录页

注意：

- 演示过程中一般不建议频繁点击
- 除非你要切换账号

---

## 7. Dashboard 页面操作说明

路径：

```text
/
```

### 7.1 页面作用

Dashboard 用于展示系统当前整体运营状态，以及 AI 使用效果。

这是一个“看数据、讲价值”的页面，不是主要业务操作页。

### 7.2 页面模块说明

#### `Total tickets`

作用：

- 展示系统里当前总工单数量

展示重点：

- 当前平台积累了多少业务数据

#### `Open workload`

作用：

- 展示仍需要处理的工单数量

展示重点：

- 当前待处理压力有多大

#### `Resolved tickets`

作用：

- 展示已经解决或关闭的工单数量

展示重点：

- 系统具备完整闭环能力

#### `Urgent tickets`

作用：

- 展示紧急工单数量

展示重点：

- 系统不仅记录工单，还能体现优先级差异

#### `AI Adoption`

作用：

- 展示 AI 草稿的采纳情况

你能看到：

- 被批准或编辑后的 AI 建议数量
- AI 草稿总数
- AI 采纳率百分比

这是一个非常适合讲项目价值的模块。

#### `Signal Summary`

作用：

- 用自然语言总结当前队列状态

你能看到：

- 当前待处理量
- 紧急比例
- AI 审核通过情况

#### `Category distribution`

作用：

- 展示工单分类分布

你能直观看出：

- 支付类、退款类、发票类等工单的大致占比

#### `Priority distribution`

作用：

- 展示工单优先级分布

你能直观看出：

- 低、中、高、紧急工单的分布情况

### 7.3 这个页面有哪些按钮

这个页面基本没有主要操作按钮。

它是展示页，主要用于：

- 观察
- 讲解
- 引导进入 Tickets 页面

### 7.4 小白如何使用

1. 登录后停留在 Dashboard
2. 先看 4 张统计卡
3. 再看 AI Adoption
4. 再看分类和优先级分布
5. 讲完后点击左侧 `Tickets` 开始主线演示

### 7.5 演示时怎么讲

可以这样讲：

```text
这个页面是管理视角的总览页。除了总工单数、待处理量和紧急工单量，我们还展示 AI adoption，也就是 AI 草稿最终被人工采纳的情况，用来体现 AI 在企业场景里的落地价值。
```

---

## 8. Tickets 页面操作说明

路径：

```text
/tickets
```

### 8.1 页面作用

这里是工单列表页，用来：

- 看所有工单
- 筛选工单
- 进入具体工单详情
- 创建新工单

### 8.2 页面模块说明

#### 顶部 `Create ticket`

作用：

- 进入新建工单页面

适合做什么：

- 现场创建一条新工单作为演示案例

#### `Total tickets`

作用：

- 当前系统中的总工单数

#### `Open workload`

作用：

- 当前仍需处理的工单数

#### `Current result set`

作用：

- 当前筛选条件下显示出来的工单数量

#### `Status` 下拉框

作用：

- 按工单状态筛选

适合用法：

- 想只看待处理工单时使用

#### `Priority` 下拉框

作用：

- 按优先级筛选

适合用法：

- 想快速找 `urgent` 工单时使用

#### `Category` 下拉框

作用：

- 按分类筛选

适合用法：

- 想只看 `payment` 或 `refund` 类工单时使用

#### 工单标题链接

作用：

- 点击后进入该工单的详情页

这是整个项目主线演示最重要的入口之一。

### 8.3 小白如何使用

推荐先这样操作：

1. 打开 `Tickets`
2. 在 `Priority` 下拉框中选择 `Urgent`
3. 在 `Category` 中选择 `Payment`
4. 找到标题类似“重复扣费 / 续费重复扣款”的工单
5. 点击工单标题进入详情

### 8.4 演示时怎么讲

```text
这不是聊天记录列表，而是企业真实工单队列。每条工单都有客户信息、类别、优先级和状态，AI 能力是在这个业务对象上工作的。
```

---

## 9. Create Ticket 页面操作说明

路径：

```text
/tickets/new
```

### 9.1 页面作用

手动创建一条新工单，模拟企业真实用户请求。

### 9.2 字段说明

#### `Title`

作用：

- 工单标题

建议怎么写：

- 尽量简洁，直接写出问题核心

示例：

```text
Customer charged twice for annual renewal
```

#### `Customer name`

作用：

- 客户姓名

#### `Customer email`

作用：

- 客户邮箱

#### `Source`

作用：

- 工单来源

常见写法：

```text
manual
```

#### `Category`

作用：

- 工单初始分类

可选示例：

- `payment`
- `refund`
- `invoice`
- `technical`
- `account`

#### `Priority`

作用：

- 工单优先级

可选示例：

- `low`
- `medium`
- `high`
- `urgent`

#### `Description`

作用：

- 工单的完整描述

建议怎么写：

- 问题是什么
- 客户诉求是什么
- 有没有时间压力
- 有没有财务/合规风险

### 9.3 按钮说明

#### `Create ticket`

作用：

- 提交工单创建请求
- 成功后跳转到新工单详情页

#### `Back to list`

作用：

- 返回工单列表页
- 不提交当前内容

### 9.4 小白推荐操作

你可以用下面这组示例创建一条非常适合演示的工单：

- `Title`：
  `Customer charged twice for annual renewal`
- `Customer name`：
  `Lena Foster`
- `Customer email`：
  `lena.foster@example.com`
- `Source`：
  `manual`
- `Category`：
  `payment`
- `Priority`：
  `urgent`
- `Description`：
  `The customer says the annual renewal was captured twice this morning. Finance needs a reversal confirmation and wants to know whether service continuity will be affected.`

创建后系统会自动跳转到详情页。

---

## 10. Ticket Detail 页面操作说明

路径：

```text
/tickets/:ticketId
```

这是整个项目最核心的页面。

你可以在这里完成：

- 查看工单详情
- 更新工单状态
- 查看消息历史
- 运行 AI 分类
- 生成 AI 回复草稿
- 审核 AI 草稿
- 运行 Multi-Agent 分析
- 查看 Agent 执行时间线

---

### 10.1 基础信息区域

你会看到：

- 工单标题
- 工单状态
- 工单正文
- 客户信息
- 分类、优先级、情绪、来源等信息

作用：

- 让你先理解当前业务问题
- 这是后续 AI 和 Multi-Agent 的输入基础

---

### 10.2 `Status control`

#### `Update status` 下拉框

作用：

- 修改当前工单状态

你可以做什么：

- 把工单从 `open` 改成 `in_progress`
- 或改成 `waiting_review`
- 或改成 `resolved`

操作方式：

- 直接选择一个新状态即可
- 不需要额外点击保存按钮

适合演示什么：

- 说明这是真实工单流转，而不是只会“分析”的 AI 页面

---

### 10.3 `AI Classification`

#### `AI classify`

作用：

- 让 AI 对当前工单做结构化分诊

点击后会发生什么：

- 系统调用 AI 分类接口
- 返回：
  - `Category`
  - `Priority`
  - `Sentiment`
  - `Department`
  - `AI summary`
  - 是否需要人工介入

适合怎么展示：

1. 先点 `AI classify`
2. 等待分类完成
3. 指着分类结果讲：
   - 这一步是“分诊”
   - 不是最终结论
   - 是后续流程自动化输入

最值得讲的字段：

- `Category`
- `Priority`
- `Sentiment`
- `Department`
- `AI summary`

---

### 10.4 `AI Reply`

#### `Generate reply draft`

作用：

- 根据工单内容和知识库检索结果生成回复草稿

点击后会出现什么：

- AI 草稿正文
- `Reasoning summary`
- `Confidence`
- `Sources / RAG references`

#### `Sources`

作用：

- 展示该回复草稿引用了哪些知识库片段

你会看到：

- `Document #`
- `Chunk`
- `Score`
- 片段内容预览

#### `View knowledge document`

作用：

- 点击后跳转到对应知识文档详情页

适合怎么展示：

1. 先点 `Generate reply draft`
2. 展示 AI 生成的回复草稿
3. 重点展开 `Sources`
4. 点击知识文档链接跳到文档详情页

适合怎么讲：

```text
这一步不是凭空生成，而是先检索知识库，再根据命中的知识片段生成回复草稿，所以可以给出来源引用。
```

---

### 10.5 `Human Review`

这是 AI 安全边界最核心的一块。

系统设计原则是：

```text
AI 只能生成建议，不能直接发送给客户。
```

#### `Editable final reply`

作用：

- 允许人工编辑 AI 草稿

适合怎么用：

- 在 AI 草稿基础上改写语气或补充承诺边界

#### `Reject reason`

作用：

- 如果不接受草稿，可以填写拒绝原因

#### `Approve as drafted`

作用：

- 直接批准 AI 原始草稿

适合什么场景：

- 草稿已经比较准确，不需要改动

#### `Save edited approval`

作用：

- 把人工编辑后的文本保存为最终审核通过内容

这是最推荐演示的按钮。

为什么：

- 它最能体现 Human-in-the-loop
- 说明 AI 只是辅助，人类才是最后决策者

#### `Reject draft`

作用：

- 拒绝当前 AI 草稿
- 记录拒绝原因

适合什么场景：

- 回复内容不准确
- 风险太高
- 承诺边界不清晰

#### 审核完成后会看到什么

- `Reviewed at`
- `Reviewer`
- `Final approved content`
- 或 `Reject reason`

### 10.6 推荐的小白演示方式

最推荐你这样操作：

1. 点 `Generate reply draft`
2. 在 `Editable final reply` 中改一两句话
3. 点 `Save edited approval`
4. 展示审核完成后的最终内容

这样最好讲清楚：

- AI 给建议
- 人工修改
- 人工确认

---

### 10.7 `AI Agent Timeline`

#### `Run multi-agent analysis`

作用：

- 运行多 Agent 工作流

点击后会发生什么：

- 系统会顺序执行多个 Agent
- 页面展示每个 Agent 的结果卡片
- 页面展示 `Audit Trail`

---

### 10.8 各 Agent 卡片怎么理解

#### `Supervisor Agent`

作用：

- 决定整体处理模式
- 汇总流程计划

你可以看：

- 处理模式
- 计划执行哪些 Agent
- 是否需要人工审核

#### `Triage Agent`

作用：

- 负责工单分类、优先级、情绪、部门建议

#### `Knowledge Agent`

作用：

- 负责检索知识库

你可以看：

- 检索 query
- 命中数量
- 置信度
- 低置信度说明

#### `Similar Case Agent`

作用：

- 查历史相似工单

你可以看：

- 相似工单数量
- 历史处理摘要

#### `Reply Agent`

作用：

- 综合当前工单、知识检索和历史案例，生成回复建议

#### `Risk Agent`

作用：

- 判断风险等级
- 判断是否必须人工审核

#### `Workflow Agent`

作用：

- 给出下一步状态和处理动作建议

你可以看：

- `Next status`
- `Department`
- `Next action`

---

### 10.9 `Audit Trail`

作用：

- 按时间顺序展示每个 Agent 执行过程

你能看到：

- `agent_name`
- `action`
- `status`
- `timestamp`
- `output_summary`

这块特别适合讲项目亮点：

- Multi-Agent 不是黑盒
- 每一步都可解释
- 每一步都可追踪

---

### 10.10 `Messages`

作用：

- 展示工单历史消息记录

适合怎么展示：

- 告诉观众 AI 不是脱离上下文做判断
- 而是结合当前工单消息历史

---

### 10.11 推荐的完整操作顺序

进入工单详情后，最推荐按这个顺序点：

1. 先看基础信息和消息
2. 在 `Status control` 中改一次状态
3. 点 `AI classify`
4. 点 `Generate reply draft`
5. 展示 `Sources`
6. 用 `Save edited approval` 完成人工审核
7. 点 `Run multi-agent analysis`
8. 展示每个 Agent 结果
9. 展示 `Audit Trail`

---

## 11. Knowledge 页面操作说明

路径：

```text
/knowledge
```

### 11.1 页面作用

这是知识库运维和 RAG 准备页。

你可以在这里：

- 上传知识文档
- 检索知识文档
- 查看文档列表和处理状态
- 打开文档详情页

---

### 11.2 `Upload`

#### `Document title`

作用：

- 输入知识文档标题

示例：

```text
Payment troubleshooting SOP
```

#### `Knowledge file`

作用：

- 选择上传文件

支持格式：

- `.txt`
- `.md`

#### `Upload document`

作用：

- 上传文档
- 后台开始解析、切分、embedding、索引

点击后会发生什么：

- 列表里会出现新文档
- 状态从 `uploaded` 变成 `processing`
- 处理完成后变成 `ready`

适合怎么展示：

- 上传一份 SOP 或 FAQ
- 解释这是 AI 回复背后的知识来源

---

### 11.3 `Search`

#### `Search query`

作用：

- 输入知识检索问题

推荐输入：

- `duplicate charge reversal`
- `invoice correction`
- `payment completed but order status did not update`
- `delayed activation refund`

#### `Top K`

作用：

- 控制返回多少条结果

#### `Run search`

作用：

- 执行知识检索

点击后结果会显示在下方 `Search Results`

---

### 11.4 `Documents`

这里是知识文档总表。

你会看到：

- 文档标题
- 文件名
- 文件类型
- 状态
- chunk 数量
- 更新时间

#### 文档标题链接

作用：

- 点击进入知识文档详情页

#### 文档状态说明

- `uploaded`
  - 刚上传，等待处理
- `processing`
  - 正在解析和索引
- `ready`
  - 已经可以参与检索和 RAG
- `failed`
  - 处理失败

---

### 11.5 `Search Results`

这里展示知识检索命中结果。

每条结果会显示：

- 文档标题
- 文档编号
- chunk 编号
- 相似度分数
- 片段预览

#### `View document details`

作用：

- 进入该文档详情页

适合怎么展示：

1. 输入一个搜索问题
2. 点 `Run search`
3. 展示结果里的 `Score`
4. 点 `View document details`
5. 去文档详情页看 chunk

---

## 12. Knowledge Detail 页面操作说明

路径：

```text
/knowledge/:docId
```

### 12.1 页面作用

用来查看知识文档的详细内容和 chunk 切分结果。

### 12.2 按钮说明

#### `Back to knowledge`

作用：

- 返回知识库列表页

---

### 12.3 页面内容说明

#### 文档主信息

你会看到：

- 文档标题
- 文档状态
- 原始文档正文

#### 元信息卡片

你会看到：

- 文件名
- 文件类型
- chunk 数量
- 上传时间
- 存储路径

#### `Retrieval readiness`

作用：

- 告诉你文档是否已经准备好用于检索和 RAG

你会看到：

- 当前状态
- 处理说明
- chunk 数量
- 文档类型
- 最新更新时间

#### `Chunks`

作用：

- 展示该文档被切分后的 chunk 结果

每个 chunk 会展示：

- `Chunk index`
- chunk 内容
- `Embedding`
- 更新时间
- `metadata_json`

适合怎么讲：

```text
这一步体现了 RAG 的准备流程：先上传文档，再切分 chunk，再做 embedding，最后在检索时被 AI 使用。
```

---

## 13. 推荐的完整演示路径

如果你要给别人完整展示项目，建议按下面顺序操作。

### 13.1 快速版

1. 登录
2. 看 Dashboard
3. 进 Tickets
4. 打开一张支付类紧急工单
5. 点 `AI classify`
6. 点 `Generate reply draft`
7. 点 `Save edited approval`
8. 点 `Run multi-agent analysis`
9. 去 Knowledge 页面搜一条相关知识

### 13.2 完整版

1. 登录页点 `Sign in`
2. Dashboard 讲统计卡和 AI Adoption
3. 点左侧 `Tickets`
4. 用 `Priority = urgent`、`Category = payment` 筛选
5. 点一条重复扣费工单进入详情
6. 修改一次 `Status`
7. 点 `AI classify`
8. 点 `Generate reply draft`
9. 展示 `Sources`
10. 点知识文档跳去详情页
11. 返回工单详情
12. 修改 `Editable final reply`
13. 点 `Save edited approval`
14. 点 `Run multi-agent analysis`
15. 展示 `Audit Trail`
16. 点左侧 `Knowledge`
17. 上传文档或执行一次 `Run search`
18. 点 `View document details` 展示 chunk

---

## 14. 最适合演示的按钮

如果时间有限，优先演示以下按钮：

- `Sign in`
- `Create ticket`
- `AI classify`
- `Generate reply draft`
- `Save edited approval`
- `Run multi-agent analysis`
- `Run search`
- `View document details`

只演示这些，就足够把项目的主要亮点讲清楚。

---

## 15. 常见问题

### 15.1 登录失败怎么办

先检查：

- 前端是否打开了 `http://localhost:5173`
- 后端是否运行在 `http://localhost:8010`
- 是否已经初始化并写入演示数据
- 使用的是否是：
  - `admin@example.com / admin123`

### 15.2 知识库上传后一直没结果怎么办

检查：

- 上传的是否是 `.txt` 或 `.md`
- 文档状态是否卡在 `processing`
- 后端是否正常运行

### 15.3 AI 没有生成很好的回复怎么办

这通常是以下原因：

- 知识库没有命中
- 当前问题不在已上传的文档范围内
- 当前项目使用的是 mock / fake 数据能力，主要用于演示流程

### 15.4 Multi-Agent 结果为空怎么办

检查：

- 当前工单是否存在
- 后端是否正常运行
- 是否已经登录

---

## 16. 给演示者的建议

第一次演示时，强烈建议你不要从创建工单开始，而是先用系统已有的种子数据。

最推荐的顺序：

1. 登录
2. Dashboard
3. Tickets
4. 打开重复扣费工单
5. AI classify
6. Generate reply draft
7. Save edited approval
8. Run multi-agent analysis
9. Knowledge 搜索

这样成功率最高，也最容易讲清楚项目价值。

如果你之后需要：

- 面向面试官的讲解版文档
- 面向最终用户的简化版文档
- 带截图的图文操作手册

可以在本手册基础上继续扩展。
