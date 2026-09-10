package com.yykitchen.notification;

import com.yykitchen.common.Api;
import com.yykitchen.identity.SecurityConfig;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/notifications")
public class NotificationController {
  private final NotificationService service;

  public NotificationController(NotificationService service) {
    this.service = service;
  }

  public record Grant(List<String> event_types) {}

  @PostMapping("/subscriptions/grant")
  Api grant(@RequestBody Grant p) {
    return Api.ok(service.grant(SecurityConfig.user(), p.event_types()), "消息提醒已开启");
  }
}
