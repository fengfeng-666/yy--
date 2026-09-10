package com.yykitchen;

import static org.junit.jupiter.api.Assertions.*;

import com.yykitchen.ai.*;
import com.yykitchen.catalog.*;
import com.yykitchen.chat.ChatService;
import com.yykitchen.common.*;
import com.yykitchen.identity.*;
import com.yykitchen.order.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
@Import(KitchenIT.Counting.class)
class KitchenIT {
  @Container
  static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

  @Container
  static GenericContainer<?> redis =
      new GenericContainer<>("redis:7-alpine").withExposedPorts(6379);

  @DynamicPropertySource
  static void properties(DynamicPropertyRegistry r) {
    r.add("spring.datasource.url", postgres::getJdbcUrl);
    r.add("spring.datasource.username", postgres::getUsername);
    r.add("spring.datasource.password", postgres::getPassword);
    r.add("spring.data.redis.host", redis::getHost);
    r.add("spring.data.redis.port", () -> redis.getMappedPort(6379));
    r.add("yy.upload-dir", () -> "target/test-uploads");
    r.add("WECHAT_TEMPLATE_NEW_ORDER", () -> "test-template");
  }

  @TestConfiguration
  static class Counting {
    @Bean
    SqlCounter counter() {
      return new SqlCounter();
    }
  }

  @Autowired IdentityService identity;
  @Autowired IdentityMapper identities;
  @Autowired CatalogService catalog;
  @Autowired OrderService orders;
  @Autowired JdbcTemplate db;
  @Autowired SqlCounter counter;
  @Autowired ChatService chat;
  @Autowired StringRedisTemplate redisClient;
  @Autowired AiMapper ai;
  @Autowired AiService aiService;
  @Autowired OrderMapper orderMapper;
  @Autowired CatalogMapper catalogMapper;
  @Autowired org.springframework.transaction.support.TransactionTemplate transaction;
  @Autowired com.yykitchen.notification.NotificationService notifications;
  @org.springframework.test.context.bean.override.mockito.MockitoBean AiGateway gateway;
  @Autowired org.springframework.boot.test.web.client.TestRestTemplate http;
  long user, cook, family, dish;

  @Test void aiCacheReusesContentButCreatesSeparateMessages() throws Exception {
    org.mockito.Mockito.when(gateway.fingerprint()).thenReturn("test-model-config");
    org.mockito.Mockito.when(gateway.generate(org.mockito.ArgumentMatchers.anyMap(),org.mockito.ArgumentMatchers.any(),org.mockito.ArgumentMatchers.any()))
      .thenReturn(Json.map("summary","推荐番茄炒蛋","recommendations",List.of(Json.map("dish_name","番茄炒蛋","rating",5,"reason","符合偏好")),"recognized_ingredients",List.of()));
    var first=aiService.generate(aiService.begin(family,user,null,"推荐",null),s->{},new AiGateway.Running());
    var second=aiService.generate(aiService.begin(family,user,null,"推荐",null),s->{},new AiGateway.Running());
    assertNotEquals(Json.id((Map<String,Object>)first.get("assistant_message")),Json.id((Map<String,Object>)second.get("assistant_message")));
    org.mockito.Mockito.verify(gateway,org.mockito.Mockito.times(1)).generate(org.mockito.ArgumentMatchers.anyMap(),org.mockito.ArgumentMatchers.any(),org.mockito.ArgumentMatchers.any());
    catalog.update(family,dish,new CatalogController.DishRequest("新菜",null,12.0,null,true));
    aiService.generate(aiService.begin(family,user,null,"推荐",null),s->{},new AiGateway.Running());
    org.mockito.Mockito.verify(gateway,org.mockito.Mockito.times(2)).generate(org.mockito.ArgumentMatchers.anyMap(),org.mockito.ArgumentMatchers.any(),org.mockito.ArgumentMatchers.any());
  }

  @Test void uniqueIndexProtectsWithoutRedisLock() throws Exception {
    Cache unavailable=org.mockito.Mockito.mock(Cache.class);
    org.mockito.Mockito.when(unavailable.acquire(org.mockito.ArgumentMatchers.anyString())).thenReturn("database-fallback");
    var fallback=new OrderService(orderMapper,catalogMapper,identities,notifications,unavailable,transaction);
    var executor=Executors.newFixedThreadPool(8);
    try {
      var tasks=new ArrayList<Future<Long>>();
      for(int i=0;i<12;i++)tasks.add(executor.submit(()->Json.id(fallback.create(family,user,request("no-redis")))));
      var ids=new HashSet<Long>();for(var task:tasks)ids.add(task.get(30,TimeUnit.SECONDS));assertEquals(1,ids.size());
    } finally {executor.shutdownNow();}
    assertEquals(1,db.queryForObject("SELECT count(*) FROM meal_orders WHERE family_id=?",Integer.class,family));
  }

  @Test void httpContractRequiresAuthAndPreservesResponseShape() {
    assertEquals(401,http.getForEntity("/api/v1/auth/me",Map.class).getStatusCode().value());
    var headers=new org.springframework.http.HttpHeaders();headers.setBearerAuth(((Map<String,Object>)identity.auth(user).get("tokens")).get("access_token").toString());
    var response=http.exchange("/api/v1/families/current",org.springframework.http.HttpMethod.GET,new org.springframework.http.HttpEntity<>(headers),Map.class);
    assertEquals(200,response.getStatusCode().value());assertEquals(0,response.getBody().get("code"));var data=(Map<String,Object>)response.getBody().get("data");assertEquals(family,Json.id(data));
    var members=(List<Map<String,Object>>)data.get("members");assertFalse(((Map<?,?>)members.get(0).get("user")).containsKey("password_hash"));
  }

