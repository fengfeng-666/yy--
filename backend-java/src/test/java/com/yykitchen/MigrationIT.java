package com.yykitchen;

import static org.junit.jupiter.api.Assertions.*;

import com.yykitchen.migration.LegacyBaseline;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers
class MigrationIT {
  @Container
  static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

  @Test
  void verifiedLegacyDatabaseKeepsDataAndSupportsOldWrites() throws Exception {
    var source =
        new DriverManagerDataSource(
            postgres.getJdbcUrl(), postgres.getUsername(), postgres.getPassword());
    var db = new JdbcTemplate(source);
    Flyway.configure().dataSource(source).target("1").load().migrate();
    db.execute("DROP TABLE flyway_schema_history");
    db.update(
        "INSERT INTO users(username,nickname,password_hash) VALUES('legacy','旧用户','old-hash')");
    db.execute("ALTER TABLE users ADD COLUMN unexpected_column text");
    assertThrows(IllegalStateException.class,()->LegacyBaseline.adopt(source));
    assertFalse(db.queryForObject("SELECT to_regclass('public.flyway_schema_history') IS NOT NULL",Boolean.class));
    db.execute("ALTER TABLE users DROP COLUMN unexpected_column");
    LegacyBaseline.adopt(source);
    Flyway.configure().dataSource(source).load().migrate();
    assertEquals(
        "old-hash",
        db.queryForObject("SELECT password_hash FROM users WHERE username='legacy'", String.class));
    db.update(
        "INSERT INTO families(name,invite_code,owner_id) SELECT '旧客户端家庭','LEGACY',id FROM users WHERE username='legacy'");
    db.update(
        "INSERT INTO dishes(family_id,name,price,need_prepare_ahead,suitable_for_weekday) SELECT id,'旧写入',0,false,false FROM families WHERE invite_code='LEGACY'");
    assertEquals(1, db.queryForObject("SELECT count(*) FROM dishes", Integer.class));
    assertEquals(3, Flyway.configure().dataSource(source).load().info().applied().length);
  }
}
