package com.yykitchen.notification;

import com.yykitchen.common.*;
import com.yykitchen.identity.*;
import java.time.Duration;
import java.util.*;
import org.springframework.core.env.Environment;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.client.RestClient;

@Service
public class WechatService {
  private final Environment env;
  private final IdentityMapper users;
  private final IdentityService identity;
  private final TransactionTemplate tx;
  private final RestClient http;
  private String accessToken = "";
  private long expiresAt = 0;

  public WechatService(
      Environment env, IdentityMapper users, IdentityService identity, TransactionTemplate tx) {
    this.env = env;
    this.users = users;
    this.identity = identity;
    this.tx = tx;
    var factory = new SimpleClientHttpRequestFactory();
    factory.setConnectTimeout(Duration.ofSeconds(10));
    factory.setReadTimeout(Duration.ofSeconds(10));
    http =
        RestClient.builder()
            .requestFactory(factory)
            .baseUrl(env.getProperty("WECHAT_API_BASE_URL", "https://api.weixin.qq.com"))
            .build();
  }

  private String app() {
    String value = env.getProperty("WECHAT_APP_ID", "");
    if (value.isBlank() || env.getProperty("WECHAT_APP_SECRET", "").isBlank())
      throw new Problem(503, 40000, "微信小程序登录尚未配置");
    return value;
  }

  public Map<String, Object> login(String code, String nickname) {
    String app = app();
    Map result =
        http.get()
            .uri(
                b ->
                    b.path("/sns/jscode2session")
                        .queryParam("appid", app)
                        .queryParam("secret", env.getProperty("WECHAT_APP_SECRET"))
                        .queryParam("js_code", code.trim())
                        .queryParam("grant_type", "authorization_code")
                        .build())
            .retrieve()
            .body(Map.class);
    if (result == null || result.get("openid") == null)
      throw new Problem(401, 40000, "微信登录凭证无效或已过期");
    String openid = result.get("openid").toString(),
        union = result.get("unionid") == null ? null : result.get("unionid").toString();
    return tx.execute(
        t -> {
          String raw = users.byOpenid(openid);
          long user;
          if (raw == null) {
            String hash = sha256(openid);
            user =
                users.createUser(
                    "wx_" + hash.substring(0, 24),
                    nickname == null || nickname.isBlank()
                        ? "微信用户" + hash.substring(0, 4)
                        : nickname.trim(),
                    Credentials.hash(UUID.randomUUID().toString()),
                    openid,
                    union);
          } else {
            var found = Json.object(raw);
            if (!Boolean.TRUE.equals(found.get("is_active"))) throw Problem.forbidden("账号已停用");
            user = Json.id(found);
            if (union != null) users.unionid(user, union);
          }
          return identity.auth(user);
        });
  }

  private static String sha256(String value) {
    try {
      return HexFormat.of()
          .formatHex(
              java.security.MessageDigest.getInstance("SHA-256")
                  .digest(value.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    } catch (Exception e) {
      throw new IllegalStateException(e);
    }
  }

  private synchronized String token() {
    if (System.currentTimeMillis() < expiresAt) return accessToken;
    String app = app();
    Map result =
        http.get()
            .uri(
                b ->
                    b.path("/cgi-bin/token")
                        .queryParam("grant_type", "client_credential")
                        .queryParam("appid", app)
                        .queryParam("secret", env.getProperty("WECHAT_APP_SECRET"))
                        .build())
            .retrieve()
            .body(Map.class);
    if (result == null || result.get("access_token") == null)
      throw new IllegalStateException("微信 token 获取失败");
    accessToken = result.get("access_token").toString();
    expiresAt =
        System.currentTimeMillis()
            + Math.max(60, ((Number) result.getOrDefault("expires_in", 7200)).longValue() - 300)
                * 1000;
    return accessToken;
  }

  public void send(Map<String, Object> notification) {
    String user = users.user(Json.number(notification, "recipient_id"));
    if (user == null) throw new IllegalStateException("Recipient missing");
    Object openid = Json.object(user).get("wechat_openid");
    if (openid == null) throw new IllegalStateException("Recipient has no OpenID");
    String token = token();
    Map result =
        http.post()
            .uri(
                b ->
                    b.path("/cgi-bin/message/subscribe/send")
                        .queryParam("access_token", token)
                        .build())
            .body(
                Map.of(
                    "touser",
                    openid,
                    "template_id",
                    notification.get("template_id"),
                    "page",
                    notification.get("page"),
                    "lang",
                    "zh_CN",
                    "data",
                    notification.get("payload")))
            .retrieve()
            .body(Map.class);
    if (result == null || ((Number) result.getOrDefault("errcode", 0)).intValue() != 0)
      throw new IllegalStateException("微信订阅消息发送失败");
  }
}
