# YY私厨 AI 智能厨房助手 v2.0 改造计划

## Summary

- 目标：将当前“基于家庭菜品列表 + 单次多模态输入的 AI 推荐”升级为“基于 RAG + Agent + 多模态 + 可确认执行”的 AI 智能厨房助手。
- 落地策略：采用分阶段演进，优先在现有 `frontend/src/pages/MessagesPage.vue` 的 AI 聊天入口上升级，不另起新页面作为首期主入口。
- 首期能力边界：
  - Agent 可以调用 `菜谱 RAG 工具 / 食材分析工具 / 家庭偏好工具`
  - Agent 输出建议，并支持用户“一键确认生成购物清单”
  - Agent 不直接无确认写入业务数据
- 检索与存储策略：
  - 本地开发首期使用 `Chroma`
  - 线上正式形态按 `pgvector` 规划
  - 代码层先抽象向量检索接口，避免后续替换时重写业务服务
- 数据底座策略：首期补齐结构化家庭知识，新增菜品食材、步骤、偏好数据，而不是继续只依赖 `dishes.name / description`

## Current State Analysis

### 现有 AI 能力

- `backend/app/services/ai_chat.py`
  - 当前通过 `build_system_prompt()` 将家庭菜品列表直接拼进 prompt。
  - 支持文本输入和单张冰箱图片输入。
  - 每次调用只生成“总结 + 推荐菜 + 所需食材 + 做法”。
  - 不具备工具调用、知识检索、任务规划或动作确认能力。
- `backend/app/services/ai_provider.py`
  - 当前是单一 OpenAI 兼容调用封装。
  - 只负责 `chat/completions` 调用和结构化 JSON 解析。
  - 没有 Agent orchestration、tool schema、rerank 或 retrieval 逻辑。
- `backend/app/models/ai_chat.py`
  - 当前只有 `AiChatConversation`、`AiChatMessage`、`FridgeImageAnalysis`。
  - 已支持 AI 对话历史、图片分析记录，但未沉淀“检索 chunk / 工具结果 / 任务执行草案 / 用户确认动作”。
- `backend/app/api/v1/ai_chat.py`
  - 当前只暴露对话列表、消息历史、发送消息、删除对话。
  - 不支持工具调用轨迹、推荐依据、确认执行动作。

### 现有家庭知识基础

- `backend/app/models/dish.py`
  - 当前菜品只有 `name / description / price / image_url / is_available`。
  - 缺少 RAG 和精确推荐真正需要的 `食材 / 步骤 / 时长 / 标签 / 难度 / 偏好` 等结构化字段。
- `backend/app/models/order.py`
  - 当前已有订单、订单明细、状态日志、单次评价。
  - 可作为家庭偏好工具的历史输入之一，但粒度偏粗。
- `backend/app/schemas/dish.py`
  - 当前创建/更新菜品请求不支持食材和步骤。
- `YY私厨_详细设计方案.md`
  - 产品文档中已经规划了 `ingredients / dish_ingredients / dish_steps / dish_preferences / food_inventory`。
  - 说明产品目标和当前代码之间存在“设计已想清、代码尚未补齐”的差距。

### 现有前端入口

- `frontend/src/pages/MessagesPage.vue`
  - 当前已经有 `家庭聊天 / AI聊天` 双 tab。
  - AI 区域支持会话切换、上传图片、展示推荐卡片。
  - 很适合作为 v2.0 首期入口继续演进。
- `frontend/src/stores/aiChat.ts`
  - 当前 store 只处理“发送一条消息，拿回一轮回答”。
  - 不支持 Agent 状态、工具执行、确认动作、草案卡片。
- `frontend/src/types/aiChat.ts`
  - 当前消息结构以 `recommendations / recognized_ingredients / fridge_image` 为主。
  - 需要扩展为可表达检索来源、工具调用结果、购物清单草案、确认态。

### 关键结论

1. 当前系统已经具备 AI 会话、图片上传、结构化返回、前端卡片渲染的基础。
2. 当前系统还没有真正的 RAG 底座，也没有 Agent 运行时。
3. 如果不先补齐结构化家庭知识，v2.0 只能停留在“更复杂的 prompt 工程”，无法成为稳定的智能厨房助手。

## Proposed Changes

### Phase 1：补齐家庭知识底座，为 RAG 和工具调用准备可检索数据

#### 1. 后端数据模型扩展

- 新增模型文件：
  - `backend/app/models/ingredient.py`
  - `backend/app/models/dish_ingredient.py`
  - `backend/app/models/dish_step.py`
  - `backend/app/models/dish_preference.py`
