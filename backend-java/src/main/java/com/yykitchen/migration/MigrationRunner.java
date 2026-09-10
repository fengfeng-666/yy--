package com.yykitchen.migration;

import javax.sql.DataSource;
import org.flywaydb.core.Flyway;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(name = "yy.migration-action", havingValue = "adopt")
public class MigrationRunner implements ApplicationRunner {
  private final DataSource source;
  private final ConfigurableApplicationContext context;

  public MigrationRunner(DataSource source, ConfigurableApplicationContext context) {
    this.source = source;
    this.context = context;
  }

  @Override
  public void run(ApplicationArguments args) throws Exception {
    LegacyBaseline.adopt(source);
    Flyway.configure().dataSource(source).load().migrate();
    context.close();
  }
}
