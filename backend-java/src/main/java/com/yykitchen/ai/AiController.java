package com.yykitchen.ai;

import com.yykitchen.catalog.Uploads;
import com.yykitchen.common.*;
import com.yykitchen.identity.*;
import jakarta.annotation.PreDestroy;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@RestController
@RequestMapping("/api/v1/ai-chat")
public class AiController {
  private final AiService service;
  private final IdentityService identity;
  private final Uploads uploads;
  private final long timeout;
  private final ThreadPoolExecutor workers =
      new ThreadPoolExecutor(4, 8, 60, TimeUnit.SECONDS, new ArrayBlockingQueue<>(32));
  private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(2);

  public AiController(
      AiService service,
      IdentityService identity,
      Uploads uploads,
      @Value("${yy.ai-timeout}") long timeout) {
    this.service = service;
    this.identity = identity;
    this.uploads = uploads;
    this.timeout = timeout;
  }

  private long family() {
    return identity.familyId(SecurityConfig.user());
  }

  @GetMapping("/conversations")
  Api conversations() {
    return Api.ok(service.conversations(family(), SecurityConfig.user()));
  }

  @GetMapping("/messages")
  Api messages(
      @RequestParam long conversation_id,
      @RequestParam(required = false) Long before_id,
      @RequestParam(defaultValue = "30") int limit) {
    return Api.ok(
        service.messages(family(), SecurityConfig.user(), conversation_id, before_id, limit));
  }

  @DeleteMapping("/conversations/{id}")
  Api delete(@PathVariable long id) {
    service.delete(family(), SecurityConfig.user(), id);
    return Api.ok(null, "AI 对话已删除");
  }

  private AiService.Turn begin(String content, Long conversation, MultipartFile image)
      throws Exception {
    long family = family();
    if (conversation != null)
      service.requireConversation(family, SecurityConfig.user(), conversation);
    return service.begin(
        family,
        SecurityConfig.user(),
        conversation,
        content,
        image == null ? null : uploads.save(family, image));
  }

  @PostMapping("/messages")
  Api message(
      @RequestParam String content,
      @RequestParam(required = false) Long conversation_id,
      @RequestParam(required = false) MultipartFile image)
      throws Exception {
    var turn = begin(content, conversation_id, image);
    try (var running = new AiGateway.Running()) {
      var deadline = scheduler.schedule(running::close, timeout + 5, TimeUnit.SECONDS);
      try {
        return Api.ok(service.generate(turn, d -> {}, running), "AI 回复已生成");
      } finally {
        deadline.cancel(false);
      }
    }
  }

  @PostMapping(value = "/messages/stream", produces = "text/event-stream")
  SseEmitter stream(
      @RequestParam String content,
      @RequestParam(required = false) Long conversation_id,
      @RequestParam(required = false) MultipartFile image)
      throws Exception {
    var turn = begin(content, conversation_id, image);
    var emitter = new SseEmitter((timeout + 10) * 1000);
    var running = new AiGateway.Running();
    var task = new AtomicReference<Future<?>>();
    Runnable cancel =
        () -> {
          running.close();
          Future<?> f = task.get();
          if (f != null) f.cancel(true);
        };
    var heartbeat =
        scheduler.scheduleAtFixedRate(
            () -> {
              try {
                emitter.send(SseEmitter.event().comment("keep-alive"));
              } catch (Exception e) {
                cancel.run();
              }
            },
            15,
            15,
            TimeUnit.SECONDS);
    var deadline =
        scheduler.schedule(
            () -> {
              sendError(emitter, new Problem(504, 50000, "AI 推理超时，请重试"));
              cancel.run();
              emitter.complete();
            },
            timeout + 5,
            TimeUnit.SECONDS);
    Runnable cleanup =
        () -> {
          heartbeat.cancel(false);
          deadline.cancel(false);
          cancel.run();
        };
    emitter.onCompletion(cleanup);
    emitter.onTimeout(cleanup);
    emitter.onError(e -> cleanup.run());
    try {
      task.set(
          workers.submit(
              () -> {
                try {
                  emitter.send(
                      SseEmitter.event().name("ready").data(Map.of("status", "processing")));
                  var result =
                      service.generate(
                          turn,
                          delta -> {
                            try {
                              emitter.send(
                                  SseEmitter.event().name("delta").data(Map.of("content", delta)));
                            } catch (Exception e) {
                              running.close();
                              throw new CompletionException(e);
                            }
                          },
                          running);
                  if (!running.closed()) {
                    emitter.send(SseEmitter.event().name("complete").data(result));
                    emitter.complete();
                  }
                } catch (Exception e) {
                  if (!running.closed()) sendError(emitter, e);
                  emitter.complete();
                } finally {
                  heartbeat.cancel(false);
                  deadline.cancel(false);
                  running.close();
                }
              }));
    } catch (RejectedExecutionException e) {
      cleanup.run();
      throw new Problem(503, 50000, "AI 服务繁忙，请稍后重试");
    }
    return emitter;
  }

  private static void sendError(SseEmitter emitter, Exception e) {
    try {
      emitter.send(
          SseEmitter.event()
              .name("error")
              .data(
                  Map.of(
                      "message",
                      e instanceof Problem ? e.getMessage() : "AI 服务暂时不可用，请稍后重试",
                      "status_code",
                      e instanceof Problem p ? p.status : 502)));
    } catch (Exception ignored) {
    }
  }

  @PreDestroy
  void close() {
    workers.shutdownNow();
    scheduler.shutdownNow();
  }
}