- 更新已有文件：
  - `backend/app/models/dish.py`
  - `backend/app/models/__init__.py`
- 目标与做法：
  - 为家庭内菜品建立结构化知识，而不是只靠自由文本描述。
  - `Ingredient` 保存家庭食材实体。
  - `DishIngredient` 维护菜品与食材的关系、数量、单位、是否可选。
  - `DishStep` 保存步骤序号、内容、可选时长。
  - `DishPreference` 保存家庭成员或家庭级口味偏好。
- 为什么现在做：
  - `菜谱 RAG 工具` 需要高质量 chunk 来源。
  - `购物清单草案` 需要明确“推荐菜缺哪些食材”。
  - `家庭偏好工具` 需要可靠偏好数据，而不只是从订单备注弱推断。

#### 2. 数据迁移与初始化

- 新增 Alembic 迁移文件：
  - `backend/alembic/versions/<timestamp>_add_dish_knowledge_tables.py`
- 迁移内容：
  - 创建 `ingredients / dish_ingredients / dish_steps / dish_preferences`
  - 为历史菜品补默认空记录，不强制一次性填满全部数据
  - 保证新模型被 `backend/app/models/__init__.py` 正确导入
- 初始化策略：
  - 先允许旧菜品逐步补录，避免一次迁移把所有历史数据卡死
  - 为 AI 检索增加“结构化优先，弱结构兜底”的知识生成策略

#### 3. 菜品接口与前端表单扩展

- 更新后端文件：
  - `backend/app/schemas/dish.py`
  - `backend/app/services/dish.py`
  - `backend/app/repositories/dish.py`
  - `backend/app/api/v1/dishes.py`
- 更新前端文件：
  - `frontend/src/types/dish.ts`
  - `frontend/src/api/dish.ts`
  - `frontend/src/stores/dish.ts`
  - 与菜品创建/编辑相关页面（按仓库实际页面继续扩展）
- 改造重点：
  - 菜品新增/编辑支持维护食材清单、步骤、偏好信息
  - 返回菜品详情时带出知识化字段，供 AI 与业务页面共用

### Phase 2：引入 RAG 底座，形成“家庭私有知识 + 外部菜谱知识”的双层检索

#### 1. 向量检索抽象

- 新增文件：
  - `backend/app/services/vector_store.py`
  - `backend/app/services/embeddings.py`
  - `backend/app/services/rag_indexer.py`
  - `backend/app/services/rag_retriever.py`
- 目标与做法：
  - 定义统一接口，例如：
    - `upsert_documents(...)`
    - `query_similar_documents(...)`
    - `delete_documents_by_source(...)`
  - 开发环境实现：`ChromaVectorStore`
  - 线上规划实现：`PgVectorStore`
- 为什么不直接把 Chroma 写死：
  - 你已经明确本地先用 Chroma、线上用 pgvector。
  - 业务层如果直接绑定 Chroma，后续上线会重复改 `Agent / RAG / 索引任务` 逻辑。

#### 2. 配置与环境变量扩展

- 更新文件：
  - `backend/app/core/config.py`
  - `backend/.env.example`
  - `docker-compose.yml`
  - `docker-compose.preview.yml`
  - `docker-compose.prod.yml`
- 新增配置建议：
  - `AI_EMBEDDING_MODEL`
  - `AI_VECTOR_BACKEND=chroma|pgvector`
  - `CHROMA_PERSIST_DIR`
  - `PGVECTOR_TABLE_PREFIX`
  - `RAG_TOP_K`
  - `RAG_SCORE_THRESHOLD`
- 部署规划：
  - 开发：Docker 内挂载 Chroma 持久化目录
  - 生产：复用 PostgreSQL，引入 `pgvector` 扩展与向量表

#### 3. 知识分层设计

- 新增文件：
  - `backend/app/schemas/rag.py`
- 文档来源分三层：
  1. 家庭私有菜品知识
     - 来源：`dishes + ingredients + dish_steps + dish_preferences`
  2. 家庭行为偏好知识
     - 来源：`meal_orders + meal_order_items + meal_reviews + ai_chat_messages`
  3. 外部菜谱知识库
     - 来源：首期可通过离线导入脚本落地到本地文档目录，再进行 chunk 和索引
- 新增脚本建议：
  - `backend/scripts/rebuild_rag_index.ps1`
  - `backend/scripts/import_recipe_knowledge.ps1`

#### 4. Chunk 策略

- 家庭菜品 chunk：
  - 以“单个菜品”为主 chunk，包含基础信息、食材、步骤、偏好摘要
