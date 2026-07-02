# DEV_NOTES — 开发学习笔记

> 本文件记录 My-platform 项目 12 步学习路线中每一步的完成情况、学到的东西、遇到的问题和验证结果。
> 按照 `My-platform_backend_learning_12_steps.md` 路线图执行。

---

## 环境信息

- Python 环境：`D:\tools\anaconda\envs\py312\python.exe`
- Node.js：系统 PATH 中可用
- 项目根目录：`E:\Bawa_Data\Xiangmu\My-platform`
- 后端目录：`backend/`
- 前端目录：`frontend/`
- 数据库：运行时用 MySQL（见 `.env`），pytest 用 SQLite（见 `conftest.py`）

---

## 常用命令速查

### 后端

```bash
# 安装依赖
cd backend
D:\tools\anaconda\envs\py312\python.exe -m pip install -r requirements.txt

# 初始化数据库
D:\tools\anaconda\envs\py312\python.exe -m app.db.init_db

# 导入演示数据
D:\tools\anaconda\envs\py312\python.exe scripts/seed_data.py

# 启动后端（端口 8010）
D:\tools\anaconda\envs\py312\python.exe -m uvicorn app.main:app --reload --port 8010

# 健康检查
curl http://localhost:8010/health
```

### 测试

```bash
cd backend
D:\tools\anaconda\envs\py312\python.exe -m pytest                          # 全部测试
D:\tools\anaconda\envs\py312\python.exe -m pytest tests/test_tickets.py    # 单项测试
D:\tools\anaconda\envs\py312\python.exe -m pytest -v                       # 详细输出
D:\tools\anaconda\envs\py312\python.exe -m pytest --tb=short               # 短回溯
```

### 前端

```bash
cd frontend
npm install
npm run dev          # 开发模式
npm run build        # 构建检查
```

### 测试账号

| 邮箱 | 密码 | 角色 |
|---|---|---|
| admin@example.com | admin123 | admin |
| agent@example.com | agent123 | agent |
| viewer@example.com | viewer123 | viewer |

---

## 任务记录

---

### Step 0：跑通环境和 pytest

**完成日期**：2026-06-29

#### 目标

确认项目能稳定启动、导入数据、运行测试，创建 DEV_NOTES.md。

#### 涉及文件

- `backend/.env` — 运行时配置（MySQL + 千问 LLM）
- `backend/tests/conftest.py` — 测试配置（SQLite + mock LLM + fake embedding）
- `docs/DEV_NOTES.md` — 本文件（新建）

#### 我自己做了什么

1. 启动了后端服务，确认 `/health` 返回正常
2. 执行了 `init_db` 初始化数据库表结构
3. 执行了 `seed_data.py` 导入演示数据
4. 使用三个默认账号测试了登录接口
5. 运行了 `pytest`，确认全部测试通过
6. 启动了前端 `npm run dev`，确认前端可以正常访问

#### Qoder 辅助了什么

1. 帮我创建了 `docs/DEV_NOTES.md`，整理了项目启动命令和基础信息
2. 帮我梳理了当前环境和配置状态

#### 遇到的问题

- 无重大问题

#### 最终测试

```bash
D:\tools\anaconda\envs\py312\python.exe -m pytest
```

#### 手动验证

- `GET /health` → 200 OK
- `POST /api/auth/login`（三个账号）→ 200 OK，返回 access_token
- 前端页面可正常访问

#### 学到的知识

1. 项目如何启动：后端用 uvicorn，前端用 vite
2. 配置从哪里读取：`.env` 文件 → `app/core/config.py`
3. 数据库如何初始化：`app.db.init_db` → SQLAlchemy `Base.metadata.create_all`
4. seed 数据如何生成：`scripts/seed_data.py` 插入演示用数据
5. 测试如何运行：pytest 通过 `conftest.py` 自动使用 SQLite + mock 模式
6. 前后端如何联调：后端 8010 端口，前端 dev server 自动代理

#### 后续可以优化

- 当前运行时依赖 MySQL，如果 MySQL 不可用可考虑切回 SQLite 做本地开发
- `.env.example` 里缺少 MySQL 相关字段的示例说明

---

## 常见问题排查

### 后端启动报数据库连接错误

检查 MySQL 是否在运行，以及 `.env` 中 `DATABASE_URL` 是否正确。如果想纯本地开发不依赖 MySQL，可以将 `DATABASE_URL` 改为：

```
DATABASE_URL=sqlite:///./app.db
```

### pytest 报错 ModuleNotFoundError

确认在 `backend/` 目录下运行，且使用了正确的 Python 环境：

```bash
D:\tools\anaconda\envs\py312\python.exe -m pytest
```

### 前端 npm install 失败

尝试清除缓存后重试：

```bash
npm cache clean --force
npm install
```

### 端口被占用

```bash
# Windows 查看端口占用
netstat -ano | findstr :8010
# 终止进程
taskkill /PID <PID> /F
```
