# Java 业务服务与 Python AI 服务

## 服务边界

网站和微信小程序只访问 Java 的 `/api/v1`。Java 17 / Spring Boot 3.5 / Spring Security / MyBatis 负责认证、家庭、菜品、订单、评价、聊天、通知、图片存储及 AI 会话。Python 3.12 / FastAPI / LangChain 负责上下文检索、多模态输入、模型调用和结构化推荐。

Python 服务不配置 PostgreSQL 或 Redis，不自行查询家庭数据。Java 在请求线程完成用户与家庭鉴权，把授权上下文传入 Python；服务间通过 `Authorization: Bearer <AI_SERVICE_TOKEN>` 验证，生产 Compose 不发布 Python 端口。

旧 `backend/` 完整保留，`docker-compose.legacy.yml` 保存迁移前生产服务配置。

## 本地启动

空数据库可直接执行：

```powershell
docker compose up -d --build
```

Java 地址为 `http://localhost:8001`，前端仍可在 `frontend` 内运行 `npm run dev`。开发 Compose 沿用 `backend/uploads`，不要对已有旧数据库直接启动 Java；请先按下文执行接管。

AI 默认关闭。开启时通过环境变量提供 `AI_ENABLED=true`、`AI_BASE_URL`、`AI_API_KEY`、`AI_MODEL`，并在 Java 与 Python 设置相同的 `AI_SERVICE_TOKEN`。生产配置必须提供独立随机令牌，不使用开发默认值。模型密钥仅传入 Python。

独立开发时，Java 使用 `mvn spring-boot:run`，Python 安装 `pip install -e '.[dev]'` 后执行 `uvicorn ai_service.main:app --port 8002`。将各目录 `.env.example` 的配置导入当前进程环境；Spring Boot 不自动加载 `.env` 文件。

## 兼容接口

| 模块 | 保留的接口 |
| --- | --- |
| 账号 | 注册、登录、微信登录、读取与修改 `/auth/me` |
| 家庭 | `/families`、`/families/join`、`/families/current`、成员列表 |
| 菜品与图片 | `/dishes` 增删改查、`/uploads/images`、静态 `/uploads/**` |
| 订单 | `/orders`、`/orders/history`、详情、`accept`、`review` |
| 聊天 | `/chat/messages`、`/chat/unread-count`、`/chat/read` |
| 首页与通知 | `/home/summary`、`/notifications/subscriptions/grant` |
| AI | 会话列表与删除、消息历史、普通发送与流式发送 |
| 健康 | `/health` |

所有业务路径均位于 `/api/v1`。保留 `{code,message,data}` 包装和原字段命名；旧 PBKDF2-SHA256 密码以及 HS256 JWT 可继续使用。前端没有布局改造。

### 订单幂等

`POST /orders` 新增可选字符串 `requestId`（1—128 字符），网站和小程序使用 UUID。一次未成功确认的提交重试复用原 ID；编辑内容或成功提交后生成新的 ID。

唯一范围是 `(family_id, requester_id, request_id)`。同键同内容返回原订单；同键不同内容返回 HTTP 409；处理中返回 HTTP 409 并提示复用原 ID 重试。省略字段的旧客户端继续可用，但不具备跨请求去重保证。

Redis 锁使用 30 秒租期和所有者令牌比较删除。数据库唯一索引在 Redis 失效、不可用及竞争时仍保证只生成一笔订单。订单、明细、日志、通知出站和额度扣减同事务完成。

通知由数据库出站记录异步发送。外部发送结果不确定时标记失败待核查，不自动重发，以免重复通知；中断的 `sending` 记录在五分钟后标记失败。

### 缓存与 SQL

菜品详情缓存 10 分钟、家庭偏好与 AI 推荐缓存 5 分钟。数据库事务触发器递增家庭数据版本，提交后旧版本缓存自然不可达；回退实例写入也会更新版本。详情命中仍有一次轻量版本查询，不再加载完整关联数据。

非空订单列表或详情加载由两条 MyBatis 查询完成：主体及用户、评价、日志摘要；`foreach` 批量读取明细与菜品。数量增加不增加客户端数据库往返。

### AI 内部协议

`POST /internal/v1/recommendations/stream` 接收 JSON：`request_id`、`content`、`dishes`、`preferences`、`dining_history`、`history`、可选 `image_data_url`。图片只能是 JPEG/PNG/WebP 内联数据，不允许任意远程 URL。

Python 使用请求范围内的 LangChain Retriever，中文双字词与英文词匹配排序，每类默认保留最多 4 条资料，每条最多 1800 字符。无向量数据库；这是结构化上下文检索，不宣称向量语义检索。

内部 SSE 的 `complete` 携带推荐结果；Java 将其写入业务库并转换为原有 `{conversation,user_message,assistant_message}`。对外事件为 `ready`、`delta`、`complete`、`error`，每 15 秒心跳。Java 和 Python 都有超时和取消清理，开始输出后不自动重试。

推荐缓存键包含家庭、用户、输入、图片内容、会话历史、实际业务上下文和模型配置指纹。命中后跳过推理，仍创建独立的两条对话消息。用户消息先提交，失败不保存伪成功的助手消息。

## 旧库接管与回退

1. 先在旧服务把 Alembic 升级到 `20260724_110000`。保留原数据库、上传卷、JWT 密钥及旧镜像。
2. 构建新镜像后进入维护窗口，停止旧后端写入，备份 PostgreSQL 和上传文件。
3. 执行 Java 接管命令，自动迁移必须关闭：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm --no-deps backend \
  --spring.main.web-application-type=none --spring.flyway.enabled=false \
  --yy.migration-action=adopt --WECHAT_ENABLED=false
```

接管工具核对 Alembic 版本，在临时独立 schema 重放完整迁移链，对比列、约束和索引。匹配后显式 baseline 到 V1，再应用后续版本；不匹配拒绝接管。临时 schema 随验证结束清理，业务数据不搬迁。

4. 启动新服务并完成登录、订单、图片、AI 等冒烟检查后恢复访问。
5. 失败时切回保存的旧镜像，保留新增兼容列和表，不执行破坏性数据库降级；如果必须恢复备份，先停止写入并明确备份之后的数据取舍。

服务器部署入口为 `bash scripts/deploy-services.sh preview deploy`（HTTPS 使用 `https`）；回退为 `bash scripts/deploy-services.sh preview rollback`。原 `deploy.ps1` 的后端/全量发布已调用该流程，前端发布保留原流程。实际服务器发布没有在开发测试中执行。

## 验证命令

```powershell
mvn -B -ntp -f backend-java/pom.xml verify
ai-service/.venv/Scripts/python.exe -m pytest ai-service/tests -q
npm --prefix frontend run verify
npm --prefix miniprogram run verify
```

小程序生产构建需配置 `.env.example` 中的 API 地址及两项订阅模板，CI 使用测试占位值。Java 集成测试要求可访问 Docker；测试资源固定 Docker API 1.44 以兼容 Docker 29。

完整 HTTP 演练使用专用 Compose 项目及本地模型桩，不访问真实模型或微信服务：

```powershell
docker compose -p yy-refactor-smoke -f docker-compose.smoke.yml up -d --build --wait
docker compose -p yy-refactor-smoke -f docker-compose.smoke.yml port frontend 80
ai-service/.venv/Scripts/python.exe tests/e2e/smoke.py http://127.0.0.1:返回的端口
docker compose -p yy-refactor-smoke -f docker-compose.smoke.yml down --volumes
```

测试项目的端口随机分配，数据库位于专用容器，不挂载现有业务数据。
