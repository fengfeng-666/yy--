package com.yykitchen.chat;

import com.yykitchen.common.*;
import java.util.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ChatService {
  private final ChatMapper mapper;

  public ChatService(ChatMapper mapper) {
    this.mapper = mapper;
  }

  public Map<String, Object> list(long family, Long before, Long after, int limit) {
    if (limit < 1 || limit > 50 || before != null && before <= 0 || after != null && after <= 0)
      throw Problem.bad("无效的分页参数");
    if (before != null && after != null) throw Problem.bad("before_id 和 after_id 不能同时使用");
    var rows =
        new ArrayList<>(
            mapper.list(family, before, after, limit + 1).stream().map(Json::object).toList());
    boolean more = rows.size() > limit;
    if (more) rows.remove(rows.size() - 1);
    if (after == null) Collections.reverse(rows);
    return Map.of("items", rows, "has_more", more);
  }

  @Transactional
  public Map<String, Object> send(long family, long user, String content) {
    long id = mapper.create(family, user, content.trim());
    return Json.object(mapper.get(family, id));
  }

  public Map<String, Object> unread(long family, long user) {
    return Map.of("unread_count", mapper.unread(family, user));
  }

  @Transactional
  public Map<String, Object> read(long family, long user, long id) {
    if (mapper.get(family, id) == null) throw Problem.missing("消息不存在");
    mapper.read(family, user, id);
    return unread(family, user);
  }
}
