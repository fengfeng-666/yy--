-- 仅用于本地开发环境：清理 YY私厨 当前阶段的核心表和 Alembic 版本记录。
-- 执行后需要重新运行 Alembic 迁移。

BEGIN;

DROP TABLE IF EXISTS meal_reviews CASCADE;
DROP TABLE IF EXISTS order_status_logs CASCADE;
DROP TABLE IF EXISTS meal_order_items CASCADE;
DROP TABLE IF EXISTS meal_orders CASCADE;
DROP TABLE IF EXISTS dishes CASCADE;
DROP TABLE IF EXISTS family_members CASCADE;
DROP TABLE IF EXISTS families CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;

COMMIT;