  @BeforeEach
  void fixture() {
    String suffix = UUID.randomUUID().toString().substring(0, 8);
    user =
        Json.id(
            (Map<String, Object>) identity.register("u" + suffix, null, "password").get("user"));
    cook =
        Json.id(
            (Map<String, Object>) identity.register("c" + suffix, null, "password").get("user"));
    var f = (Map<String, Object>) identity.createFamily(user, "测试家庭", null).get("family");
    family = Json.id(f);
    identity.join(cook, f.get("invite_code").toString());
    dish =
        Json.id(
            catalog.create(
                family, new CatalogController.DishRequest("番茄炒蛋", null, 12.0, null, true)));
  }

  OrderRequest request(String key) {
    return new OrderRequest(
        cook,
        LocalDate.now(ZoneId.of("Asia/Shanghai")),
        LocalTime.NOON,
        null,
        List.of(new OrderRequest.Item(dish, 1, null, 0)),
        key);
  }

  @Test
  void concurrentRequestsProduceOneOrderAndNotification() throws Exception {
    db.update("UPDATE users SET wechat_openid=? WHERE id=?", "openid-" + cook, cook);
    db.update(
        "INSERT INTO wechat_subscriptions(user_id,event_type,available_count) VALUES(?,'new_order',5)",
        cook);
    var pool = Executors.newFixedThreadPool(8);
    try {
      var futures = new ArrayList<Future<?>>();
      for (int i = 0; i < 16; i++)
        futures.add(
            pool.submit(
                () -> {
                  try {
                    orders.create(family, user, request("same"));
                  } catch (Problem p) {
                    assertEquals(409, p.status);
                  }
                }));
      for (var future : futures) future.get(30, TimeUnit.SECONDS);
    } finally {
      pool.shutdownNow();
    }
    var order = orders.create(family, user, request("same"));
    assertNotNull(order.get("id"));
    assertEquals(
        1,
        db.queryForObject(
            "SELECT count(*) FROM meal_orders WHERE family_id=?", Integer.class, family));
    assertEquals(
        1,
        db.queryForObject(
            "SELECT count(*) FROM wechat_notifications WHERE meal_order_id=?",
            Integer.class,
            Json.id(order)));
    assertEquals(
        4,
        db.queryForObject(
            "SELECT available_count FROM wechat_subscriptions WHERE user_id=?",
            Integer.class,
            cook));
  }

  @Test
  void queriesStayAtTwoAndAccessIsIsolated() {
    long second =
        Json.id(
            catalog.create(family, new CatalogController.DishRequest("青菜", null, 5.0, null, true)));
    var p =
        new OrderRequest(
            cook,
            LocalDate.now(),
            null,
            null,
            List.of(
                new OrderRequest.Item(dish, 1, null, 0), new OrderRequest.Item(second, 2, null, 1)),
            "two");
    long order = Json.id(orders.create(family, user, p));
    counter.queries.set(0);
    assertEquals(2, ((List<?>) orders.detail(family, order).get("items")).size());
    assertEquals(2, counter.queries.get());
    assertThrows(Problem.class, () -> orders.detail(family + 10000, order));
    assertThrows(Problem.class, () -> orders.accept(family, order, user));
    orders.accept(family, order, cook);
    assertThrows(Problem.class, () -> orders.accept(family, order, cook));
    orders.review(family, order, user, 5, "好吃");
    assertThrows(Problem.class, () -> orders.review(family, order, user, 5, "重复"));
  }

  @Test
  void cacheInvalidatesOnCommittedChanges() {
    assertEquals("番茄炒蛋", catalog.detail(family, dish).get("name"));
    String version = catalog.version(family);
    catalog.update(family, dish, new CatalogController.DishRequest("新菜名", null, 13.0, null, true));
    assertNotEquals(version, catalog.version(family));
    assertEquals("新菜名", catalog.detail(family, dish).get("name"));
    catalog.preferences(family);
    db.update(
        "INSERT INTO dish_preferences(dish_id,user_id,preference_note) VALUES(?,?,?)",
        dish,
        user,
        "不吃辣");
    assertEquals(1, catalog.preferences(family).size());
  }

  @Test
  void chatReadStateNeverMovesBackwards() {
    var first = chat.send(family, user, "one");
    var second = chat.send(family, user, "two");
    assertEquals(2, chat.unread(family, cook).get("unread_count"));
    chat.read(family, cook, Json.id(second));
    assertEquals(0, chat.read(family, cook, Json.id(first)).get("unread_count"));
  }

  @Test
  void conversationDeletionCascadesAndIsScoped() {
    long id = ai.createConversation(family, user, "test");
    ai.createMessage(family, user, id, "user", "hello", "text", null);
    assertNull(ai.conversation(family, cook, id));
    assertEquals(0, ai.delete(family, cook, id));
    assertEquals(1, ai.delete(family, user, id));
    assertEquals(
        0,
        db.queryForObject(
            "SELECT count(*) FROM ai_chat_messages WHERE conversation_id=?", Integer.class, id));
  }
}
