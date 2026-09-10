ALTER TABLE meal_orders ADD COLUMN request_id varchar(128);
ALTER TABLE meal_orders ADD COLUMN request_hash varchar(64);
CREATE UNIQUE INDEX uq_meal_orders_request ON meal_orders(family_id, requester_id, request_id);
CREATE INDEX ix_meal_orders_family_created ON meal_orders(family_id, created_at DESC, id DESC);
CREATE INDEX ix_order_items_order ON meal_order_items(meal_order_id);
CREATE INDEX ix_order_logs_order ON order_status_logs(meal_order_id);
CREATE INDEX ix_dishes_family ON dishes(family_id);
CREATE VIEW yy_user_profiles AS SELECT id, username, nickname, is_active, created_at FROM users;
-- JSON projections preserve the existing nested wire representation without ORM lazy queries.
CREATE VIEW yy_dish_profiles AS
SELECT d.*,
  COALESCE((SELECT jsonb_agg(to_jsonb(di) || jsonb_build_object('ingredient',to_jsonb(i) - 'created_at' - 'updated_at') ORDER BY di.sort_order,di.id)
    FROM dish_ingredients di JOIN ingredients i ON i.id=di.ingredient_id WHERE di.dish_id=d.id),'[]'::jsonb) AS ingredients,
  COALESCE((SELECT jsonb_agg(to_jsonb(s) ORDER BY s.step_no,s.id) FROM dish_steps s WHERE s.dish_id=d.id),'[]'::jsonb) AS steps,
  COALESCE((SELECT jsonb_agg(to_jsonb(p) ORDER BY p.id) FROM dish_preferences p WHERE p.dish_id=d.id),'[]'::jsonb) AS preferences
FROM dishes d;
CREATE VIEW yy_order_profiles AS
SELECT o.id,o.family_id,o.requester_id,o.cook_id,o.status,o.planned_date,o.planned_time,o.note,o.accepted_at,o.created_at,o.updated_at,
  to_jsonb(requester) AS requester, to_jsonb(cook) AS cook,
  (SELECT to_jsonb(r) || jsonb_build_object('reviewer',to_jsonb(u)) FROM meal_reviews r JOIN yy_user_profiles u ON u.id=r.reviewer_id WHERE r.meal_order_id=o.id) AS review,
  COALESCE((SELECT jsonb_agg(to_jsonb(l) || jsonb_build_object('operator',to_jsonb(u)) ORDER BY l.id)
    FROM order_status_logs l JOIN yy_user_profiles u ON u.id=l.operator_id WHERE l.meal_order_id=o.id),'[]'::jsonb) AS status_logs
FROM meal_orders o JOIN yy_user_profiles requester ON requester.id=o.requester_id JOIN yy_user_profiles cook ON cook.id=o.cook_id;
