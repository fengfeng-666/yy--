package com.yykitchen.migration;

import java.sql.Connection;
import java.util.*;
import javax.sql.DataSource;
import org.flywaydb.core.Flyway;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.SingleConnectionDataSource;

/** Explicit, fail-closed adoption of the exact Alembic head; never invoked on normal startup. */
public final class LegacyBaseline {
  private LegacyBaseline() {}

  public static void adopt(DataSource source) throws Exception {
    var db = new JdbcTemplate(source);
    Boolean adopted =
        db.queryForObject(
            "SELECT to_regclass('public.flyway_schema_history') IS NOT NULL", Boolean.class);
    if (Boolean.TRUE.equals(adopted)) {
      Flyway.configure().dataSource(source).load().validate();
      return;
    }
    String head = db.queryForObject("SELECT version_num FROM public.alembic_version", String.class);
    if (!"20260724_110000".equals(head))
      throw new IllegalStateException(
          "Expected Alembic head 20260724_110000; upgrade the legacy service first");
    String scratch = "yy_verify_" + UUID.randomUUID().toString().replace("-", "");
    // Isolated schema contains no user data. Its exact generated name is never supplied by a
    // caller.
    try (Connection connection = source.getConnection()) {
      var isolated = new SingleConnectionDataSource(connection, true);
      var scratchDb = new JdbcTemplate(isolated);
      scratchDb.execute("CREATE SCHEMA " + scratch);
      try {
        Flyway.configure()
            .dataSource(isolated)
            .schemas(scratch)
            .defaultSchema(scratch)
            .target("1")
            .load()
            .migrate();
        if (!columns(db, "public").equals(columns(db, scratch)))
          throw new IllegalStateException(
              "Legacy columns differ from the Alembic head; baseline refused");
        if (!constraints(db, "public").equals(constraints(db, scratch)))
          throw new IllegalStateException(
              "Legacy constraints differ from the Alembic head; baseline refused");
        if (!indexes(db, "public").equals(indexes(db, scratch)))
          throw new IllegalStateException(
              "Legacy indexes differ from the Alembic head; baseline refused");
      } finally {
        scratchDb.execute("SET search_path TO public");
        scratchDb.execute("DROP SCHEMA " + scratch + " CASCADE");
      }
    }
    Flyway.configure()
        .dataSource(source)
        .defaultSchema("public")
        .baselineVersion("1")
        .baselineDescription("Verified Alembic 20260724_110000")
        .load()
        .baseline();
  }

  private static List<Map<String, Object>> columns(JdbcTemplate db, String schema) {
    return db.queryForList(
        "SELECT table_name,column_name,udt_name,is_nullable,character_maximum_length,numeric_precision,numeric_scale,regexp_replace(COALESCE(column_default,''),'[a-zA-Z0-9_]+\\.','', 'g') AS default_value FROM information_schema.columns WHERE table_schema=? AND table_name!='flyway_schema_history' ORDER BY table_name,ordinal_position",
        schema);
  }

  private static List<String> constraints(JdbcTemplate db, String schema) {
    return db.query(
        "SELECT c.relname,con.contype,pg_get_constraintdef(con.oid) AS definition FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=? AND c.relname!='flyway_schema_history' ORDER BY c.relname,con.contype,definition",
        (rs, n) ->
            rs.getString(1)
                + ":"
                + rs.getString(2)
                + ":"
                + rs.getString(3).replace(schema + ".", "").replace("public.", ""),
        schema);
  }

  private static List<String> indexes(JdbcTemplate db, String schema) {
    return db.query(
        "SELECT tablename,indexdef FROM pg_indexes WHERE schemaname=? AND tablename!='flyway_schema_history' ORDER BY tablename,indexname",
        (rs, n) -> rs.getString(2).replace(schema + ".", "").replace("public.", ""),
        schema);
  }
}
