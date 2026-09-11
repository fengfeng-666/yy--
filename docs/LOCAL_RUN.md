# Windows 本地运行

当前架构：`frontend`（Vue 3 + Vite）→ `backend-java`（Java 17 + Spring Boot）→ PostgreSQL / Redis；`ai-service` 是内部 Python AI 服务。`backend` 是保留的旧后端。

## 本机已验证的配置

- 页面：http://127.0.0.1:5174
- Java 健康检查：http://127.0.0.1:8001/api/v1/health
- 数据库：localhost:5433 / yy_kitchen_local
- Redis：localhost:6379
- 前端使用 `/api/v1`，由 Vite 代理到 8001。
- 下方 Java 启动命令已启用 AI，需先启动本机 8002 端口的 Python AI 服务，且双方令牌一致。微信功能关闭；空库需要自行注册账号。

2026-09-11 已使用现有 `backend-java/target/backend-1.0.0.jar` 启动，验证页面、后端健康检查和 Vite API 代理均返回 HTTP 200，开发库迁移至 Flyway V3。这是启动验证，未覆盖全部业务流程。

## 以后启动

先启动 Docker Desktop，在项目根目录的 PowerShell 执行：

```powershell
Set-Location 'F:\my_project\yy私厨'
docker compose up -d postgres redis ai-service
```

本机已创建 `yy_kitchen_local`，无需重复建库。换到新环境时，可在 PostgreSQL 启动后创建一次：

```powershell
docker exec yy-kitchen-postgres createdb -U postgres yy_kitchen_local
```

在一个 PowerShell 窗口启动 Java（保留窗口）：

```powershell
Set-Location 'F:\my_project\yy私厨'
$env:DB_HOST = 'localhost'
$env:DB_PORT = '5433'
$env:DB_NAME = 'yy_kitchen_local'
$env:DB_USER = 'postgres'
$env:DB_PASSWORD = 'password'
$env:REDIS_HOST = 'localhost'
$env:REDIS_PORT = '6379'
$env:AI_ENABLED = 'true'
$env:AI_SERVICE_URL = 'http://127.0.0.1:8002'
$env:AI_SERVICE_TOKEN = 'yy-local-ai-token'
$env:WECHAT_ENABLED = 'false'
$env:UPLOAD_DIR = 'F:/my_project/yy私厨/backend/uploads'
mvn -f backend-java/pom.xml spring-boot:run
```

Spring Boot 不会自动读取 `.env`，以上变量必须在启动 Java 的同一个窗口设置。Maven 启动会编译当前源代码；如果只运行已有构建，可将最后一行换成 `java -jar backend-java/target/backend-1.0.0.jar`。

如果 AI 聊天返回 `503 / AI 服务尚未配置`，说明当前 Java 进程的 AI 开关未开启或服务令牌为空。只设置 Python 的环境变量不会更新 Java；先在运行 Java 的窗口按 Ctrl+C，设置上述三项 `AI_` 变量后重新启动 Java。`yy-local-ai-token` 仅为本地开发示例，须与 Python 的 `AI_SERVICE_TOKEN` 相同。

再开一个 PowerShell 窗口启动前端：

```powershell
Set-Location 'F:\my_project\yy私厨\frontend'
# 本机已有 node_modules；新环境首次运行需要 npm ci。
npm run dev -- --host 127.0.0.1
```

打开 http://127.0.0.1:5174 。前台启动的进程可在各自窗口按 Ctrl+C 停止。

## 本次后台进程

本次启动日志及进程 ID 在 `.test-artifacts/local-run/`，目录已被 Git 忽略。重复启动前先停止现有进程，避免占用 8001 / 5174。仅在确认仍是本次 Java/Vite 进程后，可用 `Stop-Process -Id <进程ID>` 停止。

## 旧数据库问题

本机原有 `yy_kitchen` 数据库保持原样，当前不使用它。检查时其 Alembic 版本为 `20260727_100000`，但 `backend-java/src/main/java/com/yykitchen/migration/LegacyBaseline.java` 只接受 `20260724_110000`。因此当前接管流程无法直接接管该库，默认启动也会因缺少 Flyway 历史表而失败。

需要旧数据时，应先备份，补齐针对实际旧库版本的兼容迁移和结构验证。不要为了启动而开启自动 baseline、修改旧库版本号或删除数据卷。当前根目录 `docker compose up -d --build` 默认仍连接旧库；本机请使用上面的独立开发库启动方法。

AI 容器的 8002 端口当前仅在 Docker 内网开放。后续启用本地 Java 的 AI 功能时，需要提供本机可达的 AI 服务地址，以及匹配的服务令牌和模型配置。
