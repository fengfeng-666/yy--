package com.yykitchen.identity;

import com.yykitchen.common.*;
import com.yykitchen.notification.WechatService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1")
public class IdentityController {
  private final IdentityService service;
  private final WechatService wechat;

  public IdentityController(IdentityService service, WechatService wechat) {
    this.service = service;
    this.wechat = wechat;
  }

  public record Register(
      @NotBlank @Size(min = 3, max = 32) String username,
      @Size(max = 32) String nickname,
      @NotNull @Size(min = 6, max = 128) String password) {}

  public record Login(
      @NotBlank @Size(min = 3, max = 32) String username,
      @NotNull @Size(min = 6, max = 128) String password) {}

  public record Nickname(@NotBlank @Size(max = 32) String nickname) {}

  public record Family(
      @NotBlank @Size(max = 100) String name, @Size(max = 255) String description) {}

  public record Join(@NotBlank @Size(min = 4, max = 20) String invite_code) {}

  public record Wechat(@NotBlank @Size(max = 256) String code, @Size(max = 32) String nickname) {}

  @PostMapping("/auth/register")
  Api register(@Valid @RequestBody Register p) {
    return Api.ok(service.register(p.username, p.nickname, p.password), "注册成功");
  }

  @PostMapping("/auth/login")
  Api login(@Valid @RequestBody Login p) {
    return Api.ok(service.login(p.username, p.password), "登录成功");
  }

  @PostMapping("/auth/wechat/login")
  Api wechat(@Valid @RequestBody Wechat p) {
    return Api.ok(wechat.login(p.code, p.nickname), "登录成功");
  }

  @GetMapping("/auth/me")
  Api me() {
    return Api.ok(service.profile(SecurityConfig.user()));
  }

  @PatchMapping("/auth/me")
  Api nickname(@Valid @RequestBody Nickname p) {
    return Api.ok(service.nickname(SecurityConfig.user(), p.nickname), "个人资料已更新");
  }

  @PostMapping("/families")
  Api create(@Valid @RequestBody Family p) {
    return Api.ok(service.createFamily(SecurityConfig.user(), p.name, p.description), "家庭创建成功");
  }

  @PostMapping("/families/join")
  Api join(@Valid @RequestBody Join p) {
    return Api.ok(service.join(SecurityConfig.user(), p.invite_code), "加入家庭成功");
  }

  @GetMapping("/families/current")
  Api family() {
    return Api.ok(service.family(SecurityConfig.user()));
  }

  @GetMapping("/families/current/members")
  Api members() {
    return Api.ok(service.family(SecurityConfig.user()).get("members"));
  }
}
