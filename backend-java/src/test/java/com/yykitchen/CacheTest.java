package com.yykitchen;

import com.yykitchen.common.Cache;
import org.junit.jupiter.api.Test;
import org.springframework.data.redis.RedisConnectionFailureException;
import org.springframework.data.redis.core.*;
import java.time.Duration;
import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

class CacheTest {
  @Test void redisFailureFallsBackToDatabaseAndUncachedLoader() {
    var redis=mock(StringRedisTemplate.class);
    when(redis.opsForValue()).thenThrow(new RedisConnectionFailureException("offline"));
    var cache=new Cache(redis);
    assertEquals("database-fallback",cache.acquire("order-lock"));
    assertEquals("loaded",cache.remember("dish",Duration.ofMinutes(1),()->"loaded"));
  }
}
