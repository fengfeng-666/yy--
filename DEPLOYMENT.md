# YY私厨生产部署

当前生产方案使用 Docker Compose：Nginx 提供前端静态文件并反向代理 API，FastAPI 负责业务接口，PostgreSQL 和上传文件使用独立持久化卷。

## 1. 准备配置

复制根目录的 `.env.production.example` 为 `.env.production`，至少替换：

- `POSTGRES_PASSWORD`：数据库强密码；
- `JWT_SECRET_KEY`：至少 32 字节的随机密钥，推荐执行 `openssl rand -hex 32` 生成；
- `APP_PORT`：宿主机对外端口，默认 `80`；
- `UVICORN_WORKERS`：后端进程数，建议从 `2` 开始，根据服务器 CPU 和内存调整。

`.env.production` 已被 Git 忽略，不要提交真实密钥。

## 2. 上线前验证

前端：

```bash
cd frontend
npm ci
npm run lint
npm run test
npm run build
```

后端：

```bash
cd backend
uv sync --extra dev
uv run pytest -q
```

检查 Compose 配置：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml config
```

## 3. 启动

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

后端容器会先执行数据库迁移，再启动应用。前端健康检查地址为 `/healthz`，业务健康检查地址为 `/api/v1/health`。

## 4. HTTPS

生产站点必须通过 HTTPS 访问。当前 Compose 对外提供 HTTP 端口，建议放在云负载均衡、CDN 或宿主机 Caddy/Nginx 后，由外层代理负责域名证书和 HTTPS 跳转。

## 5. 数据备份

升级或迁移前至少备份 PostgreSQL 和上传文件卷：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > yy_kitchen.sql
```

上传图片位于 Docker 卷 `uploads_data`。数据库恢复、上传卷恢复流程应在首次正式上线前演练一次。

## 6. 更新版本

```bash
git pull
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

更新后检查：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
docker compose --env-file .env.production -f docker-compose.prod.yml logs --tail=100 backend
```
