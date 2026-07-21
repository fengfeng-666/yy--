# YY私厨 Backend

基于 FastAPI 的后端初始化项目，当前完成阶段 0 的基础骨架：

- FastAPI 应用入口
- 统一响应结构
- 全局异常处理
- 请求日志与请求 ID
- PostgreSQL 异步会话配置
- Alembic 初始化文件
- Docker 开发配置

## 启动步骤

### 1. 准备环境变量

复制环境变量文件：

```bash
copy .env.example .env
```

### 2. 准备数据库

推荐先在项目根目录启动 PostgreSQL：

```bash
docker compose up -d postgres
```

数据库默认连接信息：

- Host: `localhost`
- Port: `5433`
- Database: `yy_kitchen`
- User: `postgres`
- Password: `password`

### 3. 安装依赖

```bash
pip install -e .[dev]
```

### 4. 启动后端服务

```bash
uvicorn app.main:app --reload --port 8001
```

### 5. 执行数据库迁移

首次建表或后续模型变更时，进入 `backend/` 目录执行：

```bash
uv run alembic revision --autogenerate -m "init"
uv run alembic upgrade head
```

常用命令：

- 查看当前迁移版本：`uv run alembic current`
- 查看迁移历史：`uv run alembic history`
- 回退一个版本：`uv run alembic downgrade -1`

说明：

- `alembic/env.py` 会自动读取 `backend/.env` 中的数据库连接配置
- 新增 ORM 模型后，需要在 `app/models/__init__.py` 中导入，确保 `autogenerate` 能发现元数据

### 5.1 重建开发库

如果本地开发库的迁移状态混乱，可以先执行仓库内保留的 SQL 脚本清空核心表和 `alembic_version`：

```bash
docker exec -i yy-kitchen-postgres psql -U postgres -d yy_kitchen < backend/sql/reset_dev_schema.sql
uv run alembic upgrade head
```

脚本位置：`backend/sql/reset_dev_schema.sql`

### 6. 访问接口

```text
GET http://localhost:8001/api/v1/health
```

后端运行地址：

- API 根地址：`http://localhost:8001`
- Swagger 文档：`http://localhost:8001/docs`
- 健康检查：`http://localhost:8001/api/v1/health`

## PostgreSQL 配置

推荐两种方式：

### 方式一：使用 Docker Compose

在项目根目录执行：

```bash
docker compose up -d postgres
```

数据库默认配置：

- Host: `localhost`
- Port: `5433`
- Database: `yy_kitchen`
- User: `postgres`
- Password: `password`

### 方式二：连接你自己的本地 PostgreSQL

将 `backend/.env` 中的数据库配置改成你自己的实例：

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=yy_kitchen
DB_USER=postgres
DB_PASSWORD=password
```

如果你已经有完整连接串，也可以直接设置：

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5433/yy_kitchen
```

说明：`DATABASE_URL` 优先级高于拆分的 `DB_*` 配置。

## 联调说明

- 本地直接运行后端时，默认读取 `backend/.env`
- 使用 `docker compose up` 启动整套服务时，后端容器会自动连接 `postgres` 容器
- 健康检查接口会返回数据库连接状态，便于确认 PostgreSQL 是否配置成功
- 当前默认前端地址为 `http://localhost:5174`
- 所有成功响应统一使用 `{code, message, data}` 结构
- `AppException`、请求参数校验异常、`HTTPException` 和未捕获异常都会返回统一错误结构

## 目录说明

```text
backend/
├── app/
│   ├── api/v1/
│   ├── core/
│   ├── db/
│   ├── middleware/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── alembic/
├── uploads/
├── .env.example
├── pyproject.toml
└── README.md
```
