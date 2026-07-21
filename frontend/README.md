# YY私厨 Frontend

这是基于 `Vue 3 + TypeScript + Vite` 初始化的前端工程，已经完成第一层应用壳搭建：

- Vue Router 基础路由
- Pinia 状态管理接入
- Vant 组件库接入
- Axios 请求实例
- 移动端优先的 YY 私厨主题样式
- 首页、菜单、点菜、计划、我的、登录等基础页面占位

## 启动方式

### 1. 安装依赖

```bash
npm install
```

### 2. 启动前端开发服务

```bash
npm run dev
```

前端会固定运行在：

- `http://localhost:5174`

### 3. 前后端联调说明

- 默认后端接口地址：`http://localhost:8001/api/v1`
- 如需修改，可通过 `VITE_API_BASE_URL` 覆盖
- 后端默认 CORS 已允许 `http://localhost:5174`

## 检查命令

```bash
npm run check
npm run test
```
