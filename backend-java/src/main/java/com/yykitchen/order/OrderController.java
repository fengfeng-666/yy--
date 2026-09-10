package com.yykitchen.order;

import com.yykitchen.common.*;
import com.yykitchen.identity.*;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {
  private final OrderService service;
  private final IdentityService identity;

  public OrderController(OrderService service, IdentityService identity) {
    this.service = service;
    this.identity = identity;
  }

  private long family() {
    return identity.familyId(SecurityConfig.user());
  }

  public record Review(@Min(1) @Max(5) int rating, @Size(max = 500) String content) {}

  @GetMapping
  Api list(
      @RequestParam(required = false) String role, @RequestParam(required = false) String status) {
    return Api.ok(service.list(family(), SecurityConfig.user(), null, role, status, false));
  }

  @GetMapping("/history")
  Api history() {
    return Api.ok(service.list(family(), SecurityConfig.user(), null, null, "accepted", true));
  }

  @GetMapping("/{id}")
  Api detail(@PathVariable long id) {
    return Api.ok(service.detail(family(), id));
  }

  @PostMapping
  Api create(@Valid @RequestBody OrderRequest p) {
    return Api.ok(service.create(family(), SecurityConfig.user(), p), "点菜创建成功");
  }

  @PostMapping("/{id}/accept")
  Api accept(@PathVariable long id) {
    return Api.ok(service.accept(family(), id, SecurityConfig.user()), "点菜已接受");
  }

  @PostMapping("/{id}/review")
  Api review(@PathVariable long id, @Valid @RequestBody Review p) {
    return Api.ok(
        service.review(family(), id, SecurityConfig.user(), p.rating, p.content), "评价已提交");
  }
}
