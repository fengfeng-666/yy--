# YY私厨——双人家庭点菜与用餐管理应用详细设计方案

> 项目名称：YY私厨  
> 项目定位：只属于两个人的家庭点菜、做饭协作与用餐记录应用  
> 目标用户：伴侣  
> 推荐技术栈：Vue 3 + TypeScript + FastAPI + PostgreSQL + Capacitor  
> 文档版本：V1.0  
> 创建日期：2026-07-21

---

# 1. 项目背景

日常家庭生活中，“今天吃什么”是一个高频但容易消耗精力的问题。

常见场景包括：

- 两个人都不知道吃什么。
- 一个人想吃某道菜，但不知道对方是否愿意做。
- 家里会做的菜很多，但临时想不起来。
- 决定好菜单后，才发现缺少食材。
- 同一道菜做过很多次，但每次口味要求都要重新沟通。
- 过去吃过什么、哪道菜最受欢迎，没有统一记录。
- 想规划一周菜单，但缺少方便的工具。

YY私厨的目标不是做一个面向大众的菜谱平台，而是做一个专属于两个人的家庭私厨系统。

核心闭环如下：

```text
管理菜品
   ↓
浏览家庭菜单
   ↓
发起点菜
   ↓
对方确认
   ↓
准备食材
   ↓
开始制作
   ↓
完成用餐
   ↓
双方评价
   ↓
沉淀用餐记录
```

---

# 2. 产品定位

## 2.1 一句话定位

YY私厨是一款面向双人家庭的私人点菜与用餐管理应用，用于解决“今天吃什么、谁来做、缺什么食材、吃得怎么样”的完整家庭用餐问题。

## 2.2 核心价值

### 对点菜者

- 可以浏览家里真正会做的菜。
- 可以直接向对方点菜。
- 可以填写口味和时间要求。
- 可以查看点菜进度。

### 对做饭者

- 可以明确知道对方想吃什么。
- 可以查看制作步骤和特殊口味。
- 可以快速判断缺少哪些食材。
- 可以接受、修改或拒绝点菜请求。

### 对两个人

- 减少每天讨论“吃什么”的时间。
- 建立共同维护的家庭菜单。
- 记录共同生活中的每一顿饭。
- 通过统计和回忆增强产品的情感价值。

---

# 3. 产品目标与非目标

## 3.1 第一阶段目标

第一阶段需要打通最核心的使用闭环：

```text
创建家庭空间
→ 添加菜品
→ 浏览菜单
→ 发起点菜
→ 对方确认
→ 标记制作完成
→ 记录评价
```

## 3.2 第二阶段目标

在核心闭环稳定后增加：

- 一周菜单计划。
- 购物清单。
- 随机选菜。
- 双人投票。
- 食材库存。
- 用餐相册。
- 数据统计。

## 3.3 第三阶段目标

增加 AI 能力：

- AI 推荐今晚吃什么。
- 根据库存推荐菜品。
- 图片识别食材。
- AI 生成菜谱。
- 根据双方历史偏好自动调整推荐。

## 3.4 暂不考虑

第一版暂时不做以下内容：

- 面向公众开放注册。
- 菜品社区。
- 用户关注与评论。
- 商家入驻。
- 外卖下单。
- 在线支付。
- 多家庭切换。
- 复杂积分或竞争排行。
- 过度精细的营养计算。

---

# 4. 用户与角色设计

系统虽然只有两个人使用，但仍然建议保留标准的角色和权限模型，便于以后扩展。

## 4.1 用户角色

### 家庭管理员

默认由创建家庭空间的人担任。

权限：

- 修改家庭名称和封面。
- 邀请另一位成员。
- 管理菜品。
- 管理菜品分类。
- 管理食材。
- 修改家庭设置。
- 查看全部用餐记录。
- 删除错误记录。

### 家庭成员

权限：

- 浏览菜品。
- 发起点菜。
- 接受或拒绝点菜。
- 修改自己创建的内容。
- 参与评价。
- 查看共同历史。

## 4.2 双人限制

当前版本一个家庭最多两名成员。

数据库设计上不建议写死为两个字段，而应使用 `family_members` 关系表，并在业务层限制人数不超过 2。

这样以后需要扩展为三口之家时，不需要修改数据库结构。

---

# 5. 用户故事

## 5.1 菜品管理

- 作为家庭成员，我希望添加一道家里会做的菜，方便以后点菜。
- 作为家庭成员，我希望上传菜品图片，让菜单更直观。
- 作为家庭成员，我希望标记谁会做这道菜。
- 作为家庭成员，我希望记录制作时长和难度。
- 作为家庭成员，我希望记录对方的特殊口味要求。
- 作为家庭成员，我希望暂时下架某道菜，而不是删除它。

## 5.2 点菜

- 作为点菜者，我希望一次选择多道菜。
- 作为点菜者，我希望选择用餐日期和时间。
- 作为点菜者，我希望指定谁来做。
- 作为点菜者，我希望填写“少糖、不要香菜”等备注。
- 作为接单者，我希望接受、拒绝或提出修改。
- 作为接单者，我希望查看缺少哪些食材。
- 作为双方，我希望查看当前点菜进度。

## 5.3 用餐记录

- 作为家庭成员，我希望在吃完后评分。
- 作为家庭成员，我希望记录本次菜品照片。
- 作为家庭成员，我希望记录“下次少放盐”等建议。
- 作为家庭成员，我希望查看过去一周、一个月吃过什么。

## 5.4 用餐计划

- 作为家庭成员，我希望安排未来一周的菜单。
- 作为家庭成员，我希望标记某天外出吃饭。
- 作为家庭成员，我希望系统自动汇总需要购买的食材。

## 5.5 智能选择

- 作为家庭成员，我希望点击“随机选菜”快速得到结果。
- 作为家庭成员，我希望排除最近刚吃过的菜。
- 作为家庭成员，我希望只推荐 30 分钟以内能做完的菜。
- 作为家庭成员，我希望双方分别选择后，由系统找出共同想吃的菜。

---

# 6. 功能模块总览

```text
YY私厨
├── 身份认证
│   ├── 登录
│   ├── 注册
│   ├── 刷新令牌
│   └── 退出登录
│
├── 家庭空间
│   ├── 创建家庭
│   ├── 邀请成员
│   ├── 加入家庭
│   ├── 家庭信息
│   └── 家庭成员
│
├── 菜品管理
│   ├── 菜品列表
│   ├── 菜品详情
│   ├── 新增菜品
│   ├── 编辑菜品
│   ├── 上架/下架
│   ├── 菜品分类
│   └── 菜品食材
│
├── 点菜中心
│   ├── 发起点菜
│   ├── 点菜详情
│   ├── 接受点菜
│   ├── 拒绝点菜
│   ├── 修改建议
│   ├── 制作状态
│   └── 完成用餐
│
├── 用餐计划
│   ├── 日历视图
│   ├── 一周菜单
│   ├── 外出用餐
│   └── 菜单复制
│
├── 购物清单
│   ├── 自动生成
│   ├── 手工添加
│   ├── 购买状态
│   └── 负责人
│
├── 用餐记录
│   ├── 历史记录
│   ├── 双方评价
│   ├── 用餐照片
│   └── 改进建议
│
├── 智能工具
│   ├── 随机选菜
│   ├── 双人投票
│   └── 条件筛选
│
└── 我的
    ├── 个人资料
    ├── 饮食偏好
    ├── 菜品管理
    ├── 家庭设置
    ├── 数据统计
    └── 系统设置
```

