# YY私厨微信小程序

这是基于 uni-app、Vue 3 和 TypeScript 的微信小程序端，生产产物位于
`dist/build/mp-weixin`。

## 本地开发

```powershell
npm install
npm run dev:mp-weixin
```

然后在微信开发者工具中导入 `dist/dev/mp-weixin`。

## 上线前配置

1. 在微信公众平台注册小程序，取得 AppID，并填写到 `src/manifest.json` 的
   `mp-weixin.appid`。AppID 可以进入代码仓库，AppSecret 不可以。
2. 复制 `.env.example` 为 `.env.production`，填写 HTTPS API 地址和两个订阅消息模板 ID。
3. 在微信公众平台把 API 域名加入“request 合法域名”；域名必须使用 HTTPS，且不能使用
   IP 地址或 localhost。
4. 在服务端环境变量中填写同一个 AppID、AppSecret 和模板 ID，然后执行 Alembic 迁移。

订阅消息模板需要按以下字段顺序配置，否则微信会拒绝发送：

- `thing1`：菜品
- `thing2`：点菜人或接单人
- `time3`：计划用餐时间

微信订阅消息不是永久授权：每次用户在小程序内点击允许，通常只获得一次发送机会。
本项目会在发起点菜和接单前请求授权，并在服务端记录剩余次数。

## 验证与构建

```powershell
npm run type-check
npm run test
npm run build:mp-weixin
```

生产构建会强制检查 API 地址和两个模板 ID，并拒绝使用非 HTTPS API。
