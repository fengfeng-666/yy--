package com.yykitchen.identity;

import com.yykitchen.common.*;
import java.util.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class IdentityService {
  private final IdentityMapper mapper;
  private final Credentials credentials;

  public IdentityService(IdentityMapper mapper, Credentials credentials) {
    this.mapper = mapper;
    this.credentials = credentials;
  }

  public long familyId(long user) {
    Long id = mapper.familyId(user);
    if (id == null) throw Problem.missing("当前还未加入家庭");
    return id;
  }

  public Map<String, Object> profile(long user) {
    return Json.object(mapper.profile(user));
  }

  public Map<String, Object> auth(long user) {
    return Map.of("user", profile(user), "tokens", credentials.tokens(user));
  }

  @Transactional
  public Map<String, Object> register(String username, String nickname, String password) {
    username = username.trim().toLowerCase(Locale.ROOT);
    if (!username.matches("[\\p{L}\\p{N}_-]{3,32}")) throw Problem.bad("用户名仅支持字母、数字、下划线和短横线");
    if (mapper.byUsername(username) != null) throw new Problem(409, 40904, "用户名已存在");
    return auth(
        mapper.createUser(
            username,
            nickname == null || nickname.isBlank() ? username : nickname.trim(),
            Credentials.hash(password),
            null,
            null));
  }

  public Map<String, Object> login(String username, String password) {
    String json = mapper.byUsername(username.trim().toLowerCase(Locale.ROOT));
    if (json == null) throw new Problem(401, 40102, "用户名或密码错误");
    var user = Json.object(json);
    if (!Credentials.verify(password, (String) user.get("password_hash")))
      throw new Problem(401, 40102, "用户名或密码错误");
    if (!Boolean.TRUE.equals(user.get("is_active"))) throw Problem.forbidden("账号已停用");
    return auth(Json.id(user));
  }

  @Transactional
  public Map<String, Object> nickname(long user, String name) {
    mapper.nickname(user, name.trim());
    return profile(user);
  }

  public Map<String, Object> family(long user) {
    return Json.object(mapper.family(familyId(user)));
  }

  @Transactional
  public Map<String, Object> createFamily(long user, String name, String description) {
    mapper.lockUser(user);
    ensureNoFamily(user);
    String code =
        UUID.randomUUID().toString().replace("-", "").substring(0, 10).toUpperCase(Locale.ROOT);
    long family = mapper.createFamily(name.trim(), description, code, user);
    mapper.addMember(family, user, "owner");
    return Map.of("family", Json.object(mapper.family(family)), "needs_onboarding", false);
  }

  @Transactional
  public Map<String, Object> join(long user, String code) {
    mapper.lockUser(user);
    ensureNoFamily(user);
    String raw = mapper.invited(code.trim().toUpperCase(Locale.ROOT));
    if (raw == null) throw Problem.missing("邀请码不存在，请检查后重试");
    var f = Json.object(raw);
    long id = Json.id(f);
    if (mapper.memberCount(id) >= Json.number(f, "max_members"))
      throw new Problem(409, 40902, "当前家庭人数已满");
    mapper.addMember(id, user, "member");
    return Map.of("family", Json.object(mapper.family(id)), "needs_onboarding", false);
  }

  private void ensureNoFamily(long user) {
    if (mapper.familyId(user) != null) throw new Problem(409, 40901, "当前用户已加入家庭");
  }
}
