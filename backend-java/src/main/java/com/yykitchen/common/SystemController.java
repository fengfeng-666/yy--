package com.yykitchen.common;

import com.yykitchen.identity.*;
import com.yykitchen.order.HomeService;
import java.util.Map;
import org.springframework.core.env.Environment;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1")
public class SystemController {
  private final JdbcTemplate db;
  private final Environment env;
  private final HomeService home;
  private final IdentityService identity;

  public SystemController(
      JdbcTemplate db, Environment env, HomeService home, IdentityService identity) {
    this.db = db;
    this.env = env;
    this.home = home;
    this.identity = identity;
  }

  @GetMapping("/health")
  Api health() {
    db.queryForObject("SELECT 1", Integer.class);
    return Api.ok(
        Map.of(
            "app_name",
            env.getProperty("APP_NAME", "YY私厨"),
            "environment",
            env.getProperty("APP_ENV", "development"),
            "status",
            "ok",
            "database",
            Map.of(
                "status",
                "ok",
                "host",
                env.getProperty("DB_HOST", "localhost"),
                "name",
                env.getProperty("DB_NAME", "yy_kitchen"))));
  }

  @GetMapping("/home/summary")
  Api home() {
    long user = SecurityConfig.user();
    return Api.ok(home.summary(identity.familyId(user), user));
  }
}