---

# 7. 信息架构与导航

推荐底部导航使用五个入口：

```text
首页 | 菜单 | 点菜 | 计划 | 我的
```

## 7.1 首页

首页用于快速查看当天最重要的信息：

- 今日日期。
- 今日早餐、午餐、晚餐安排。
- 待处理点菜请求。
- 当前制作中的菜单。
- 随机选菜入口。
- 最近常吃。
- 家庭提醒。
- 缺少食材提醒。

## 7.2 菜单

菜单用于浏览家庭菜品：

- 分类筛选。
- 关键词搜索。
- 制作时长筛选。
- 难度筛选。
- 当前可做筛选。
- 谁会做筛选。
- 收藏菜品。
- 最近没吃筛选。

## 7.3 点菜

点菜模块用于创建和处理订单：

- 我发起的。
- 对方发起的。
- 待确认。
- 已接受。
- 制作中。
- 已完成。
- 已取消。

## 7.4 计划

计划模块用于安排未来：

- 日历。
- 一周菜单。
- 购物清单。
- 外出用餐。
- 愿望菜单。

## 7.5 我的

我的模块用于个人与管理设置：

- 个人资料。
- 饮食偏好。
- 家庭信息。
- 菜品管理。
- 食材管理。
- 分类管理。
- 数据统计。
- 通知设置。
- 退出登录。

---

# 8. 页面详细设计

# 8.1 登录页

## 页面内容

- 应用 Logo。
- 手机号或用户名。
- 密码。
- 登录按钮。
- 注册入口。
- 忘记密码入口。
- 记住登录状态。

## 第一版简化建议

因为只有两个人使用，可以暂时采用：

- 用户名 + 密码。
- 不接短信验证码。
- 不接第三方登录。
- 账号由管理员创建。

---

# 8.2 创建家庭页

## 字段

- 家庭名称。
- 家庭封面。
- 创建人昵称。
- 邀请码。

## 示例

```text
家庭名称：YY私厨
家庭描述：只属于我们的两人食堂
邀请码：YY2026
```

---

# 8.3 首页

## 页面区域

### 顶部区域

- 当前家庭名称。
- 双方头像。
- 日期。
- 通知入口。

### 今日菜单卡片

显示：

- 早餐。
- 午餐。
- 晚餐。
- 当前状态。
- 负责人。

### 点菜请求卡片

显示：

- 发起人。
- 菜品。
- 用餐时间。
- 备注。
- 接受按钮。
- 修改按钮。
- 拒绝按钮。

### 快捷功能

- 发起点菜。
- 随机选菜。
- 安排一周。
- 添加菜品。

### 最近常吃

展示最近 4～6 道菜。

### 温馨数据

例如：

- 本月一起吃饭 18 次。
- 本月你做饭 9 次。
- 最受欢迎菜品：糖醋排骨。
- 已经 20 天没有吃火锅。

---

# 8.4 菜单列表页

## 卡片字段

- 菜品图片。
- 菜品名称。
- 菜品分类。
- 制作时间。
- 难度。
- 默认厨师。
- 双方平均评分。
- 最近一次吃的时间。
- 当前是否可点。

## 操作

- 查看详情。
- 加入点菜单。
- 收藏。
- 编辑。
- 下架。

## 筛选项

```text
分类：全部 / 荤菜 / 素菜 / 汤 / 主食 / 甜品
时长：15分钟以内 / 30分钟以内 / 60分钟以内
难度：简单 / 普通 / 复杂
厨师：我会做 / 对方会做 / 都会做
状态：可点 / 暂不可点
历史：最近没吃 / 经常吃 / 高评分
```

---

# 8.5 菜品详情页

## 页面内容

### 基础信息

- 菜品大图。
- 菜品名称。
- 菜品描述。
- 分类标签。
- 难度。
- 制作时间。
- 辣度。
- 默认厨师。

### 所需食材

示例：

```text
排骨 500g
冰糖 30g
生抽 2勺
醋 3勺
姜 5片
```

### 制作步骤

```text
1. 排骨焯水。
2. 炒糖色。
3. 加入排骨翻炒。
4. 加入调味料炖煮。
5. 大火收汁。
```

### 双方口味偏好

```text
睿丰：正常甜度，多放芝麻
老婆：少糖，不要太肥，多留一点酱汁
```

### 历史信息

- 做过次数。
- 最近一次制作日期。
- 双方平均评分。
- 最近一次评价。

### 操作按钮

- 点这道菜。
- 加入愿望菜单。
- 编辑菜品。
- 下架菜品。

---

# 8.6 新增菜品页

## 必填字段

- 菜品名称。
- 菜品分类。
- 菜品状态。

## 推荐字段

- 菜品图片。
- 描述。
- 制作时间。
- 难度。
- 默认厨师。
- 辣度。
- 是否适合工作日。
- 是否适合减脂。
- 是否需要提前准备。
- 食材列表。
- 制作步骤。
- 双方备注。

## 表单结构

```text
基础信息
├── 名称
├── 图片
├── 分类
├── 描述
└── 状态

制作信息
├── 制作时长
├── 难度
├── 默认厨师
├── 辣度
└── 是否需要提前准备

食材信息
├── 食材名称
├── 数量
├── 单位
└── 是否可选

制作步骤
├── 步骤序号
├── 步骤描述
└── 步骤图片

家庭偏好
├── 睿丰备注
└── 老婆备注
```

---

# 8.7 发起点菜页

## 操作流程

```text
选择菜品
→ 选择用餐时间
→ 选择做饭人
→ 填写备注
→ 确认提交
```

## 字段

- 菜品，可多选。
- 用餐类型：早餐、午餐、晚餐、夜宵。
- 用餐日期。
- 预计用餐时间。
- 指定厨师。
- 是否允许对方修改。
- 备注。
- 是否同步生成购物清单。

## 示例

```text
菜品：糖醋排骨、清炒生菜
用餐：今晚 19:00
厨师：睿丰
备注：排骨少糖，生菜不要蒜
允许修改：是
```

---

# 8.8 点菜详情页

## 展示信息

- 发起人。
- 接单人。
- 菜品列表。
- 用餐日期。
- 用餐时间。
- 当前状态。
- 点菜备注。
- 修改记录。
- 食材准备情况。
- 状态时间线。

