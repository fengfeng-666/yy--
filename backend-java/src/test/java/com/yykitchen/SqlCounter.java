package com.yykitchen;

import java.sql.Statement;
import java.util.concurrent.atomic.AtomicInteger;
import org.apache.ibatis.executor.statement.StatementHandler;
import org.apache.ibatis.plugin.*;

@Intercepts(
    @Signature(
        type = StatementHandler.class,
        method = "query",
        args = {Statement.class, org.apache.ibatis.session.ResultHandler.class}))
public class SqlCounter implements Interceptor {
  public final AtomicInteger queries = new AtomicInteger();

  @Override
  public Object intercept(Invocation invocation) throws Throwable {
    queries.incrementAndGet();
    return invocation.proceed();
  }
}
