# YY私厨生产部署

当前生产方案使用 Docker Compose：Caddy 提供公网 HTTPS 入口，Nginx 提供网站静态文件，
FastAPI 负责业务接口，PostgreSQL 和上传文件使用独立持久化卷。

## 一键部署（推荐）

Windows 本机在项目根目录运行：

```powershell
.\deploy.cmd
```

脚本会自动识别前端、后端或全量变更，并依次完成：敏感文件检查、测试、提交、推送、
安全打包、上传、按需重建、健康检查和公网验收。发现未提交改动时，会先显示文件列表并
要求确认，不会静默提交。

常用参数：

```powershell
# 仅演练检查，不提交、推送或上传
.\deploy.cmd -DryRun -Scope Frontend

# 明确只发布前端
.\deploy.cmd -Scope Frontend

# 紧急情况下跳过测试（不推荐）
.\deploy.cmd -SkipTests

# 备案和 DNS 生效后切换 HTTPS Compose
.\deploy.cmd -Https -PublicUrl https://www.yykitchen.xyz
```

`deploy.cmd` 只对本次运行使用 PowerShell 执行策略绕过，不会修改 Windows 的全局安全设置。

默认连接信息为 `ubuntu@124.221.19.62`，私钥为
`%USERPROFILE%\.ssh\yykitchen_deploy_ed25519`，服务器目录为 `/opt/yykitchen`。
如环境不同，可以通过 `-Server`、`-RemoteUser`、`-SshKey` 和 `-RemoteDir` 覆盖。

## 0. 云资源建议

- 腾讯云中国内地轻量应用服务器：2 核 2GB、40GB SSD、带公网 IP，Ubuntu 24.04 LTS，
  包年包月至少 3 个月；建议直接购买 1 年。
- 已注册域名：`yykitchen.xyz`。
- DNS 规划：`www.yykitchen.xyz` 和 `api.yykitchen.xyz` 的 A 记录均指向服务器公网 IP
  `124.221.19.62`。
- 安全组开放 TCP 22、80、443 和 UDP 443。SSH 的 22 端口尽量只允许管理员常用 IP。
- 中国内地服务器正式对外服务前先完成 ICP 备案。域名、腾讯云账号和备案主体信息应保持一致。

## 1. 准备配置

复制根目录的 `.env.production.example` 为 `.env.production`，至少替换：

- `POSTGRES_PASSWORD`：数据库强密码；
- `JWT_SECRET_KEY`：至少 32 字节的随机密钥，推荐执行 `openssl rand -hex 32` 生成；
- `ROOT_DOMAIN`、`WEB_DOMAIN`、`API_DOMAIN`：根域名、网站域名和小程序 API 域名；
- `ACME_EMAIL`：Caddy 申请和续期 HTTPS 证书使用的联系邮箱；
- `UVICORN_WORKERS`：后端进程数，建议从 `2` 开始，根据服务器 CPU 和内存调整。
- `WECHAT_ENABLED`：仅部署网站时设为 `false`；启用小程序后改为 `true`；
- 启用微信功能后再填写 `WECHAT_APP_ID`、`WECHAT_APP_SECRET` 和两个订阅消息模板 ID。

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

微信小程序：

```bash
cd miniprogram
npm ci
npm run verify
```

小程序生产构建前需创建 `miniprogram/.env.production`，填写 HTTPS API 地址和两个消息模板
ID，并在 `miniprogram/src/manifest.json` 中填写 AppID。构建后用微信开发者工具导入
`miniprogram/dist/build/mp-weixin`，完成真机测试、上传、体验版验证和提交审核。

检查 Compose 配置：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml config
```

## 3. 启动

备案前仅通过服务器 IP 预览网站（只开放 HTTP 80，不启动 Caddy）：

```bash
docker compose --env-file .env.production \
  -f docker-compose.prod.yml -f docker-compose.preview.yml up -d --build
```

备案完成、DNS 生效后的正式 HTTPS 启动命令：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

后端容器会先执行数据库迁移，再启动应用。前端健康检查地址为 `/healthz`，业务健康检查地址为 `/api/v1/health`。

## 4. HTTPS

生产 Compose 已包含 Caddy。域名 A 记录指向服务器公网 IP，并开放 TCP 80、TCP 443
和 UDP 443 后，Caddy 会自动申请证书、续期并将 HTTP 跳转到 HTTPS。证书状态保存在
`caddy_data` 卷中。

同时需要在微信公众平台把该 HTTPS API 域名配置为 `request` 合法域名。微信开发者工具中
“不校验合法域名”只适合本地调试，不能代替正式平台配置。

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