## 状态时间线

```text
18:00 发起点菜
18:05 对方接受
18:20 开始准备食材
18:40 开始制作
19:10 已上菜
20:00 完成用餐
```

---

# 8.9 用餐评价页

每个人分别提交评价。

## 评价字段

- 总体评分，1～5 分。
- 味道评分。
- 卖相评分。
- 份量评分。
- 下次是否还想吃。
- 本次评价。
- 下次改进建议。
- 上传照片。

## 限制

- 每个用户对同一次用餐只能评价一次。
- 完成用餐后才能评价。
- 可以修改自己的评价。
- 不能修改对方评价。

---

# 8.10 一周计划页

采用周日历或横向卡片。

## 页面示例

```text
周一
午餐：外出
晚餐：番茄炒蛋 + 米饭

周二
晚餐：糖醋排骨 + 清炒生菜

周三
晚餐：待安排
```

## 操作

- 添加菜单。
- 复制昨天菜单。
- 复制上周菜单。
- 标记外出。
- 自动生成购物清单。
- 一键随机安排。

---

# 8.11 购物清单页

## 数据来源

- 系统根据菜单自动生成。
- 用户手工添加。
- 从菜品详情直接加入。

## 字段

- 食材名称。
- 数量。
- 单位。
- 来源菜品。
- 是否已购买。
- 负责人。
- 备注。

## 示例

```text
□ 排骨 500g      负责人：睿丰
□ 西红柿 4个     负责人：老婆
☑ 鸡蛋 1盒       已购买
```

---

# 8.12 我的页面

## 个人资料

- 头像。
- 昵称。
- 登录账号。
- 个人简介。

## 饮食偏好

- 喜欢的口味。
- 不喜欢的食材。
- 过敏食材。
- 辣度。
- 饭量。
- 是否减脂。
- 是否控制糖分。

## 家庭设置

- 家庭名称。
- 家庭封面。
- 邀请码。
- 成员列表。
- 通知设置。

## 管理入口

- 菜品管理。
- 分类管理。
- 食材管理。
- 标签管理。
- 数据统计。

---

# 9. 核心业务流程

# 9.1 家庭创建流程

```text
用户注册
   ↓
创建家庭空间
   ↓
系统生成邀请码
   ↓
另一位用户注册
   ↓
输入邀请码
   ↓
加入家庭
   ↓
家庭成员数达到 2
```

## 业务规则

- 一个用户只能加入一个家庭。
- 一个家庭最多两人。
- 邀请码必须唯一。
- 已加入家庭的用户不能重复加入。
- 管理员不能直接删除另一位成员，需要二次确认。

---

# 9.2 菜品创建流程

```text
进入我的
   ↓
菜品管理
   ↓
新增菜品
   ↓
填写基础信息
   ↓
添加食材与步骤
   ↓
保存草稿或直接上架
```

## 菜品状态

```text
DRAFT       草稿
ACTIVE      已上架
INACTIVE    已下架
ARCHIVED    已归档
```

---

# 9.3 点菜流程

```text
发起点菜
   ↓
订单状态：PENDING
   ↓
对方查看
   ├── 接受 → ACCEPTED
   ├── 拒绝 → REJECTED
   └── 提出修改 → NEGOTIATING
                     ↓
                双方确认
                     ↓
                  ACCEPTED
   ↓
PREPARING
   ↓
COOKING
   ↓
SERVED
   ↓
COMPLETED
```

---

# 9.4 点菜状态机

| 状态 | 中文含义 | 可以执行的操作 |
|---|---|---|
| PENDING | 待确认 | 接受、拒绝、提出修改、取消 |
| NEGOTIATING | 协商中 | 接受修改、继续修改、取消 |
| ACCEPTED | 已接受 | 开始准备、取消 |
| PREPARING | 准备食材 | 开始制作、取消 |
| COOKING | 制作中 | 标记上菜 |
| SERVED | 已上菜 | 完成用餐 |
| COMPLETED | 已完成 | 评价、查看记录 |
| REJECTED | 已拒绝 | 重新发起 |
| CANCELLED | 已取消 | 查看记录 |

## 状态约束

- 只有被指定的接单人可以接受或拒绝。
- 发起人可以在 `PENDING` 状态取消。
- 进入 `COOKING` 后不能直接删除订单。
- 完成订单后自动生成用餐记录。
- 已完成订单不允许修改菜品，只能补充评价和照片。

---

# 10. 数据库设计

推荐数据库：PostgreSQL。

推荐 ORM：SQLAlchemy 2.0。

推荐迁移工具：Alembic。

---

# 10.1 users 用户表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| username | VARCHAR(50) | 登录名，唯一 |
| password_hash | VARCHAR(255) | 密码哈希 |
| nickname | VARCHAR(50) | 昵称 |
| avatar_url | VARCHAR(500) | 头像 |
| status | VARCHAR(20) | ACTIVE/DISABLED |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

---

# 10.2 families 家庭表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| name | VARCHAR(100) | 家庭名称 |
| description | VARCHAR(255) | 家庭描述 |
| cover_url | VARCHAR(500) | 家庭封面 |
| invite_code | VARCHAR(20) | 邀请码，唯一 |
| owner_id | UUID | 创建者 |
| max_members | INT | 最大成员数，默认 2 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

---

# 10.3 family_members 家庭成员表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| family_id | UUID | 家庭 ID |
| user_id | UUID | 用户 ID |
| role | VARCHAR(20) | OWNER/MEMBER |
| joined_at | TIMESTAMP | 加入时间 |

## 唯一约束

```text
UNIQUE(family_id, user_id)
UNIQUE(user_id)
```

---

# 10.4 dish_categories 菜品分类表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| family_id | UUID | 家庭 ID |
| name | VARCHAR(50) | 分类名称 |
| icon | VARCHAR(50) | 图标 |
| sort_order | INT | 排序 |
| created_at | TIMESTAMP | 创建时间 |

---

# 10.5 dishes 菜品表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| family_id | UUID | 家庭 ID |
| category_id | UUID | 分类 ID |
| name | VARCHAR(100) | 菜品名称 |
| description | TEXT | 描述 |
| cover_url | VARCHAR(500) | 封面 |
| cooking_minutes | INT | 制作时长 |
| difficulty | INT | 难度 1～5 |
| spicy_level | INT | 辣度 0～5 |
| status | VARCHAR(20) | 状态 |
| default_cook_id | UUID | 默认厨师 |
| need_prepare_ahead | BOOLEAN | 是否提前准备 |
| suitable_for_weekday | BOOLEAN | 是否适合工作日 |
| is_favorite | BOOLEAN | 是否收藏 |
| created_by | UUID | 创建人 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | 软删除时间 |

---

# 10.6 ingredients 食材表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| family_id | UUID | 家庭 ID |
| name | VARCHAR(100) | 食材名称 |
| category | VARCHAR(50) | 食材分类 |
| default_unit | VARCHAR(20) | 默认单位 |
| created_at | TIMESTAMP | 创建时间 |

