package com.yykitchen.notification;

import com.yykitchen.common.*;
import com.yykitchen.identity.IdentityMapper;
import java.time.*;
import java.util.*;
import java.util.stream.Collectors;
import org.springframework.core.env.Environment;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class NotificationService {
  private final NotificationMapper mapper;
  private final IdentityMapper users;
  private final Environment env;
  private final WechatService wechat;

  public NotificationService(
      NotificationMapper mapper, IdentityMapper users, Environment env, WechatService wechat) {
    this.mapper = mapper;
    this.users = users;
    this.env = env;
    this.wechat = wechat;
  }

  @Transactional
  public List<Map<String, Object>> grant(long user, List<String> events) {
    if (events == null
        || events.isEmpty()
        || events.size() > 2
        || !events.stream().allMatch(e -> List.of("new_order", "order_accepted").contains(e)))
      throw Problem.bad("无效的消息订阅类型");
    return events.stream()
        .distinct()
        .map(e -> Json.map("event_type", e, "available_count", mapper.grant(user, e)))
        .toList();
  }

  // Called within the order transaction; dispatch happens only after rows become visible.
  public void enqueue(
      long family,
      long order,
      long actor,
      long recipient,
      String event,
      LocalDate date,
      LocalTime time,
      List<Map<String, Object>> dishes) {
    String template =
        env.getProperty(
            event.equals("new_order")
                ? "WECHAT_TEMPLATE_NEW_ORDER"
                : "WECHAT_TEMPLATE_ORDER_ACCEPTED",
            "");
    if (template.isBlank()) return;
    var user = Json.object(users.user(recipient));
    if (user.get("wechat_openid") == null || mapper.consume(recipient, event) == 0) return;
    String names =
        dishes.stream().map(d -> d.get("name").toString()).collect(Collectors.joining("、"));
    String nickname = Json.object(users.profile(actor)).get("nickname").toString();
    String planned = date.toString() + (time == null ? "" : " " + time.toString());
    mapper.enqueue(
        recipient,
        order,
        event,
        template,
        Json.write(
            Map.of(
                "thing1",
                Map.of("value", names.substring(0, Math.min(20, names.length()))),
                "thing2",
                Map.of("value", nickname.substring(0, Math.min(20, nickname.length()))),
                "time3",
                Map.of("value", planned))));
  }

  @Scheduled(fixedDelayString = "${yy.notification-poll-ms:3000}")
  public void dispatch() {
    if (!env.getProperty("WECHAT_ENABLED", Boolean.class, false)) return;
    mapper.interrupted();
    for (int i = 0; i < 10; i++) {
      String raw = mapper.claim();
      if (raw == null) return;
      var notification = Json.object(raw);
      long id = Json.id(notification);
      try {
        wechat.send(notification);
        mapper.finish(id, "sent", null);
      } catch (Exception e) {
        mapper.finish(id, "failed", "发送失败或结果不确定，请核对后重试");
      }
    }
  }
}
