package com.yykitchen.chat;

import com.yykitchen.common.Api;
import com.yykitchen.identity.*;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/chat")
public class ChatController {
  private final ChatService service;
  private final IdentityService identity;

  public ChatController(ChatService service, IdentityService identity) {
    this.service = service;
    this.identity = identity;
  }

  private long family() {
    return identity.familyId(SecurityConfig.user());
  }

  public record Message(@NotBlank @Size(max = 1000) String content) {}

  public record Read(@Positive long last_read_message_id) {}

  @GetMapping("/messages")
  Api list(
      @RequestParam(required = false) Long before_id,
      @RequestParam(required = false) Long after_id,
      @RequestParam(defaultValue = "30") int limit) {
    return Api.ok(service.list(family(), before_id, after_id, limit));
  }

  @PostMapping("/messages")
  Api send(@Valid @RequestBody Message p) {
    return Api.ok(service.send(family(), SecurityConfig.user(), p.content), "消息已发送");
  }

  @GetMapping("/unread-count")
  Api unread() {
    return Api.ok(service.unread(family(), SecurityConfig.user()));
  }

  @PostMapping("/read")
  Api read(@Valid @RequestBody Read p) {
    return Api.ok(service.read(family(), SecurityConfig.user(), p.last_read_message_id));
  }
}
