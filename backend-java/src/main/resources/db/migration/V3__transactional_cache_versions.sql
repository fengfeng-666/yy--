CREATE TABLE yy_family_data_versions (
    family_id integer PRIMARY KEY REFERENCES families(id) ON DELETE CASCADE,
    version bigint NOT NULL DEFAULT 0
);
INSERT INTO yy_family_data_versions(family_id) SELECT id FROM families;
CREATE FUNCTION yy_bump_family_version() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE data jsonb; family integer;
BEGIN
    data := CASE WHEN TG_OP='DELETE' THEN to_jsonb(OLD) ELSE to_jsonb(NEW) END;
    IF TG_TABLE_NAME IN ('dish_preferences','dish_ingredients','dish_steps') THEN
        SELECT family_id INTO family FROM dishes WHERE id=(data->>'dish_id')::integer;
    ELSIF TG_TABLE_NAME='meal_reviews' THEN
        SELECT family_id INTO family FROM meal_orders WHERE id=(data->>'meal_order_id')::integer;
    ELSIF TG_TABLE_NAME='families' THEN
        family := (data->>'id')::integer;
    ELSE
        family := (data->>'family_id')::integer;
    END IF;
    IF family IS NOT NULL AND EXISTS(SELECT 1 FROM families WHERE id=family) THEN
        INSERT INTO yy_family_data_versions(family_id,version) VALUES(family,1)
        ON CONFLICT(family_id) DO UPDATE SET version=yy_family_data_versions.version+1;
    END IF;
    RETURN NULL;
END $$;
CREATE TRIGGER yy_cache_families AFTER INSERT OR UPDATE ON families FOR EACH ROW EXECUTE FUNCTION yy_bump_family_version();
CREATE TRIGGER yy_cache_dishes AFTER INSERT OR UPDATE OR DELETE ON dishes FOR EACH ROW EXECUTE FUNCTION yy_bump_family_version();
CREATE TRIGGER yy_cache_preferences AFTER INSERT OR UPDATE OR DELETE ON dish_preferences FOR EACH ROW EXECUTE FUNCTION yy_bump_family_version();
CREATE TRIGGER yy_cache_ingredients AFTER INSERT OR UPDATE OR DELETE ON dish_ingredients FOR EACH ROW EXECUTE FUNCTION yy_bump_family_version();
CREATE TRIGGER yy_cache_steps AFTER INSERT OR UPDATE OR DELETE ON dish_steps FOR EACH ROW EXECUTE FUNCTION yy_bump_family_version();
CREATE TRIGGER yy_cache_orders AFTER INSERT OR UPDATE OR DELETE ON meal_orders FOR EACH ROW EXECUTE FUNCTION yy_bump_family_version();
CREATE TRIGGER yy_cache_reviews AFTER INSERT OR UPDATE OR DELETE ON meal_reviews FOR EACH ROW EXECUTE FUNCTION yy_bump_family_version();
