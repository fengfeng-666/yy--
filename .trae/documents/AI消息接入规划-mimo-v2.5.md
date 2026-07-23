# AI 消息接入规划（mimo-v2.5）

## Summary

- 目标：在现有 Web 消息页中新增 `家庭聊天 / AI聊天` 两个入口，其中 `AI聊天` 为“个人私聊 AI”，不与家庭成员共享。
- AI 能力：支持文本多轮对话、基于当前家庭已有菜品库推荐菜品、用户上传冰箱图片后识别食材并给出多个推荐结果。
- 模型接入：后端通过 OpenAI 兼容接口接入 `mimo-v2.5`，使用 `base_url + api_key + model` 配置。
- 首期返回内容：推荐多个菜品，每个菜品包含星级评分、所需食材、做法步骤；优先从当前家庭 `dishes` 菜品库中推荐。
- 图片策略：冰箱图片从 AI 输入区附件按钮上传，后端保存原图和识别结果；识别与推荐都沉淀进 AI 对话记录。

## Current State Analysis

### 现有前端

- `frontend/src/pages/MessagesPage.vue`
  - 当前只有“家庭聊天”单页形态，包含消息列表、轮询拉新、上滑加载历史、底部输入框。
  - 页面标题、消息列表、输入区均围绕家庭消息设计，没有会话切换或附件上传能力。
- `frontend/src/stores/chat.ts`
  - 仅管理家庭聊天状态：`messages / hasMore / initialLoading / olderLoading / polling / sending / unreadCount / connectionError`。
  - 轮询接口固定是 `/chat/messages`，并带未读计数逻辑。
- `frontend/src/api/chat.ts` 与 `frontend/src/types/chat.ts`
  - 只有家庭聊天接口与类型：拉消息、发消息、未读数、标记已读。
- `frontend/src/layouts/MainLayout.vue`
  - 底部导航“消息”入口已存在，未读角标来自家庭聊天 store。

### 现有后端

- `backend/app/api/v1/chat.py`
  - 已提供家庭聊天 API：`GET /chat/messages`、`POST /chat/messages`、`GET /chat/unread-count`、`POST /chat/read`。
- `backend/app/models/chat.py`
  - 当前只有家庭消息表 `chat_messages` 与已读游标表 `chat_read_states`，字段不区分消息类型，不支持 AI 对话。
- `backend/app/services/chat.py` 与 `backend/app/repositories/chat.py`
  - 当前逻辑仅处理“家庭内用户消息”，没有模型调用、图片附件、结构化推荐结果。
- `backend/app/core/config.py`
  - 现有配置已支持 `.env` 读取，也已引入 `httpx` 依赖，适合直接扩展 AI provider 配置。
- `backend/app/services/dish.py`
  - 已有菜品图片上传与本地落盘逻辑，可提炼成 AI 冰箱图片上传的复用基础。
- `backend/app/models/dish.py` 与 `backend/app/models/order.py`
  - 当前菜品数据仅有 `name / description / price / image_url / is_available`，没有“菜品食材清单”字段。
  - 订单表可提供历史点单上下文，但首期推荐主依据仍应是“当前已有菜品库 + 用户输入/冰箱图”。

### 已确认的产品决策

- AI 会话归属：个人私聊 AI。
- 首期覆盖范围：仅 Web 端消息页。
- 模型接入方式：OpenAI 兼容接口。
- 推荐范围：优先当前家庭已有菜品库。
- 图片入口：AI 输入区附件按钮。
- 图片保存：保存原图和识别结果。
- 回复内容：推荐多个菜品，返回星级、所需食材、做法。

### 明确不在本期范围

- 小程序 AI 聊天入口。
- WebSocket / SSE 流式输出。
- 通用食材库存管理后台。
- 家庭共享 AI 会话。
- 基于向量检索或复杂排序模型的推荐系统。

## Proposed Changes

### 一、后端数据模型与迁移