---

# 10.7 dish_ingredients 菜品食材关系表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| dish_id | UUID | 菜品 ID |
| ingredient_id | UUID | 食材 ID |
| quantity | DECIMAL(10,2) | 数量 |
| unit | VARCHAR(20) | 单位 |
| is_optional | BOOLEAN | 是否可选 |
| note | VARCHAR(255) | 备注 |

---

# 10.8 dish_steps 制作步骤表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| dish_id | UUID | 菜品 ID |
| step_no | INT | 步骤序号 |
| content | TEXT | 步骤描述 |
| image_url | VARCHAR(500) | 步骤图片 |
| duration_minutes | INT | 预计耗时 |

---

# 10.9 dish_preferences 菜品个性偏好表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| dish_id | UUID | 菜品 ID |
| user_id | UUID | 用户 ID |
| preference_note | TEXT | 个人口味备注 |
| updated_at | TIMESTAMP | 更新时间 |

---

# 10.10 meal_orders 点菜订单表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| family_id | UUID | 家庭 ID |
| requester_id | UUID | 发起人 |
| cook_id | UUID | 指定厨师 |
| meal_type | VARCHAR(20) | BREAKFAST/LUNCH/DINNER/SNACK |
| planned_date | DATE | 计划日期 |
| planned_time | TIME | 计划时间 |
| status | VARCHAR(30) | 点菜状态 |
| note | TEXT | 点菜备注 |
| allow_modify | BOOLEAN | 是否允许修改 |
| rejection_reason | TEXT | 拒绝原因 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| completed_at | TIMESTAMP | 完成时间 |

---

# 10.11 meal_order_items 点菜明细表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| meal_order_id | UUID | 点菜订单 ID |
| dish_id | UUID | 菜品 ID |
| quantity | INT | 份数 |
| note | VARCHAR(255) | 单道菜备注 |
| sort_order | INT | 排序 |

---

# 10.12 order_status_logs 订单状态日志表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| meal_order_id | UUID | 订单 ID |
| from_status | VARCHAR(30) | 原状态 |
| to_status | VARCHAR(30) | 新状态 |
| operator_id | UUID | 操作人 |
| note | VARCHAR(255) | 说明 |
| created_at | TIMESTAMP | 时间 |

---

# 10.13 meal_reviews 用餐评价表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| meal_order_id | UUID | 点菜订单 ID |
| user_id | UUID | 评价人 |
| overall_score | DECIMAL(2,1) | 总体评分 |
| taste_score | DECIMAL(2,1) | 味道评分 |
| appearance_score | DECIMAL(2,1) | 卖相评分 |
| portion_score | DECIMAL(2,1) | 份量评分 |
| want_again | BOOLEAN | 是否还想吃 |
| comment | TEXT | 评价 |
| improvement_note | TEXT | 改进建议 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 唯一约束

```text
UNIQUE(meal_order_id, user_id)
```

---

# 10.14 meal_photos 用餐照片表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| meal_order_id | UUID | 订单 ID |
| uploader_id | UUID | 上传人 |
| image_url | VARCHAR(500) | 图片地址 |
| caption | VARCHAR(255) | 图片说明 |
| created_at | TIMESTAMP | 上传时间 |

---

# 10.15 meal_plans 用餐计划表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| family_id | UUID | 家庭 ID |
| plan_date | DATE | 日期 |
| meal_type | VARCHAR(20) | 餐次 |
| plan_type | VARCHAR(20) | HOME/OUTSIDE/SKIP |
| note | VARCHAR(255) | 备注 |
| created_by | UUID | 创建人 |
| created_at | TIMESTAMP | 创建时间 |

---

# 10.16 meal_plan_items 计划菜品表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| meal_plan_id | UUID | 计划 ID |
| dish_id | UUID | 菜品 ID |
| quantity | INT | 份数 |

---

# 10.17 shopping_lists 购物清单表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| family_id | UUID | 家庭 ID |
| name | VARCHAR(100) | 清单名称 |
| status | VARCHAR(20) | ACTIVE/COMPLETED |
| source_type | VARCHAR(20) | MANUAL/ORDER/PLAN |
| source_id | UUID | 来源 ID |
| created_at | TIMESTAMP | 创建时间 |

---

# 10.18 shopping_list_items 购物项表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| shopping_list_id | UUID | 清单 ID |
| ingredient_id | UUID | 食材 ID |
| name | VARCHAR(100) | 快照名称 |
| quantity | DECIMAL(10,2) | 数量 |
| unit | VARCHAR(20) | 单位 |
| assignee_id | UUID | 负责人 |
| is_purchased | BOOLEAN | 是否已购买 |
| purchased_at | TIMESTAMP | 购买时间 |
| note | VARCHAR(255) | 备注 |

---

# 10.19 food_inventory 食材库存表

第二阶段实现。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID | 主键 |
| family_id | UUID | 家庭 ID |
| ingredient_id | UUID | 食材 ID |
| quantity | DECIMAL(10,2) | 当前数量 |
| unit | VARCHAR(20) | 单位 |
| expire_date | DATE | 保质期 |
| updated_at | TIMESTAMP | 更新时间 |

---

# 11. 数据关系说明

```text
users
  └── family_members
         └── families
                ├── dishes
                │    ├── dish_ingredients
                │    ├── dish_steps
                │    └── dish_preferences
                │
                ├── meal_orders
                │    ├── meal_order_items
                │    ├── order_status_logs
                │    ├── meal_reviews
                │    └── meal_photos
                │
                ├── meal_plans
                │    └── meal_plan_items
                │
                └── shopping_lists
                     └── shopping_list_items
```

---

# 12. API 设计

统一前缀：

```text
/api/v1
```

统一响应结构：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

错误响应：

```json
{
  "code": 40001,
  "message": "菜品不存在",
  "data": null
}
```

---

# 12.1 认证接口

## 注册

```http
POST /api/v1/auth/register
```

请求：

```json
{
  "username": "ruifeng",
  "password": "******",
  "nickname": "睿丰"
}
```

## 登录

```http
POST /api/v1/auth/login
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "xxx",
    "refresh_token": "xxx",
    "token_type": "bearer",
    "user": {
      "id": "uuid",
      "nickname": "睿丰"
    }
  }
}
```

## 刷新令牌

```http
POST /api/v1/auth/refresh
```

## 当前用户

```http
GET /api/v1/users/me
```

---

# 12.2 家庭接口

```http
POST   /api/v1/families
GET    /api/v1/families/current
PATCH  /api/v1/families/current
POST   /api/v1/families/join
GET    /api/v1/families/current/members
POST   /api/v1/families/current/regenerate-invite-code
```

---

# 12.3 菜品接口

