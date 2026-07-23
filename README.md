# YY私厨

当前仓库包含网站端、微信小程序端和 FastAPI 后端：

```text
F:\my_project\yy私厨
├── backend
│   ├── app
│   ├── alembic
│   ├── uploads
│   ├── .env.example
│   ├── Dockerfile
│   ├── README.md
│   ├── alembic.ini
│   └── pyproject.toml
├── frontend
│   ├── src
│   ├── README.md
│   ├── package.json
│   └── vite.config.ts
├── miniprogram
│   ├── src
│   ├── tests
│   ├── README.md
│   └── package.json
├── docker-compose.yml
└── YY私厨_详细设计方案.md
```

## 当前完成内容

- 初始化 Vue 3 + TypeScript 前端工程
- 新增 uni-app + Vue 3 + TypeScript 微信小程序，支持微信登录与订阅消息授权
- 初始化 FastAPI 项目结构
- 配置基础环境变量
- 配置 PostgreSQL 异步连接
- 配置 Alembic
- 配置统一响应和异常处理
- 配置请求日志和请求 ID
- 提供健康检查接口
- 增加微信 OpenID、订阅额度和通知出站记录的数据迁移

## 快速启动

### 1. 启动 PostgreSQL

在项目根目录执行：

```bash
docker compose up -d postgres
```

启动后宿主机连接信息：

- Host: `localhost`
- Port: `5433`
- Database: `yy_kitchen`
- User: `postgres`
- Password: `password`

### 2. 启动后端

先复制环境变量模板：

```bash
copy backend\.env.example backend\.env
```

然后进入 `backend` 目录安装依赖并启动：

```bash
cd backend
pip install -e .[dev]
uvicorn app.main:app --reload --port 8001
```

后端地址：

- API 根地址：`http://localhost:8001`
- 健康检查：`http://localhost:8001/api/v1/health`

启动后首次请执行数据库初始化，推荐在 `backend/` 目录运行：

```bash
uv run alembic upgrade head
```

如果你想直接用 SQL 快照初始化当前库结构，也可以执行：

```bash
docker exec -i yy-kitchen-postgres psql -U postgres -d yy_kitchen < backend/sql/bootstrap_schema.sql
```

详细迁移约定见 [backend/README.md](file:///f:/my_project/yy私厨/backend/README.md)。

### 3. 启动前端

进入 `frontend` 目录安装依赖并启动：

```bash
cd frontend
npm install
npm run dev
```

前端地址：

- 开发地址：`http://localhost:5174`

### 4. 前后端联调

- 前端默认请求后端：`http://localhost:8001/api/v1`
- 后端默认允许前端来源：`http://localhost:5174`

## 单独查看说明

- 后端详细说明见 `backend/README.md`
- 前端详细说明见 `frontend/README.md`

## 下一步建议

1. 复制 `backend/.env.example` 为 `backend/.env`
2. 执行 `docker compose up -d postgres` 启动数据库
3. 安装后端依赖并启动本地服务
4. 开始实现“账号与家庭空间”相关模型和迁移

## PostgreSQL 快速使用

项目已经补齐 PostgreSQL 配置：

- 本地运行后端时，通过 `backend/.env` 的 `DB_HOST`、`DB_PORT`、`DB_NAME`、`DB_USER`、`DB_PASSWORD` 连接数据库
- Docker 运行时，后端容器自动连接 `docker-compose.yml` 中的 `postgres` 服务
- 健康检查接口 `GET /api/v1/health` 会附带数据库连接状态