- 新增 `backend/app/models/ai_chat.py`
  - 新建 `AiChatMessage` 表，字段建议：
    - `id`
    - `family_id`：用于限定可推荐的家庭菜品范围
    - `user_id`：AI 对话归属到个人
    - `role`：`user | assistant`
    - `content`：原始文本内容
    - `message_kind`：`text | fridge_image | recommendation`
    - `metadata_json`：JSON，存结构化推荐结果、识别出的食材、图片信息
    - `created_at`
  - 新建 `FridgeImageAnalysis` 表，字段建议：
    - `id`
    - `family_id`
    - `user_id`
    - `image_url`
    - `recognized_ingredients_json`
    - `raw_model_output`
    - `created_at`
  - 这样可以把“聊天记录”和“冰箱识别结果”都落库，满足后续追溯和再次展示。
- 更新 `backend/app/models/__init__.py`
  - 导入新模型，确保 Alembic 自动发现。
- 新增 Alembic 迁移
  - 路径：`backend/alembic/versions/<timestamp>_add_ai_chat_tables.py`
  - 创建 `ai_chat_messages`、`fridge_image_analyses` 两张表，并建立 `(family_id, user_id, id)` 索引，便于按用户分页拉历史消息。

### 二、后端配置与 Provider 封装

- 更新 `backend/app/core/config.py`
  - 新增配置项：
    - `ai_enabled: bool`
    - `ai_base_url: str`
    - `ai_api_key: str`
    - `ai_model: str = "mimo-v2.5"`
    - `ai_timeout_seconds: int`
    - `ai_max_history_messages: int`
  - 在生产环境校验中增加 AI 配置检查：当 `ai_enabled=true` 时必须提供上述关键参数。
- 更新 `backend/.env.example`
  - 补充 AI 配置示例，便于本地与部署环境设置。
- 新增 `backend/app/services/ai_provider.py`
  - 用 `httpx.AsyncClient` 封装 OpenAI 兼容调用。
  - 对外提供一个统一方法，例如 `generate_ai_recommendation(...)`。
  - 内部负责：
    - 拼接 `Authorization: Bearer`
    - 调用 `POST {base_url}/chat/completions`
    - 发送文本和图片内容
    - 处理超时、非 2xx、空响应、JSON 解析失败

### 三、后端上传与 AI 业务服务

- 新增 `backend/app/services/upload.py`
  - 将 `backend/app/services/dish.py` 中图片校验与落盘逻辑抽为通用工具。
  - 保留现有菜品上传能力，同时新增 AI 冰箱图片保存目录：
    - `uploads/families/{family_id}/ai/fridge/`
  - 避免在 `dish.py` 与 AI 服务中重复维护图片规则。
- 新增 `backend/app/repositories/ai_chat.py`
  - 提供以下能力：
    - 分页查询当前用户 AI 消息历史
    - 创建 AI 用户消息
    - 创建 AI 助手消息
    - 创建冰箱图片识别记录
    - 查询最近 N 条 AI 对话上下文
- 新增 `backend/app/schemas/ai_chat.py`
  - 定义请求/响应模型：
    - `AiChatMessageProfile`
    - `AiChatMessagePage`
    - `AiRecommendationItem`
    - `FridgeImageAnalysisProfile`
    - `AiChatMetadata`
    - `AiChatTurnResponse`
  - `AiRecommendationItem` 固定结构：
    - `dish_name`
    - `rating`
    - `required_ingredients`
    - `matched_ingredients`
    - `steps`
    - `reason`
- 新增 `backend/app/services/ai_chat.py`
  - 业务入口设计：
    - `list_ai_messages_for_user(...)`
    - `create_ai_turn(...)`
  - `create_ai_turn(...)` 的固定流程：
    1. 校验当前用户已加入家庭。
    2. 如带图片，先落盘保存原图。
    3. 拉取当前家庭可用菜品列表 `dishes`，只取 `is_available = true` 的数据作为推荐候选。
    4. 拉取该用户最近若干条 AI 历史消息，组成上下文。
    5. 构造 system prompt，明确要求模型优先从已有菜品库中推荐，并输出严格 JSON。
    6. 若有冰箱图，使用多模态消息体一并发给模型；图片通过 base64 data URL 传输，而不是本地 `/uploads` 地址。
    7. 解析模型返回 JSON，生成：
       - 识别出的食材列表
       - 推荐菜清单
       - 文本摘要
    8. 持久化一条 `user` 消息和一条 `assistant` 消息；如有图片，再持久化 `FridgeImageAnalysis`。
    9. 返回完整 turn，供前端一次性更新列表。
  - Prompt 约束要点：
    - 优先推荐当前家庭已有菜品；若匹配度不足，可降级给“接近的做法建议”，但首选仍是已有菜名。
    - 输出 1~5 星评分。
    - 每个推荐给出所需食材、匹配到的现有食材、简要做法。
    - 若看不清图片，要明确说明识别不确定。
  - 错误处理策略：
    - provider 调用失败时，接口返回统一业务异常 `"AI 服务暂时不可用，请稍后再试"`。
    - 模型返回非 JSON 时，服务端尝试一次提取 JSON 块；仍失败则返回错误，不落 assistant 消息脏数据。

