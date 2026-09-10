package com.yykitchen.ai;

import com.yykitchen.catalog.*;
import com.yykitchen.common.*;
import com.yykitchen.order.OrderService;
import java.time.Duration;
import java.util.*;
import java.util.function.Consumer;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

@Service
public class AiService {
  private final AiMapper mapper;
  private final CatalogService catalog;
  private final OrderService orders;
  private final Cache cache;
  private final AiGateway gateway;
  private final TransactionTemplate tx;

  public AiService(
      AiMapper mapper,
      CatalogService catalog,
      OrderService orders,
      Cache cache,
      AiGateway gateway,
      TransactionTemplate tx) {
    this.mapper = mapper;
    this.catalog = catalog;
    this.orders = orders;
    this.cache = cache;
    this.gateway = gateway;
    this.tx = tx;
  }

  public Map<String, Object> conversations(long family, long user) {
    return Map.of("items", mapper.conversations(family, user).stream().map(Json::object).toList());
  }

  public Map<String, Object> requireConversation(long family, long user, long conversation) {
    String raw = mapper.conversation(family, user, conversation);
    if (raw == null) throw Problem.missing("AI 对话不存在");
    return Json.object(raw);
  }

  public Map<String, Object> messages(
      long family, long user, long conversation, Long before, int limit) {
    requireConversation(family, user, conversation);
    if (limit < 1 || limit > 50 || before != null && before <= 0) throw Problem.bad("无效的分页参数");
    var rows =
        new ArrayList<>(
            mapper.messages(family, user, conversation, before, limit + 1).stream()
                .map(Json::object)
                .toList());
    boolean more = rows.size() > limit;
    if (more) rows.remove(rows.size() - 1);
    Collections.reverse(rows);
    return Map.of("items", rows, "has_more", more);
  }

  public void delete(long family, long user, long conversation) {
    if (mapper.delete(family, user, conversation) == 0) throw Problem.missing("AI 对话不存在");
  }

  public record Turn(
      long family,
      long user,
      long conversation,
      long message,
      String content,
      Uploads.Image image,
      List<Map<String, Object>> history) {}

  public Turn begin(
      long family, long user, Long conversation, String content, Uploads.Image image) {
    gateway.requireEnabled();
    if (content == null || content.isBlank() || content.length() > 2000)
      throw Problem.bad("消息内容不能为空且不能超过2000字");
    return tx.execute(
        t -> {
          long id;
          if (conversation == null) {
            id =
                mapper.createConversation(
                    family,
                    user,
                    content.strip().substring(0, Math.min(30, content.strip().length())));
          } else {
            requireConversation(family, user, conversation);
            id = conversation;
          }
          var history =
              new ArrayList<>(
                  mapper.messages(family, user, id, null, 12).stream()
                      .map(Json::object)
                      .map(m -> Json.map("role", m.get("role"), "content", m.get("content")))
                      .toList());
          Collections.reverse(history);
          String metadata =
              image == null
                  ? null
                  : Json.write(
                      Map.of(
                          "fridge_image",
                          Map.of("image_url", image.path(), "recognized_ingredients", List.of())));
          long message =
              mapper.createMessage(
                  family,
                  user,
                  id,
                  "user",
                  content.trim(),
                  image == null ? "text" : "fridge_image",
                  metadata);
          mapper.touch(id);
          return new Turn(family, user, id, message, content.trim(), image, history);
        });
  }

  public Map<String, Object> generate(Turn turn, Consumer<String> delta, AiGateway.Running running)
      throws Exception {
    var dishes = catalog.list(turn.family()).stream().limit(2000).toList();
    var preferences = catalog.preferences(turn.family()).stream().limit(2000).toList();
    var dining =
        orders.list(turn.family(), turn.user(), null, null, "accepted", true).stream()
            .limit(100)
            .toList();
    var payload =
        Json.map(
            "content",
            turn.content(),
            "dishes",
            dishes,
            "preferences",
            preferences,
            "dining_history",
            dining,
            "history",
            turn.history(),
            "image_data_url",
            turn.image() == null ? null : turn.image().dataUrl());
    String key =
        "ai:"
            + turn.family()
            + ":"
            + turn.user()
            + ":"
            + Json.hash(List.of(payload, gateway.fingerprint()));
    String cached = cache.get(key);
    Map<String, Object> result;
    if (cached != null) {
      result = Json.object(cached);
      AiGateway.validate(result);
      delta.accept(result.get("summary").toString());
    } else {
      payload.put("request_id", UUID.randomUUID().toString());
      result = gateway.generate(payload, delta, running);
      cache.put(key, Json.write(result), Duration.ofMinutes(5));
    }
    if (running.closed()) throw new java.util.concurrent.CancellationException();
    return finish(turn, result);
  }

  private Map<String, Object> finish(Turn turn, Map<String, Object> result) {
    return tx.execute(
        t -> {
          requireConversation(turn.family(), turn.user(), turn.conversation());
          var metadata = new LinkedHashMap<>(result);
          StringBuilder content = new StringBuilder(result.get("summary").toString());
          int index = 0;
          for (var r : (List<Map<String, Object>>) result.get("recommendations")) {
            int rating = ((Number) r.get("rating")).intValue();
            content
                .append("\n")
                .append(++index)
                .append(". ")
                .append(r.get("dish_name"))
                .append(" ")
                .append("★".repeat(rating))
                .append("☆".repeat(5 - rating));
            if (r.get("reason") != null) content.append("\n推荐理由：").append(r.get("reason"));
          }
          metadata.put("action_draft", null);
          metadata.put("confirmation_required", false);
          metadata.put("confidence", null);
          if (turn.image() != null) {
            Object ingredients = result.getOrDefault("recognized_ingredients", List.of());
            metadata.put(
                "fridge_image",
                Map.of("image_url", turn.image().path(), "recognized_ingredients", ingredients));
            mapper.imageAnalysis(
                turn.family(),
                turn.user(),
                turn.image().path(),
                Json.write(ingredients),
                Objects.toString(result.get("raw_model_output"), ""));
          }
          long assistant =
              mapper.createMessage(
                  turn.family(),
                  turn.user(),
                  turn.conversation(),
                  "assistant",
                  content.toString(),
                  "tool_result",
                  Json.write(metadata));
          mapper.touch(turn.conversation());
          var conversation = requireConversation(turn.family(), turn.user(), turn.conversation());
          var message = Json.object(mapper.message(turn.family(), turn.user(), assistant));
          conversation.put(
              "last_message_preview", content.substring(0, Math.min(60, content.length())));
          conversation.put("last_message_at", message.get("created_at"));
          return Map.of(
              "conversation",
              conversation,
              "user_message",
              Json.object(mapper.message(turn.family(), turn.user(), turn.message())),
              "assistant_message",
              message);
        });
  }
}