```http
GET    /api/v1/dishes
POST   /api/v1/dishes
GET    /api/v1/dishes/{dish_id}
PATCH  /api/v1/dishes/{dish_id}
DELETE /api/v1/dishes/{dish_id}
POST   /api/v1/dishes/{dish_id}/activate
POST   /api/v1/dishes/{dish_id}/deactivate
```

查询参数示例：

```text
GET /api/v1/dishes?category_id=xxx&cook_id=xxx&max_minutes=30&status=ACTIVE&keyword=排骨
```

创建菜品请求：

```json
{
  "name": "糖醋排骨",
  "category_id": "uuid",
  "description": "酸甜口家庭常做菜",
  "cooking_minutes": 45,
  "difficulty": 3,
  "spicy_level": 0,
  "default_cook_id": "uuid",
  "need_prepare_ahead": false,
  "suitable_for_weekday": true,
  "ingredients": [
    {
      "ingredient_id": "uuid",
      "quantity": 500,
      "unit": "g",
      "is_optional": false
    }
  ],
  "steps": [
    {
      "step_no": 1,
      "content": "排骨焯水",
      "duration_minutes": 10
    }
  ],
  "preferences": [
    {
      "user_id": "uuid",
      "preference_note": "少糖，多留一点汁"
    }
  ]
}
```

---

# 12.4 菜品分类接口

```http
GET    /api/v1/dish-categories
POST   /api/v1/dish-categories
PATCH  /api/v1/dish-categories/{category_id}
DELETE /api/v1/dish-categories/{category_id}
```

---

# 12.5 点菜接口

```http
GET    /api/v1/meal-orders
POST   /api/v1/meal-orders
GET    /api/v1/meal-orders/{order_id}
POST   /api/v1/meal-orders/{order_id}/accept
POST   /api/v1/meal-orders/{order_id}/reject
POST   /api/v1/meal-orders/{order_id}/propose-change
POST   /api/v1/meal-orders/{order_id}/confirm-change
POST   /api/v1/meal-orders/{order_id}/start-preparing
POST   /api/v1/meal-orders/{order_id}/start-cooking
POST   /api/v1/meal-orders/{order_id}/serve
POST   /api/v1/meal-orders/{order_id}/complete
POST   /api/v1/meal-orders/{order_id}/cancel
```

创建点菜请求：

```json
{
  "cook_id": "uuid",
  "meal_type": "DINNER",
  "planned_date": "2026-07-21",
  "planned_time": "19:00:00",
  "allow_modify": true,
  "note": "排骨少糖",
  "items": [
    {
      "dish_id": "uuid",
      "quantity": 1,
      "note": "多留一点汁"
    },
    {
      "dish_id": "uuid",
      "quantity": 1,
      "note": "不要蒜"
    }
  ]
}
```

---

# 12.6 评价接口

```http
GET   /api/v1/meal-orders/{order_id}/reviews
POST  /api/v1/meal-orders/{order_id}/reviews
PATCH /api/v1/meal-orders/{order_id}/reviews/me
```

---

# 12.7 用餐计划接口

```http
GET    /api/v1/meal-plans?start_date=2026-07-20&end_date=2026-07-26
POST   /api/v1/meal-plans
PATCH  /api/v1/meal-plans/{plan_id}
DELETE /api/v1/meal-plans/{plan_id}
POST   /api/v1/meal-plans/generate-shopping-list
```

---

# 12.8 购物清单接口

```http
GET    /api/v1/shopping-lists
POST   /api/v1/shopping-lists
GET    /api/v1/shopping-lists/{list_id}
POST   /api/v1/shopping-lists/{list_id}/items
PATCH  /api/v1/shopping-lists/{list_id}/items/{item_id}
DELETE /api/v1/shopping-lists/{list_id}/items/{item_id}
POST   /api/v1/shopping-lists/{list_id}/complete
```

---

# 12.9 首页聚合接口

为了减少手机端请求次数，建议提供首页聚合接口：

```http
GET /api/v1/dashboard
```