### 四、后端 API 暴露

- 新增 `backend/app/api/v1/ai_chat.py`
  - 路由前缀：`/ai-chat`
  - 新增接口：
    - `GET /api/v1/ai-chat/messages`
      - 参数：`before_id`, `limit`
      - 用于 AI 聊天历史分页。
    - `POST /api/v1/ai-chat/messages`
      - `multipart/form-data`
      - 字段：
        - `content: string`
        - `image: UploadFile | None`
      - 返回：`AiChatTurnResponse`
      - 一次请求同步完成“保存用户输入 -> 调模型 -> 保存 assistant 回复 -> 返回 turn”
- 更新 `backend/app/api/v1/router.py`
  - 注册 `ai_chat_router`。

### 五、前端类型、API 与 Store

- 新增 `frontend/src/types/aiChat.ts`
  - 对齐后端 AI 消息结构，定义：
    - `AiChatMessage`
    - `AiChatMessagePage`
    - `AiRecommendationItem`
    - `FridgeImageAnalysis`
    - `AiChatTurnResponse`
- 新增 `frontend/src/api/aiChat.ts`
  - 提供：
    - `fetchAiChatMessages(params)`
    - `sendAiChatMessage({ content, imageFile })`
  - `sendAiChatMessage` 使用 `FormData`。
- 新增 `frontend/src/stores/aiChat.ts`
  - 独立于现有 `chat.ts`，避免污染家庭聊天逻辑。
  - 状态建议：
    - `messages`
    - `hasMore`
    - `initialLoading`
    - `olderLoading`
    - `sending`
    - `selectedImage`
    - `connectionError`
  - 核心动作：
    - `loadInitialMessages`
    - `loadOlderMessages`
    - `sendMessage`
    - `setSelectedImage`
    - `clearSelectedImage`
    - `reset`
  - 不做未读数与轮询；AI 聊天仅在进入页面时加载历史和用户发送后刷新本地状态。

### 六、前端消息页改造

- 更新 `frontend/src/pages/MessagesPage.vue`
  - 将页面改为两个分段入口：
    - `家庭聊天`
    - `AI聊天`
  - 保留原有家庭聊天区块和现有 `useChatStore` 行为不变。
  - 新增 AI 聊天区块：
    - 单独的 AI 消息列表
    - 分页加载更早消息
    - AI 回复卡片化展示推荐结果
    - 输入区附件按钮，用于选择冰箱图片
    - 图片预览条，可删除重新选择
    - 发送后显示“AI 正在思考”加载态
  - 交互细节固定如下：
    - 默认进入消息页时停留在“家庭聊天”标签，避免影响现有使用习惯。
    - 只有切换到“AI聊天”时才加载 AI 历史。
    - 如果没有家庭，`家庭聊天` 和 `AI聊天` 都显示 `NoFamilyState`，因为 AI 推荐也依赖家庭菜品库。
    - AI 消息中如果包含 `recommendations`，渲染为多张推荐卡：
      - 菜名
      - 星级
      - 所需食材
      - 匹配到的食材
      - 做法步骤
      - 推荐理由
    - 若有 `fridge_image.image_url`，在用户消息中展示缩略图。
