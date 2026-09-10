package com.yykitchen.order;

import com.yykitchen.catalog.CatalogMapper;
import com.yykitchen.common.*;
import com.yykitchen.identity.IdentityMapper;
import com.yykitchen.notification.NotificationService;
import java.time.*;
import java.util.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

@Service
public class OrderService {
  private final OrderMapper mapper;
  private final CatalogMapper dishes;
  private final IdentityMapper identity;
  private final NotificationService notifications;
  private final Cache cache;
  private final TransactionTemplate tx;

  public OrderService(
      OrderMapper mapper,
      CatalogMapper dishes,
      IdentityMapper identity,
      NotificationService notifications,
      Cache cache,
      TransactionTemplate tx) {
    this.mapper = mapper;
    this.dishes = dishes;
    this.identity = identity;
    this.notifications = notifications;
    this.cache = cache;
    this.tx = tx;
  }

  public List<Map<String, Object>> list(
      long family, long user, Long id, String role, String status, boolean history) {
    if (role != null && !List.of("my_requested", "to_me").contains(role))
      throw Problem.bad("无效的订单筛选条件");
    if (status != null && !List.of("pending", "accepted").contains(status))
      throw new Problem(400, 40002, "无效的点菜状态");
    List<Map<String, Object>> orders =
        mapper.headers(family, user, id, role, status, history).stream().map(Json::object).toList();
    if (orders.isEmpty()) return orders;
    Map<Long, List<Map<String, Object>>> byOrder = new HashMap<>();
    for (String raw : mapper.items(family, orders.stream().map(Json::id).toList())) {
      var item = Json.object(raw);
      byOrder
          .computeIfAbsent(Json.number(item, "meal_order_id"), key -> new ArrayList<>())
          .add(item);
    }
    orders.forEach(o -> o.put("items", byOrder.getOrDefault(Json.id(o), List.of())));
    return orders;
  }

  public Map<String, Object> detail(long family, long id) {
    var rows = list(family, 0, id, null, null, false);
    if (rows.isEmpty()) throw Problem.missing("点菜订单不存在");
    return rows.get(0);
  }

  private Long existing(long family, long user, OrderRequest p, String hash) {
    if (p.requestId() == null) return null;
    String raw = mapper.existing(family, user, p.requestId());
    if (raw == null) return null;
    var previous = Json.object(raw);
    if (!hash.equals(previous.get("request_hash"))) throw Problem.conflict("requestId 已用于不同的点菜内容");
    return Json.id(previous);
  }

  public Map<String, Object> create(long family, long user, OrderRequest p) {
    String hash =
        Json.hash(
            Json.map(
                "cook",
                p.cook_id(),
                "date",
                p.planned_date(),
                "time",
                p.planned_time(),
                "note",
                p.note(),
                "items",
                p.items()));
    Long previous = existing(family, user, p, hash);
    if (previous != null) return detail(family, previous);
    String key = "order-lock:" + family + ":" + user + ":" + p.requestId();
    String token = p.requestId() == null ? "database-fallback" : cache.acquire(key);
    if (token == null) {
      previous = existing(family, user, p, hash);
      if (previous != null) return detail(family, previous);
      throw Problem.conflict("点菜正在处理中，请使用相同 requestId 重试");
    }
    try {
      long id =
          Objects.requireNonNull(
              tx.execute(
                  transaction -> {
                    Long duplicate = existing(family, user, p, hash);
                    if (duplicate != null) return duplicate;
                    if (p.cook_id() == user) throw Problem.bad("不能给自己发起点菜");
                    if (!Objects.equals(identity.familyId(p.cook_id()), family))
                      throw Problem.forbidden("指定厨师不属于当前家庭");
                    var ids = p.items().stream().map(OrderRequest.Item::dish_id).toList();
                    if (new HashSet<>(ids).size() != ids.size()) throw Problem.bad("同一个菜品不能重复添加");
                    var selected = dishes.batch(family, ids).stream().map(Json::object).toList();
                    if (selected.size() != ids.size()) throw Problem.missing("菜品不存在或不属于当前家庭");
                    if (selected.stream()
                        .anyMatch(d -> !Boolean.TRUE.equals(d.get("is_available"))))
                      throw Problem.bad("所选菜品已下架");
                    Long created = mapper.create(family, user, p, hash);
                    if (created == null) {
                      Long found = existing(family, user, p, hash);
                      if (found == null) throw Problem.conflict("点菜处理中，请重试");
                      return found;
                    }
                    mapper.addItems(created, p.items());
                    mapper.log(created, null, "pending", user, "发起点菜");
                    notifications.enqueue(
                        family,
                        created,
                        user,
                        p.cook_id(),
                        "new_order",
                        p.planned_date(),
                        p.planned_time(),
                        selected);
                    return created;
                  }));
      return detail(family, id);
    } finally {
      cache.release(key, token);
    }
  }

  public Map<String, Object> accept(long family, long id, long user) {
    tx.executeWithoutResult(
        t -> {
          var order = detail(family, id);
          if (Json.number(order, "cook_id") != user) throw Problem.forbidden("只有被指定的厨师可以接受点菜");
          if (mapper.accept(family, id, user) == 0) throw new Problem(400, 40002, "当前点菜状态不允许接受");
          mapper.log(id, "pending", "accepted", user, "接受点菜");
          var rows = (List<Map<String, Object>>) order.get("items");
          var selected = rows.stream().map(i -> (Map<String, Object>) i.get("dish")).toList();
          notifications.enqueue(
              family,
              id,
              user,
              Json.number(order, "requester_id"),
              "order_accepted",
              LocalDate.parse((String) order.get("planned_date")),
              order.get("planned_time") == null
                  ? null
                  : LocalTime.parse((String) order.get("planned_time")),
              selected);
        });
    return detail(family, id);
  }

  public Map<String, Object> review(long family, long id, long user, int rating, String content) {
    tx.executeWithoutResult(
        t -> {
          var order = detail(family, id);
          if (Json.number(order, "requester_id") != user) throw Problem.forbidden("只有发起点菜的人可以评价");
          if (!"accepted".equals(order.get("status")))
            throw new Problem(400, 40002, "只有已接受的点菜可以评价");
          if (LocalDate.parse((String) order.get("planned_date"))
              .isAfter(LocalDate.now(ZoneId.of("Asia/Shanghai"))))
            throw Problem.bad("用餐日期未到，暂时不能评价");
          if (mapper.review(id, user, rating, content) == 0)
            throw new Problem(409, 40903, "这次用餐已经评价过了");
        });
    return detail(family, id);
  }
}
