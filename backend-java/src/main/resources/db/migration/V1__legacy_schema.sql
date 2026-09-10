

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 20260721_170000

CREATE TABLE users (
    id SERIAL NOT NULL, 
    username VARCHAR(32) NOT NULL, 
    nickname VARCHAR(32) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    is_active BOOLEAN DEFAULT true NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_username ON users (username);

INSERT INTO alembic_version (version_num) VALUES ('20260721_170000') RETURNING alembic_version.version_num;

-- Running upgrade 20260721_170000 -> 20260721_180000

CREATE TABLE families (
    id SERIAL NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    description VARCHAR(255), 
    cover_url VARCHAR(500), 
    invite_code VARCHAR(20) NOT NULL, 
    owner_id INTEGER NOT NULL, 
    max_members INTEGER DEFAULT '2' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(owner_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX ix_families_invite_code ON families (invite_code);

CREATE TABLE family_members (
    id SERIAL NOT NULL, 
    family_id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    role VARCHAR(16) NOT NULL, 
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(family_id) REFERENCES families (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT uq_family_members_family_user UNIQUE (family_id, user_id), 
    CONSTRAINT uq_family_members_user UNIQUE (user_id)
);

UPDATE alembic_version SET version_num='20260721_180000' WHERE alembic_version.version_num = '20260721_170000';

-- Running upgrade 20260721_180000 -> 20260722_120000

CREATE TABLE dish_categories (
    id SERIAL NOT NULL, 
    family_id INTEGER NOT NULL, 
    name VARCHAR(50) NOT NULL, 
    sort_order INTEGER DEFAULT '0' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(family_id) REFERENCES families (id) ON DELETE CASCADE, 
    CONSTRAINT uq_dish_categories_family_name UNIQUE (family_id, name)
);

CREATE TABLE dishes (
    id SERIAL NOT NULL, 
    family_id INTEGER NOT NULL, 
    category_id INTEGER NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    description VARCHAR(500), 
    price FLOAT DEFAULT '0' NOT NULL, 
    image_url VARCHAR(500), 
    is_available BOOLEAN DEFAULT true NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(category_id) REFERENCES dish_categories (id) ON DELETE RESTRICT, 
    FOREIGN KEY(family_id) REFERENCES families (id) ON DELETE CASCADE
);

UPDATE alembic_version SET version_num='20260722_120000' WHERE alembic_version.version_num = '20260721_180000';

-- Running upgrade 20260722_120000 -> 20260722_150000

CREATE TABLE meal_orders (
    id SERIAL NOT NULL, 
    family_id INTEGER NOT NULL, 
    requester_id INTEGER NOT NULL, 
    cook_id INTEGER NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    planned_date DATE NOT NULL, 
    planned_time TIME WITHOUT TIME ZONE, 
    note VARCHAR(500), 
    accepted_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(cook_id) REFERENCES users (id) ON DELETE RESTRICT, 
    FOREIGN KEY(family_id) REFERENCES families (id) ON DELETE CASCADE, 
    FOREIGN KEY(requester_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE TABLE meal_order_items (
    id SERIAL NOT NULL, 
    meal_order_id INTEGER NOT NULL, 
    dish_id INTEGER NOT NULL, 
    quantity INTEGER DEFAULT '1' NOT NULL, 
    note VARCHAR(255), 
    sort_order INTEGER DEFAULT '0' NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(dish_id) REFERENCES dishes (id) ON DELETE RESTRICT, 
    FOREIGN KEY(meal_order_id) REFERENCES meal_orders (id) ON DELETE CASCADE
);

CREATE TABLE order_status_logs (
    id SERIAL NOT NULL, 
    meal_order_id INTEGER NOT NULL, 
    from_status VARCHAR(30), 
    to_status VARCHAR(30) NOT NULL, 
    operator_id INTEGER NOT NULL, 
    note VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(meal_order_id) REFERENCES meal_orders (id) ON DELETE CASCADE, 
    FOREIGN KEY(operator_id) REFERENCES users (id) ON DELETE RESTRICT
);

UPDATE alembic_version SET version_num='20260722_150000' WHERE alembic_version.version_num = '20260722_120000';

-- Running upgrade 20260722_150000 -> 20260722_170000

CREATE TABLE meal_reviews (
    id SERIAL NOT NULL, 
    meal_order_id INTEGER NOT NULL, 
    reviewer_id INTEGER NOT NULL, 
    rating INTEGER NOT NULL, 
    content VARCHAR(500), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(meal_order_id) REFERENCES meal_orders (id) ON DELETE CASCADE, 
    FOREIGN KEY(reviewer_id) REFERENCES users (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_meal_reviews_order UNIQUE (meal_order_id)
);

UPDATE alembic_version SET version_num='20260722_170000' WHERE alembic_version.version_num = '20260722_150000';

-- Running upgrade 20260722_170000 -> 20260722_180000

ALTER TABLE dishes DROP CONSTRAINT dishes_category_id_fkey;

ALTER TABLE dishes DROP COLUMN category_id;

DROP TABLE dish_categories;

UPDATE alembic_version SET version_num='20260722_180000' WHERE alembic_version.version_num = '20260722_170000';

-- Running upgrade 20260722_180000 -> 20260722_190000

ALTER TABLE users ADD COLUMN wechat_openid VARCHAR(128);

ALTER TABLE users ADD COLUMN wechat_unionid VARCHAR(128);

CREATE UNIQUE INDEX ix_users_wechat_openid ON users (wechat_openid);

CREATE INDEX ix_users_wechat_unionid ON users (wechat_unionid);

CREATE TABLE wechat_subscriptions (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    event_type VARCHAR(40) NOT NULL, 
    available_count INTEGER DEFAULT '0' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT uq_wechat_subscriptions_user_event UNIQUE (user_id, event_type)
);

CREATE INDEX ix_wechat_subscriptions_user_id ON wechat_subscriptions (user_id);

CREATE TABLE wechat_notifications (
    id SERIAL NOT NULL, 
    recipient_id INTEGER NOT NULL, 
    meal_order_id INTEGER, 
    event_type VARCHAR(40) NOT NULL, 
    template_id VARCHAR(128) NOT NULL, 
    page VARCHAR(255) NOT NULL, 
    payload JSON NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    attempt_count INTEGER DEFAULT '0' NOT NULL, 
    error_message VARCHAR(500), 
    sent_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(meal_order_id) REFERENCES meal_orders (id) ON DELETE SET NULL, 
    FOREIGN KEY(recipient_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_wechat_notifications_meal_order_id ON wechat_notifications (meal_order_id);

CREATE INDEX ix_wechat_notifications_recipient_id ON wechat_notifications (recipient_id);

CREATE INDEX ix_wechat_notifications_status ON wechat_notifications (status);

UPDATE alembic_version SET version_num='20260722_190000' WHERE alembic_version.version_num = '20260722_180000';

-- Running upgrade 20260722_190000 -> 20260723_100000

CREATE TABLE chat_messages (
    id SERIAL NOT NULL, 
    family_id INTEGER NOT NULL, 
    sender_id INTEGER NOT NULL, 
    content TEXT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(family_id) REFERENCES families (id) ON DELETE CASCADE, 
    FOREIGN KEY(sender_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_chat_messages_family_id_id ON chat_messages (family_id, id);

CREATE TABLE chat_read_states (
    id SERIAL NOT NULL, 
    family_id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    last_read_message_id INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(family_id) REFERENCES families (id) ON DELETE CASCADE, 
    FOREIGN KEY(last_read_message_id) REFERENCES chat_messages (id) ON DELETE SET NULL, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT uq_chat_read_states_family_user UNIQUE (family_id, user_id)
);

UPDATE alembic_version SET version_num='20260723_100000' WHERE alembic_version.version_num = '20260722_190000';

-- Running upgrade 20260723_100000 -> 20260723_140000

CREATE TABLE ai_chat_messages (
    id SERIAL NOT NULL, 
    family_id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    role VARCHAR(20) NOT NULL, 
    content TEXT NOT NULL, 
    message_kind VARCHAR(30) NOT NULL, 
    metadata_json JSON, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(family_id) REFERENCES families (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_ai_chat_messages_family_user_id ON ai_chat_messages (family_id, user_id, id);

CREATE TABLE fridge_image_analyses (
    id SERIAL NOT NULL, 
    family_id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    image_url VARCHAR(500) NOT NULL, 
    recognized_ingredients_json JSON NOT NULL, 
    raw_model_output TEXT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(family_id) REFERENCES families (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_fridge_image_analyses_family_user_id ON fridge_image_analyses (family_id, user_id, id);

UPDATE alembic_version SET version_num='20260723_140000' WHERE alembic_version.version_num = '20260723_100000';

-- Running upgrade 20260723_140000 -> 20260723_160000

CREATE TABLE ai_chat_conversations (
    id SERIAL NOT NULL, 
    family_id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    title VARCHAR(100) DEFAULT '新对话' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(family_id) REFERENCES families (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_ai_chat_conversations_family_user_updated_at ON ai_chat_conversations (family_id, user_id, updated_at);

ALTER TABLE ai_chat_messages ADD COLUMN conversation_id INTEGER;

ALTER TABLE ai_chat_messages ADD CONSTRAINT fk_ai_chat_messages_conversation_id FOREIGN KEY(conversation_id) REFERENCES ai_chat_conversations (id) ON DELETE CASCADE;

INSERT INTO ai_chat_conversations (family_id, user_id, title, created_at, updated_at)
            SELECT
                family_id,
                user_id,
                '历史对话',
                MIN(created_at),
                MAX(created_at)
            FROM ai_chat_messages
            GROUP BY family_id, user_id;

UPDATE ai_chat_messages AS message
            SET conversation_id = conversation.id
            FROM ai_chat_conversations AS conversation
            WHERE message.family_id = conversation.family_id
              AND message.user_id = conversation.user_id
              AND message.conversation_id IS NULL;

ALTER TABLE ai_chat_messages ALTER COLUMN conversation_id SET NOT NULL;

DROP INDEX ix_ai_chat_messages_family_user_id;

CREATE INDEX ix_ai_chat_messages_family_user_conversation_id ON ai_chat_messages (family_id, user_id, conversation_id, id);

UPDATE alembic_version SET version_num='20260723_160000' WHERE alembic_version.version_num = '20260723_140000';

-- Running upgrade 20260723_160000 -> 20260724_110000

ALTER TABLE dishes ADD COLUMN cooking_minutes INTEGER;

ALTER TABLE dishes ADD COLUMN difficulty INTEGER;

ALTER TABLE dishes ADD COLUMN spicy_level INTEGER;

ALTER TABLE dishes ADD COLUMN need_prepare_ahead BOOLEAN DEFAULT false NOT NULL;

ALTER TABLE dishes ADD COLUMN suitable_for_weekday BOOLEAN DEFAULT false NOT NULL;

CREATE TABLE ingredients (
    id SERIAL NOT NULL, 
    family_id INTEGER NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    category VARCHAR(50), 
    default_unit VARCHAR(20), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(family_id) REFERENCES families (id) ON DELETE CASCADE, 
    CONSTRAINT uq_ingredients_family_name UNIQUE (family_id, name)
);

CREATE TABLE dish_ingredients (
    id SERIAL NOT NULL, 
    dish_id INTEGER NOT NULL, 
    ingredient_id INTEGER NOT NULL, 
    quantity FLOAT, 
    unit VARCHAR(20), 
    is_optional BOOLEAN DEFAULT false NOT NULL, 
    note VARCHAR(255), 
    sort_order INTEGER DEFAULT '0' NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(dish_id) REFERENCES dishes (id) ON DELETE CASCADE, 
    FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT
);

CREATE TABLE dish_steps (
    id SERIAL NOT NULL, 
    dish_id INTEGER NOT NULL, 
    step_no INTEGER DEFAULT '1' NOT NULL, 
    content TEXT NOT NULL, 
    duration_minutes INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(dish_id) REFERENCES dishes (id) ON DELETE CASCADE
);

CREATE TABLE dish_preferences (
    id SERIAL NOT NULL, 
    dish_id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    preference_note TEXT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(dish_id) REFERENCES dishes (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE shopping_lists (
    id SERIAL NOT NULL, 
    family_id INTEGER NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    status VARCHAR(20) DEFAULT 'active' NOT NULL, 
    source_type VARCHAR(20) DEFAULT 'manual' NOT NULL, 
    source_reference VARCHAR(100), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(family_id) REFERENCES families (id) ON DELETE CASCADE
);

CREATE TABLE shopping_list_items (
    id SERIAL NOT NULL, 
    shopping_list_id INTEGER NOT NULL, 
    ingredient_id INTEGER, 
    name VARCHAR(100) NOT NULL, 
    quantity FLOAT, 
    unit VARCHAR(20), 
    note TEXT, 
    source_dish_name VARCHAR(100), 
    is_purchased BOOLEAN DEFAULT false NOT NULL, 
    sort_order INTEGER DEFAULT '0' NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE SET NULL, 
    FOREIGN KEY(shopping_list_id) REFERENCES shopping_lists (id) ON DELETE CASCADE
);

ALTER TABLE dishes ALTER COLUMN need_prepare_ahead DROP DEFAULT;

ALTER TABLE dishes ALTER COLUMN suitable_for_weekday DROP DEFAULT;

UPDATE alembic_version SET version_num='20260724_110000' WHERE alembic_version.version_num = '20260723_160000';



