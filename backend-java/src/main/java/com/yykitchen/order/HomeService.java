package com.yykitchen.order;

import com.yykitchen.common.Json;
import java.time.*;
import java.util.*;
import org.springframework.stereotype.Service;

@Service
public class HomeService {
  private final OrderService orders;

  public HomeService(OrderService orders) {
    this.orders = orders;
  }

  public Map<String, Object> summary(long family, long user) {
    var all = orders.list(family, user, null, null, null, false);
    var history = orders.list(family, user, null, null, "accepted", true);
    LocalDate today = LocalDate.now(ZoneId.of("Asia/Shanghai"));
    var pending = all.stream().filter(o -> "pending".equals(o.get("status"))).toList();
    var monthly =
        history.stream()
            .filter(
                o -> ((String) o.get("planned_date")).startsWith(today.toString().substring(0, 7)))
            .toList();
    Map<String, Long> counts = new LinkedHashMap<>();
    for (var o : monthly)
      for (var item : (List<Map<String, Object>>) o.get("items")) {
        String name = ((Map<String, Object>) item.get("dish")).get("name").toString();
        counts.merge(name, Json.number(item, "quantity"), Long::sum);
      }
    var top = counts.entrySet().stream().max(Map.Entry.comparingByValue()).orElse(null);
    var todayOrder =
        all.stream()
            .filter(o -> today.toString().equals(o.get("planned_date")))
            .min(
                Comparator.<Map<String, Object>, Integer>comparing(
                        o -> "pending".equals(o.get("status")) ? 0 : 1)
                    .thenComparing(
                        o ->
                            o.get("planned_time") == null ? "99" : o.get("planned_time").toString())
                    .thenComparing(o -> o.get("created_at").toString()))
            .orElse(null);
    return Json.map(
        "pending_orders_count",
        pending.size(),
        "pending_to_me_count",
        pending.stream().filter(o -> Json.number(o, "cook_id") == user).count(),
        "review_pending_count",
        history.stream()
            .filter(
                o ->
                    Json.number(o, "requester_id") == user
                        && o.get("review") == null
                        && !LocalDate.parse(o.get("planned_date").toString()).isAfter(today))
            .count(),
        "monthly_accepted_orders_count",
        monthly.size(),
        "monthly_top_dish_name",
        top == null ? null : top.getKey(),
        "monthly_top_dish_count",
        top == null ? 0 : top.getValue(),
        "today_order",
        todayOrder,
        "recent_history",
        history.stream().limit(3).toList());
  }
}