响应内容：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "today_plans": [],
    "pending_orders": [],
    "active_order": null,
    "recent_dishes": [],
    "stats": {
      "meal_count_this_month": 18,
      "my_cook_count": 9,
      "partner_cook_count": 7,
      "favorite_dish": "糖醋排骨"
    }
  }
}
```

---

# 13. 后端架构设计

推荐采用模块化单体架构，不需要一开始拆微服务。

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── families.py
│   │       ├── dishes.py
│   │       ├── categories.py
│   │       ├── meal_orders.py
│   │       ├── meal_plans.py
│   │       ├── shopping_lists.py
│   │       └── dashboard.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── family.py
│   │   ├── dish.py
│   │   ├── ingredient.py
│   │   ├── meal_order.py
│   │   ├── meal_plan.py
│   │   ├── review.py
│   │   └── shopping_list.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── family.py
│   │   ├── dish.py
│   │   ├── meal_order.py
│   │   ├── meal_plan.py
│   │   └── shopping_list.py
│   │
│   ├── repositories/
│   │   ├── dish_repository.py
│   │   ├── order_repository.py
│   │   └── family_repository.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── family_service.py
│   │   ├── dish_service.py
│   │   ├── meal_order_service.py
│   │   ├── meal_plan_service.py
│   │   ├── shopping_service.py
│   │   └── dashboard_service.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── constants.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── migrations/
│   │
│   ├── middleware/
│   │   ├── request_id.py
│   │   ├── logging.py
│   │   └── exception_handler.py
│   │
│   ├── tests/
│   └── main.py
│
├── alembic/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 分层职责

### API 层

- 接收请求。
- 参数校验。
- 调用 Service。
- 返回统一响应。

### Service 层

- 处理业务规则。
- 校验家庭权限。
- 管理订单状态。
- 控制事务。

### Repository 层

- 数据库 CRUD。
- 查询封装。
- 不包含复杂业务规则。

### Model 层

- SQLAlchemy 数据模型。
- 定义表关系和约束。

### Schema 层

- Pydantic 请求和响应模型。

---

# 14. 前端架构设计

```text
frontend/
├── src/
│   ├── api/
│   │   ├── auth.ts
│   │   ├── family.ts
│   │   ├── dish.ts
│   │   ├── mealOrder.ts
│   │   ├── mealPlan.ts
│   │   └── shoppingList.ts
│   │
│   ├── assets/
│   ├── components/
│   │   ├── DishCard.vue
│   │   ├── OrderCard.vue
│   │   ├── EmptyState.vue
│   │   ├── AppHeader.vue
│   │   └── BottomTabBar.vue
│   │
│   ├── composables/
│   │   ├── useAuth.ts
│   │   ├── useFamily.ts
│   │   └── useUpload.ts
│   │
│   ├── layouts/
│   │   ├── MainLayout.vue
│   │   └── AuthLayout.vue
│   │
│   ├── router/
│   │   └── index.ts
│   │
│   ├── stores/
│   │   ├── auth.ts
│   │   ├── family.ts
│   │   ├── dishes.ts
│   │   └── orders.ts
│   │
│   ├── types/
│   │   ├── user.ts
│   │   ├── dish.ts
│   │   ├── mealOrder.ts
│   │   └── common.ts
│   │
│   ├── utils/
│   │   ├── request.ts
│   │   ├── date.ts
│   │   └── storage.ts
│   │
│   ├── views/
│   │   ├── auth/
│   │   ├── home/
│   │   ├── dishes/
│   │   ├── orders/
│   │   ├── plans/
│   │   └── profile/
│   │
│   ├── App.vue
│   └── main.ts
│
├── capacitor.config.ts
├── vite.config.ts
├── package.json
└── tsconfig.json
```

## 推荐前端依赖

```text
Vue 3
TypeScript
Vite
Vue Router
Pinia
Axios
Vant
Day.js
Zod（可选）
Capacitor
```

## UI 推荐

移动端优先，推荐使用 Vant。

原因：

- 组件适合手机端。
- 表单、弹窗、日期选择器较完善。
- 与 Vue 3 配合成熟。
- 第一版开发速度快。

---

# 15. 接口调用与状态管理

## Pinia Store 建议

### authStore

- 当前用户。
- access token。
- refresh token。
- 登录状态。
- 登录、退出、刷新令牌。

### familyStore

- 当前家庭。
- 家庭成员。
- 邀请码。

### dishStore

- 菜品列表。
- 分类列表。
- 当前筛选条件。
- 当前菜品详情。

### orderStore

- 待处理点菜。
- 我发起的点菜。
- 当前制作中的订单。
- 状态更新。

## Token 策略

- access token 有效期 30 分钟。
- refresh token 有效期 30 天。
- Axios 响应拦截器处理 401。
- 刷新失败后跳转登录页。
- 移动端初期可使用安全存储插件或本地存储。
- 正式版本建议使用 Capacitor Secure Storage。

---

# 16. 文件与图片存储

## 开发环境

图片存储在本地目录：

```text
backend/uploads/
├── avatars/
├── dishes/
└── meals/
```

FastAPI 挂载：

```python
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
```

## 正式环境

推荐使用对象存储：

- 阿里云 OSS。
- 腾讯云 COS。
- Cloudflare R2。
- AWS S3。

第一版可以暂时本地存储，后期通过统一的 `FileStorageService` 切换到对象存储。

---

# 17. 通知设计

## 第一版

应用内通知即可：

- 新点菜请求。
- 点菜已接受。
- 点菜被拒绝。
- 对方提出修改。
- 开始制作。
- 已上菜。
- 提醒评价。

## 第二版

Capacitor 推送通知：

- Android 本地通知。
- iOS 本地通知。
- 定时提醒。

## 通知示例

```text
老婆向你点了：糖醋排骨、清炒生菜
计划用餐时间：今晚 19:00
```

---

# 18. 安全设计

虽然只有两个人使用，也要保持基础安全规范。

## 18.1 密码安全

- 使用 Argon2 或 bcrypt。
- 禁止明文密码。
- 密码最少 8 位。
- 登录失败不提示具体用户名是否存在。

## 18.2 权限校验

所有家庭资源必须验证：

```text
当前用户是否属于该资源所在家庭
```

不能只依赖前端隐藏按钮。

## 18.3 数据隔离

所有菜品、订单、计划查询必须附带 `family_id` 条件。

例如：

```python
SELECT * FROM dishes
WHERE id = :dish_id
AND family_id = :current_family_id
```

## 18.4 上传安全

- 限制图片格式。
- 限制图片大小。
- 生成随机文件名。
- 禁止用户控制文件保存路径。
- 对 EXIF 信息进行清理可作为后期优化。

## 18.5 日志脱敏

禁止记录：

- 密码。
- Token。
- 密钥。
- 完整 Authorization Header。

---

# 19. 异常码设计

| 错误码 | 含义 |
|---|---|
| 40000 | 请求参数错误 |
| 40001 | 资源不存在 |
| 40002 | 状态不允许 |
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限 |
| 40301 | 不属于当前家庭 |
| 40900 | 数据冲突 |
| 40901 | 用户已加入家庭 |
| 40902 | 家庭成员已满 |
| 40903 | 重复评价 |
| 50000 | 系统内部错误 |

---

# 20. 日志与可观测性

## 日志字段

```text
timestamp
level
request_id
user_id
family_id
method
path
status_code
duration_ms
message
```

## 关键业务日志

- 用户登录。
- 家庭创建与加入。
- 菜品新增与修改。
- 点菜发起。
- 点菜状态变化。
- 用餐完成。
- 评价提交。
- 图片上传失败。

## 推荐工具

第一版：

- Python logging。
- JSON 日志。
- 本地文件轮转。

后续：

- Sentry。
- Loki + Grafana。
- Prometheus。

---

# 21. 缓存与并发

当前只有两个用户，不需要过早引入 Redis。

第一版：

- 不使用缓存。
- 不使用消息队列。
- 使用 PostgreSQL 事务。
- 订单状态更新使用乐观锁或条件更新。

示例：

```sql
UPDATE meal_orders
SET status = 'ACCEPTED'
WHERE id = :order_id
AND status = 'PENDING';
```

判断受影响行数是否为 1，避免重复接受。

后期增加推送、任务调度时再引入 Redis。

---

# 22. 定时任务

第二阶段可以增加：

- 用餐前 30 分钟提醒。
- 每周日晚生成下周计划提示。
- 食材临期提醒。
- 未评价提醒。
- 长时间未处理点菜提醒。

推荐工具：

- 初期：APScheduler。
- 规模扩大后：Celery + Redis。

当前项目不需要一开始使用 Celery。

---

# 23. 测试方案

## 23.1 后端单元测试

推荐：

```text
pytest
pytest-asyncio
httpx
factory-boy
```

重点测试：

- 用户注册与登录。
- 家庭人数限制。
- 菜品权限。
- 点菜状态机。
- 重复评价。
- 跨家庭访问拦截。
- 自动生成购物清单。

## 23.2 接口测试

覆盖：

- 正常路径。
- 参数错误。
- 未登录。
- 无权限。
- 资源不存在。
- 重复操作。
- 非法状态切换。

## 23.3 前端测试

第一版可以只做：

- 核心组件测试。
- 登录流程。
- 添加菜品流程。
- 发起点菜流程。
- 接受点菜流程。

后期增加：

- Vitest。
- Vue Test Utils。
- Playwright。

---

# 24. MVP 范围

第一版只做真正必要的功能。

## 24.1 MVP 必须功能

### 账号

- 注册。
- 登录。
- 退出。

### 家庭

- 创建家庭。
- 输入邀请码加入家庭。
- 查看成员。

### 菜品

- 菜品分类。
- 新增菜品。
- 编辑菜品。
- 菜品列表。
- 菜品详情。
- 上架和下架。

### 点菜

- 选择菜品。
- 发起点菜。
- 接受。
- 拒绝。
- 开始制作。
- 已上菜。
- 完成用餐。

### 评价

- 双方评分。
- 文字评价。
- 历史记录。

### 首页

- 今日菜单。
- 待处理点菜。
- 快捷入口。

---

# 24.2 MVP 暂缓功能

- 精确食材库存。
- AI 推荐。
- 图片识别。
- 双人投票。
- 购物负责人。
- 营养统计。
- 推送通知。
- 多家庭。
- 公开分享。

---

# 25. 开发阶段拆解

# 阶段 0：项目初始化

## 后端

- 创建 FastAPI 项目。
- 配置 PostgreSQL。
- 配置 SQLAlchemy。
- 配置 Alembic。
- 配置统一响应。
- 配置异常处理。
- 配置日志。
- 配置环境变量。

## 前端

- 创建 Vue 3 + TypeScript 项目。
- 安装 Vue Router。
- 安装 Pinia。
- 安装 Axios。
- 安装 Vant。
- 配置请求封装。
- 配置路由守卫。
- 配置移动端布局。

## 验收标准

- 前后端都能启动。
- 前端能请求健康检查接口。
- Alembic 可以正常迁移。
- 环境变量不写死。

---

# 阶段 1：账号与家庭空间

## 任务

- 用户表。
- 家庭表。
- 家庭成员表。
- 注册接口。
- 登录接口。
- 当前用户接口。
- 创建家庭接口。
- 加入家庭接口。
- 家庭成员接口。
- 登录页。
- 创建家庭页。
- 加入家庭页。

## 验收标准

- 两个账号可以分别登录。
- 用户 A 创建家庭。
- 用户 B 使用邀请码加入。
- 第三个用户无法加入。
- 两个用户能看到彼此。

---

# 阶段 2：菜品管理

## 任务

- 菜品分类表。
- 菜品表。
- 食材表。
- 菜品食材表。
- 制作步骤表。
- 菜品偏好表。
- 菜品 CRUD。
- 图片上传。
- 菜品列表页。
- 菜品详情页。
- 新增和编辑页。
- 分类管理页。

## 验收标准

- 能新增完整菜品。
- 能编辑菜品。
- 能上传图片。
- 能按分类筛选。
- 能上下架。
- 下架菜品不能被新点菜选择。

---

# 阶段 3：点菜闭环

## 任务

- 点菜订单表。
- 点菜明细表。
- 状态日志表。
- 创建点菜接口。
- 接受接口。
- 拒绝接口。
- 开始准备。
- 开始制作。
- 已上菜。
- 完成用餐。
- 点菜列表页。
- 点菜详情页。
- 状态时间线。

## 验收标准

- A 可以向 B 发起点菜。
- B 能接受或拒绝。
- 状态只能按合法流程推进。
- 状态变化有日志。
- 完成后订单不可修改。

---

# 阶段 4：评价和历史

## 任务

- 评价表。
- 用餐照片表。
- 提交评价。
- 修改自己的评价。
- 用餐历史。
- 菜品历史统计。
- 评价页面。
- 历史详情页。

## 验收标准

- 两个人可以分别评价。
- 同一人不能重复提交两条评价。
- 菜品详情能显示历史评分。
- 用餐记录能按日期查看。

---

# 阶段 5：首页和体验优化

## 任务

- 首页聚合接口。
- 今日菜单。
- 待处理请求。
- 最近常吃。
- 快捷入口。
- 空状态。
- 加载状态。
- 错误提示。
- 移动端适配。
- Capacitor 打包。

## 验收标准

- 首页一次请求获得主要数据。
- 手机端操作流畅。
- Android 可以安装运行。
- 两个账号完成真实点菜闭环。

---

# 26. 第一版开发任务清单

```text
[ ] 初始化 FastAPI 项目
[ ] 初始化 Vue 3 + TypeScript 项目
[ ] 配置 PostgreSQL
[ ] 配置 Alembic
[ ] 配置统一响应和异常
[ ] 实现注册登录
[ ] 实现 JWT
[ ] 实现家庭创建
[ ] 实现邀请码加入
[ ] 实现家庭成员限制
[ ] 实现菜品分类
[ ] 实现菜品 CRUD
[ ] 实现图片上传
[ ] 实现菜品列表
[ ] 实现菜品详情
[ ] 实现点菜创建
[ ] 实现点菜状态机
[ ] 实现点菜列表
[ ] 实现点菜详情
[ ] 实现评价
[ ] 实现用餐历史
[ ] 实现首页聚合
[ ] 完成移动端适配
[ ] 使用 Capacitor 打包 Android
[ ] 部署后端与数据库
```

---

# 27. 产品迭代路线

## V1.0：点菜闭环

- 双人账号。
- 家庭空间。
- 菜品管理。
- 发起点菜。
- 接受或拒绝。
- 制作状态。
- 用餐评价。
- 用餐历史。

## V1.1：计划与购物

- 一周菜单。
- 购物清单。
- 菜单复制。
- 外出用餐。
- 随机选菜。

## V1.2：互动与回忆

- 双人投票。
- 用餐相册。
- 愿望菜单。
- 纪念日菜单。
- 月度统计。
- 情侣称号。

## V2.0：AI 私厨助手

- AI 菜单推荐。
- 根据库存推荐。
- 图片识别食材。
- AI 生成菜谱。
- 偏好学习。
- 自然语言点菜。

---

# 28. AI 功能详细构想

## 28.1 AI 菜单推荐

输入条件：

- 最近吃过什么。
- 双方评分。
- 现有食材。
- 计划用餐时间。
- 可接受制作时长。
- 是否工作日。
- 双方口味。
- 是否减脂。
- 天气。

输出：

```json
{
  "recommended_dishes": [
    {
      "dish_id": "uuid",
      "reason": "最近14天没有吃过，双方评分均高于4.5分，且制作时间不超过30分钟"
    }
  ]
}
```

## 28.2 自然语言点菜

用户输入：

```text
今晚想吃两个菜，一个肉菜一个素菜，30分钟内做好，不要辣。
```

系统转换为结构化条件并推荐菜品。

## 28.3 食材图片识别

流程：

```text
拍摄冰箱照片
→ 多模态模型识别食材
→ 用户确认识别结果
→ 写入库存
→ 推荐可制作菜品
```

## 28.4 AI 使用原则

- AI 只做建议，不直接修改核心数据。
- AI 识别结果必须允许人工确认。
- 推荐理由必须可解释。
- 不要让 AI 取代确定性业务逻辑。
- 点菜状态机、权限、数据写入仍由后端规则控制。

---

# 29. 部署方案

## 29.1 开发环境

```text
前端：http://localhost:5174
后端：http://localhost:8001
数据库：localhost:5433
```

## 29.2 Docker Compose

```text
services:
├── frontend
├── backend
├── postgres
└── nginx
```

## 29.3 正式部署推荐

低成本方案：

- 后端：云服务器 Docker。
- 数据库：同一服务器 PostgreSQL。
- 前端：Nginx 静态文件。
- 图片：初期本地磁盘。
- 域名：自定义域名。
- HTTPS：Let's Encrypt。

## 29.4 备份

因为内容具有情感价值，需要定期备份：

- 每天自动备份 PostgreSQL。
- 每周备份上传图片。
- 保留最近 7～30 天备份。
- 支持导出 JSON 或 ZIP。

---

# 30. 环境变量示例

```env
APP_NAME=YY私厨
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5433/yy_kitchen