- 家庭历史偏好 chunk：
  - 以“用户-菜品偏好摘要”或“家庭偏好摘要”为聚合 chunk
- 外部菜谱 chunk：
  - 以“菜谱说明 / 做法技巧 / 食材替代建议”切分
- 检索策略：
  - 先查家庭私有知识
  - 不足时补充外部菜谱知识
  - 返回来源标签，供前端展示“推荐依据”

### Phase 3：把现有 AI 聊天升级为可用 Agent

#### 1. Agent Runtime

- 新增文件：
  - `backend/app/services/agent_runtime.py`
  - `backend/app/services/agent_tools.py`
  - `backend/app/schemas/agent.py`
- Agent 编排决策：
  - 一个主 Agent 负责理解用户意图、决定是否调用工具、整合结果并生成最终回答
  - 不做多 Agent 并行自治系统，避免首期复杂度过高
- 运行时流程：
  1. 读取当前对话上下文
  2. 判断用户目标：推荐、补货、搭配、识别、计划
  3. 调用一个或多个工具
  4. 汇总证据并生成结构化答案
  5. 如果涉及业务写入，先返回“待确认草案”

#### 2. 首期工具集

- `菜谱 RAG 工具`
  - 依赖：`rag_retriever.py`
  - 功能：检索适合的家庭菜品、相近做法、替代食材、做法注意点
- `食材分析工具`
  - 复用并扩展：
    - `backend/app/services/ai_provider.py`
    - `backend/app/services/ai_chat.py`
    - `backend/app/models/ai_chat.py`
  - 功能：识别图片中的食材，输出置信度、标准化食材名、可疑项
- `家庭偏好工具`
  - 新增或扩展：
    - `backend/app/services/family_preference.py`
  - 数据来源：
    - `dish_preferences`
    - `meal_reviews`
    - `meal_orders.note`
    - `ai_chat_messages` 中的长期偏好表达
  - 功能：总结“谁喜欢什么、不吃什么、最近吃腻了什么、谁更常做什么”

#### 3. AI 会话与消息结构升级

- 更新文件：
  - `backend/app/models/ai_chat.py`
  - `backend/app/schemas/ai_chat.py`
  - `backend/app/repositories/ai_chat.py`
  - `backend/app/services/ai_chat.py`
- 新增消息扩展字段建议：
  - `message_kind` 增加：
    - `tool_result`
    - `plan`
    - `draft_action`
  - `metadata_json` 增加：
    - `retrieval_sources`
    - `tool_calls`
    - `action_draft`
    - `confirmation_required`
    - `confidence`
- 这样前端可以区分：
  - 普通推荐回答
  - 识别结果
  - 购物清单草案
  - 等待用户确认的动作

#### 4. Provider 能力升级

- 更新文件：
  - `backend/app/services/ai_provider.py`
- 增加能力：
  - 聊天模型调用与多模态输入继续保留
  - 补充 embedding 调用能力，供索引和检索使用
  - 为 Agent 提供结构化 tool-call 解析接口
- 注意：
  - 不要求底层模型必须原生 function calling
  - 首期可采用“结构化 JSON 意图 + 服务端路由工具”的折中方案

### Phase 4：引入“一键确认生成购物清单”的闭环

#### 1. 购物清单领域落地

- 现状说明：
  - 当前仓库还没有 `shopping_lists` 模块实现，只有产品文档中已规划。
- 新增后端文件建议：
  - `backend/app/models/shopping_list.py`
  - `backend/app/repositories/shopping_list.py`
  - `backend/app/services/shopping_list.py`
  - `backend/app/schemas/shopping_list.py`
  - `backend/app/api/v1/shopping_lists.py`
- 更新文件：
  - `backend/app/api/v1/router.py`
  - `backend/app/models/__init__.py`
- 首期能力：
  - Agent 根据推荐菜和现有家庭食材信息生成购物清单草案
  - 用户确认后，后端写入正式购物清单
  - 购物清单中的每项要标记来源：
    - `source_type=ai_agent`
    - `source_reference=conversation_id / message_id`

#### 2. Agent 确认动作接口

- 新增文件：
  - `backend/app/api/v1/ai_agent.py`
  - 或在 `backend/app/api/v1/ai_chat.py` 中新增确认路由
- 接口建议：
  - `POST /api/v1/ai-chat/actions/{action_id}/confirm`
  - `POST /api/v1/ai-chat/actions/{action_id}/cancel`
- 设计原则：
  - Agent 先产出草案，不直接写业务表
  - 用户明确确认后，才调用 `shopping_list_service`

#### 3. 前端确认交互

