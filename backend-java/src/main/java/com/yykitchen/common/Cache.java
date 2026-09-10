package com.yykitchen.common;

import java.time.Duration;
import java.util.List;
import java.util.UUID;
import java.util.function.Supplier;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.*;

@Component
public class Cache {
  private final StringRedisTemplate redis;

  public Cache(StringRedisTemplate redis) {
    this.redis = redis;
  }

  public String get(String key) {
    try {
      return redis.opsForValue().get(key);
    } catch (org.springframework.dao.DataAccessException e) {
      return null;
    }
  }

  public void put(String key, String value, Duration ttl) {
    try {
      redis.opsForValue().set(key, value, ttl);
    } catch (org.springframework.dao.DataAccessException ignored) {
    }
  }

  public String remember(String key, Duration ttl, Supplier<String> loader) {
    String value = get(key);
    if (value != null) return value;
    value = loader.get();
    if (value != null) put(key, value, ttl);
    return value;
  }

  public void afterCommit(Runnable action) {
    if (TransactionSynchronizationManager.isActualTransactionActive())
      TransactionSynchronizationManager.registerSynchronization(
          new TransactionSynchronization() {
            @Override
            public void afterCommit() {
              action.run();
            }
          });
    else action.run();
  }

  public void invalidate(String key) {
    afterCommit(
        () -> {
          try {
            redis.delete(key);
          } catch (org.springframework.dao.DataAccessException ignored) {
          }
        });
  }

  public String acquire(String key) {
    String token = UUID.randomUUID().toString();
    try {
      return Boolean.TRUE.equals(
              redis.opsForValue().setIfAbsent(key, token, Duration.ofSeconds(30)))
          ? token
          : null;
    } catch (org.springframework.dao.DataAccessException e) {
      return "database-fallback";
    }
  }

  public void release(String key, String token) {
    if (token == null || token.equals("database-fallback")) return;
    try {
      redis.execute(
          new DefaultRedisScript<Long>(
              "if redis.call('get',KEYS[1]) == ARGV[1] then return redis.call('del',KEYS[1]) else return 0 end",
              Long.class),
          List.of(key),
          token);
    } catch (org.springframework.dao.DataAccessException ignored) {
    }
  }
}