JWT_SECRET_KEY=replace-with-strong-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=10

CORS_ORIGINS=http://localhost:5174
```

---

# 31. 非功能性要求

## 性能

- 普通接口响应时间小于 500ms。
- 首页聚合接口小于 1s。
- 图片上传需要压缩。
- 列表默认分页 20 条。

## 可用性

- 移动端优先。
- 常用操作不超过 3 步。
- 点菜操作不超过 1 分钟。
- 重要状态使用颜色和图标区分。
- 所有危险操作二次确认。

## 可维护性

- 前后端类型清晰。
- 所有数据库变更通过 Alembic。
- 禁止手动修改生产数据库结构。
- API 统一版本管理。
- 业务状态使用枚举。
- 核心逻辑必须有测试。

## 可扩展性

- 家庭成员表不要写死两个人字段。
- 图片存储使用抽象接口。
- 通知使用独立服务。
- AI 使用独立模块。
- 菜品分类支持自定义。

---

# 32. 交互设计原则

## 32.1 温馨而不是工具化

不要设计得像后台管理系统。

建议使用：

- 温暖的文案。
- 菜品大图。
- 双方头像。
- 用餐回忆卡片。
- 柔和圆角。
- 轻量动画。

## 32.2 状态表达清晰

例如点菜状态：

- 待确认：橙色。
- 已接受：蓝色。
- 制作中：紫色。
- 已上菜：绿色。
- 已完成：灰色。
- 已拒绝：红色。

## 32.3 减少输入

- 常用备注可保存为快捷标签。
- 用餐时间默认今晚。
- 默认厨师自动带出。
- 最近菜品快捷选择。
- 食材支持复用。
- 制作步骤支持拖拽排序。

---

# 33. 推荐文案

## 空状态

```text
还没有菜品，先添加一道你们都爱吃的菜吧。
```

```text
今天还没有安排，看看谁先来点菜。
```

```text
暂时没有待处理的点菜请求。
```

## 点菜通知

```text
老婆向你点了 2 道菜，等你接单。
```

```text
睿丰接受了今晚的菜单。
```

```text
晚饭已经做好，可以开饭啦。
```

## 用餐记录

```text
这是你们一起记录的第 100 顿饭。
```

```text
糖醋排骨已经成为本月最受欢迎的菜。
```

---

# 34. 验收场景

## 场景一：新增菜品

1. 睿丰登录。
2. 进入“我的 → 菜品管理”。
3. 新增糖醋排骨。
4. 添加图片、食材和步骤。
5. 设置默认厨师为睿丰。
6. 设置老婆偏好为“少糖”。
7. 保存并上架。
8. 老婆可以在菜单中看到。

结果：通过。

## 场景二：发起点菜

1. 老婆登录。
2. 在菜单选择糖醋排骨和生菜。
3. 设置今晚 19:00。
4. 指定睿丰制作。
5. 填写“排骨少糖”。
6. 提交。
7. 睿丰首页看到待处理请求。

结果：通过。

## 场景三：完成用餐

1. 睿丰接受点菜。
2. 状态变为“已接受”。
3. 睿丰点击开始准备。
4. 点击开始制作。
5. 点击已上菜。
6. 用餐后点击完成。
7. 双方分别评价。
8. 历史页面生成记录。

结果：通过。

## 场景四：权限隔离

1. 第三方用户获得订单 ID。
2. 尝试请求订单详情。
3. 后端检查其不属于家庭。
4. 返回 403。

结果：通过。

---

# 35. 推荐开发优先级

## P0：必须完成

- 登录注册。
- 家庭空间。
- 菜品管理。
- 点菜订单。
- 状态机。
- 用餐评价。
- 用餐历史。

## P1：完成后明显提升体验

- 首页聚合。
- 图片上传。
- 分类筛选。
- 随机选菜。
- 一周菜单。
- 购物清单。

## P2：增强情感价值

- 用餐相册。
- 纪念日菜单。
- 情侣统计。
- 愿望菜单。
- 双人投票。

## P3：技术探索

- AI 推荐。
- 多模态识别。
- 推送通知。
- 语音点菜。

---

# 36. 最终推荐技术栈

```text
前端语言：
TypeScript