- 更新文件：
  - `frontend/src/types/aiChat.ts`
  - `frontend/src/api/aiChat.ts`
  - `frontend/src/stores/aiChat.ts`
  - `frontend/src/pages/MessagesPage.vue`
- 新增组件建议：
  - `frontend/src/components/AiActionDraftCard.vue`
  - `frontend/src/components/AiRetrievalSources.vue`
  - `frontend/src/components/AiToolTrace.vue`
- 首期展示内容：
  - 推荐依据
  - 识别到的食材
  - 缺失食材列表
  - 生成购物清单按钮
  - 已确认 / 已取消状态

### Phase 5：上线与部署策略

#### 1. 开发环境

- 向量库：`Chroma`
- 原因：
  - 快速起步
  - 与当前单体项目集成轻
  - 方便离线重建索引

#### 2. 生产环境

- 向量库：`pgvector`
- 原因：
  - 当前项目已使用 PostgreSQL，运维复杂度最低
  - 家庭私有知识规模不大，pgvector 足够支撑首期在线检索
  - 与业务表同库或近库管理，便于事务追踪、备份和权限控制
- 对计划的直接影响：
  - 必须从第一天就引入 `VectorStore` 抽象
  - 不能把 Chroma collection 名、查询语义、返回结构直接散落在业务代码里

#### 3. Docker 与部署编排

- 更新文件：
  - `docker-compose.yml`
  - `docker-compose.preview.yml`
  - `docker-compose.prod.yml`
  - `backend/Dockerfile`
- 规划内容：
  - 开发环境增加 Chroma 持久化卷
  - 生产环境为 PostgreSQL 增加 `pgvector` 初始化与迁移说明
  - 增加索引重建命令入口，而不是把索引构建耦合进应用启动

## Assumptions & Decisions

- 已确认采用分阶段落地，而不是一次性重写整个 AI 模块。
- 已确认主入口继续使用现有 `MessagesPage.vue` 中的 AI 聊天。
- 已确认首期 Agent 工具集为：
  - 菜谱 RAG 工具
  - 食材分析工具
  - 家庭偏好工具
- 已确认首期用户确认动作优先落在“生成购物清单”。
- 已确认本地开发 `Chroma`、线上部署 `pgvector`。
- 已确认首期要补齐 `菜品食材 / 步骤 / 偏好` 结构化数据。
- 默认继续沿用当前 OpenAI 兼容模型接入方式，不在本期切换整套模型接入协议。
- 默认首期只覆盖 Web 端，不同步扩展 `miniprogram/`。
- 默认购物清单模块尚未存在，需要在 v2.0 中一并补建。

## Verification Steps

1. 数据层验证
   - Alembic 成功创建 `ingredients / dish_ingredients / dish_steps / dish_preferences`
   - 历史菜品仍可正常读取
   - 新菜品可以完整保存结构化知识

2. RAG 验证
   - 执行索引构建脚本后，家庭菜品知识与外部菜谱知识均可入库
   - AI 对同一道菜的推荐能够返回检索来源
   - 开发环境可跑 Chroma，生产规划可切换为 pgvector 实现

3. Agent 验证
   - 用户上传冰箱图时，Agent 能先调用食材分析工具
   - 用户询问“今晚吃什么”时，Agent 能组合调用菜谱 RAG 工具和家庭偏好工具
   - 返回结果中能区分普通回答、工具结果和待确认草案

4. 业务闭环验证
   - 当 Agent 判断缺少食材时，能生成购物清单草案
   - 用户点击确认后，成功写入购物清单业务表
   - 取消后不写入业务数据

5. 前端验证
   - `MessagesPage.vue` 仍保留现有 AI 聊天体验
   - 能展示推荐依据、工具轨迹、购物清单草案与确认状态
   - 现有家庭聊天和旧 AI 会话列表无回归

6. 回归验证
   - `backend/app/tests/test_ai_chat.py` 继续通过并补充 Agent/RAG 场景
   - `frontend/src/stores/aiChat.test.ts` 补充工具结果与确认流测试
   - 现有订单、评价、菜品 CRUD 不受影响

## 实施顺序建议

1. 先补 `菜品食材 / 步骤 / 偏好` 结构化表和接口。
2. 再加 `VectorStore + Chroma` 与索引构建脚本。
3. 再把 `ai_chat` 升级为 Agent Runtime。
4. 最后补 `shopping_list` 领域和确认执行闭环。

这样推进的原因很简单：先把知识底座打稳，再谈 Agent；先让 Agent 会“看”和“想”，再让它在用户确认后“做”。
