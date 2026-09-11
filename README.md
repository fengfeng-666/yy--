# YY私厨

当前默认架构为 **Java 业务后端 + Python AI 服务**，网站和微信小程序接口保持兼容。

- `backend-java/`：Java 17、Spring Boot 3、Spring Security、MyBatis、PostgreSQL、Redis、Flyway。
- `ai-service/`：FastAPI、LangChain，负责全部 AI 推理与检索，通过内部 SSE 接入 Java。
- `frontend/`、`miniprogram/`：原有网站和微信小程序，新增下单请求幂等标识。
- `backend/`：保留的旧 FastAPI 完整服务，用于对照与回退。

**启动、测试、旧库接管、部署与回退请使用 [双服务重构文档](docs/REFACTOR.md)。已有数据库必须先验证并接管，不能直接用 Flyway 自动基线。**

空库开发启动：`docker compose up -d --build`。Java 默认端口为 8001，AI 服务仅在容器内网开放。生产模型配置及内部令牌参考 `.env.production.example`。

以下为迁移前 FastAPI 版本的历史说明，仅用于维护保留的旧服务。

## 旧版项目结构

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

### 2. 启动后端（默认 Java 业务服务 + Python AI 服务）

> **仅限空库。** 若已存在旧 FastAPI 数据库，不要直接启动 Java——必须先按 [双服务重构文档](docs/REFACTOR.md) 的“旧库接管与回退”验证并接管，Flyway 已关闭自动基线，直接启动会拒绝迁移。

一键构建并启动全套服务（`backend-java` 与 `ai-service` 以容器运行）：

```bash
docker compose up -d --build
```

启动后 Java 后端地址：

- API 根地址：`http://localhost:8001`
- 健康检查：`http://localhost:8001/api/v1/health`

AI 默认关闭；开启需设置 `AI_ENABLED=true` 及 `AI_BASE_URL`、`AI_API_KEY`、`AI_MODEL`，并让 Java 与 Python 使用相同的 `AI_SERVICE_TOKEN`（详见 REFACTOR）。

改用本地进程开发（而非容器）时：

```bash
docker compose up -d postgres redis ai-service
cd backend-java && mvn spring-boot:run                          # Java 17，环境变量按 application.yml 注入
cd ai-service && pip install -e '.[dev]' && uvicorn ai_service.main:app --port 8002
```

空库由 Flyway 自动完成 schema 迁移（`V1__legacy_schema.sql` 起）。迁移与接管细节见 [双服务重构文档](docs/REFACTOR.md) 与 [backend-java/README.md](backend-java/README.md)。

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

- 默认后端（Java）详细说明见 `backend-java/README.md`
- AI 服务详细说明见 `ai-service/README.md`
- 前端详细说明见 `frontend/README.md`
- 保留的旧 FastAPI 后端说明见 `backend/README.md`

## 下一步建议

1. 空库开发：执行 `docker compose up -d --build` 启动全套服务
2. 已有旧库：先按 `docs/REFACTOR.md` 的“旧库接管与回退”验证并接管，再启动新服务
3. 用 `mvn -B -ntp -f backend-java/pom.xml verify` 与 `pytest` 验证 Java 与 AI 服务
4. 使用 `docker-compose.smoke.yml` 做端到端冒烟（不访问真实模型与微信）

## PostgreSQL 快速使用

项目已经补齐 PostgreSQL 配置：

- 本地运行后端时，通过 `backend/.env` 的 `DB_HOST`、`DB_PORT`、`DB_NAME`、`DB_USER`、`DB_PASSWORD` 连接数据库
- Docker 运行时，后端容器自动连接 `docker-compose.yml` 中的 `postgres` 服务
- 健康检查接口 `GET /api/v1/health` 会附带数据库连接状态