- 可按需新增轻量展示组件
  - `frontend/src/components/AiRecommendationCard.vue`
  - `frontend/src/components/AiImageAttachmentPreview.vue`
  - 这样能让 `MessagesPage.vue` 不至于过度膨胀。

### 七、推荐与提示词策略

- 推荐数据源固定为：
  - 当前家庭 `dishes` 表中的可用菜品。
  - 用户文本输入。
  - 可选冰箱图片识别结果。
- 首期不新增“菜品食材表”，因此 prompt 中要告诉模型：
  - 菜品库只提供菜名、描述等弱结构信息。
  - 如果数据库没有完整食材明细，可根据常见做法估算“所需食材”，但要优先与用户已提供/识别出的食材匹配。
- 服务端构造给模型的候选菜品清单格式建议为：
  - `dish_id`
  - `name`
  - `description`
  - `price`
  - `is_available`
- 服务端要求模型输出 JSON 结构示例：

```json
{
  "summary": "根据冰箱现有食材，比较适合做以下几道菜。",
  "recognized_ingredients": ["鸡蛋", "番茄", "葱"],
  "recommendations": [
    {
      "dish_name": "番茄炒蛋",
      "rating": 5,
      "required_ingredients": ["番茄", "鸡蛋", "盐", "油"],
      "matched_ingredients": ["番茄", "鸡蛋"],
      "steps": ["番茄切块", "鸡蛋打散炒熟", "混合翻炒调味"],
      "reason": "现有食材匹配度高，做法简单。"
    }
  ]
}
```

### 八、测试与回归覆盖

- 新增 `backend/app/tests/test_ai_chat.py`
  - 覆盖场景：
    - 获取 AI 历史消息成功
    - 仅文本发起 AI 对话成功
    - 文本 + 图片发起 AI 对话成功
    - 未加入家庭时请求失败
    - AI provider 失败时返回统一错误
    - 模型返回非法 JSON 时失败
  - 使用 mock/stub 替代真实模型调用，避免测试依赖外部网络。
- 更新或新增前端测试
  - `frontend/src/stores/aiChat.test.ts`
    - 测试拉历史、发消息、选择图片、失败回滚。
  - 如页面已有测试基础不足，可优先补 store 级测试，不强行补整页组件测试。

## Assumptions & Decisions

- AI 对话为“个人私聊”，但仍绑定 `family_id`，因为推荐候选来自当前家庭菜品库。
- AI 首期只做一个默认会话流，不引入“多个 AI 会话列表”。
- AI 回复采用同步等待完整结果，不做流式输出。
- 冰箱图片通过消息输入区附件按钮提交，单次请求最多一张图。
- AI 图片分析与推荐合并为一次后端处理，不拆成“先识别、再推荐”两个接口。
- 前端“消息”底部导航和家庭聊天未读角标保持现状；AI 聊天不引入未读概念。
- 推荐结果允许模型根据常见做法补全“所需食材”和“做法”，但推荐菜名优先命中当前家庭已有菜品。
- 若模型无法可靠识别图片，仍返回一条 assistant 消息，说明识别不确定并建议补充文字描述。

## Verification Steps

1. 配置验证
   - 在 `backend/.env` 中配置 `AI_ENABLED / AI_BASE_URL / AI_API_KEY / AI_MODEL`。
   - 启动后端，确认配置校验通过。
2. 数据库验证
   - 执行 Alembic 迁移，确认新增 AI 聊天与冰箱识别表。
3. 后端接口验证
   - 调 `GET /api/v1/ai-chat/messages`，空会话时返回空列表。
   - 调 `POST /api/v1/ai-chat/messages` 发送文本，返回 `user_message + assistant_message`。
   - 调 `POST /api/v1/ai-chat/messages` 发送文本和图片，确认图片落盘且返回识别结果与推荐列表。
4. 前端交互验证
   - 打开消息页，能在 `家庭聊天 / AI聊天` 间切换。
   - 家庭聊天行为保持原状，不受 AI 功能影响。
   - AI 聊天可以上传图片、预览图片、发送文本、显示推荐卡片。
5. 回归验证
   - 现有家庭聊天接口、菜品图片上传、订单相关功能无回归。
   - 前后端新增测试通过，最近编辑文件无诊断错误。