前端框架：
Vue 3 + Vite

移动端 UI：
Vant

状态管理：
Pinia

路由：
Vue Router

网络请求：
Axios

移动端打包：
Capacitor

后端语言：
Python 3.12+

后端框架：
FastAPI

ORM：
SQLAlchemy 2.0

数据库：
PostgreSQL

数据库迁移：
Alembic

认证：
JWT Access Token + Refresh Token

图片存储：
开发阶段本地存储
正式阶段对象存储

部署：
Docker Compose + Nginx

测试：
Pytest + Vitest + Playwright
```

---

# 37. 项目目录建议

```text
F:\my_project\yy私厨
├── backend
├── frontend
├── docs
│   ├── design.md
│   ├── api.md
│   ├── database.md
│   └── deployment.md
├── docker-compose.yml
├── .env.example
└── README.md
```

建议将本设计文档保存为：

```text
F:\my_project\yy私厨\docs\YY私厨-详细设计方案.md
```

---

# 38. 下一步行动

建议严格按照以下顺序开始开发：

```text
第一步：创建前后端项目
第二步：设计并迁移用户、家庭相关表
第三步：完成登录和双人家庭空间
第四步：完成菜品管理
第五步：完成点菜订单状态机
第六步：完成评价和历史
第七步：完善首页和移动端体验
第八步：使用 Capacitor 打包 Android
```

最重要的原则：

> 先做完整闭环，再增加功能；先保证两个人真实可用，再考虑 AI 和复杂扩展。

---

# 39. 项目成功标准

当以下场景能够稳定完成时，第一版即算成功：

- 两个人分别使用自己的账号登录。
- 两个人进入同一个家庭空间。
- 任意一方可以新增家庭菜品。
- 任意一方可以向对方点菜。
- 对方可以接受或拒绝。
- 点菜可以完整流转到“完成用餐”。
- 双方可以独立评价。
- 历史中可以看到菜品、照片和评价。
- 手机端使用体验正常。
- 数据可以备份和恢复。

这时 YY私厨就不再只是一个练习项目，而是一个真正可以进入日常生活长期使用的家庭应用。
