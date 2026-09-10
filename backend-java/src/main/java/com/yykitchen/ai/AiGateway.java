package com.yykitchen.ai;

import com.yykitchen.common.*;
import java.io.*;
import java.net.URI;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.Consumer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class AiGateway {
  private final HttpClient http =
      HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
  private final String url, token;
  private final boolean enabled;
  private final long timeout;

  public AiGateway(
      @Value("${yy.ai-url}") String url,
      @Value("${yy.ai-token}") String token,
      @Value("${yy.ai-enabled}") boolean enabled,
      @Value("${yy.ai-timeout}") long timeout) {
    this.url = url.replaceAll("/$", "");
    this.token = token;
    this.enabled = enabled;
    this.timeout = timeout;
  }

  public void requireEnabled() {
    if (!enabled || token.isBlank()) throw new Problem(503, 50000, "AI 服务尚未配置");
  }

  private HttpRequest.Builder request(String path) {
    requireEnabled();
    return HttpRequest.newBuilder(URI.create(url + path))
        .header("Authorization", "Bearer " + token)
        .timeout(Duration.ofSeconds(timeout));
  }

  public String fingerprint() throws Exception {
    var response =
        http.send(
            request("/internal/v1/config").GET().build(), HttpResponse.BodyHandlers.ofString());
    if (response.statusCode() != 200) throw new Problem(502, 50000, "AI 服务暂时不可用");
    return Json.object(response.body()).get("fingerprint").toString();
  }

  public static class Running implements AutoCloseable {
    private boolean closed;
    private InputStream stream;
    private CompletableFuture<?> request;

    public synchronized void request(CompletableFuture<?> value) {
      request = value;
      if (closed) value.cancel(true);
    }

    public synchronized void stream(InputStream value) throws IOException {
      stream = value;
      if (closed) {
        value.close();
        throw new IOException("Stream cancelled");
      }
    }

    public synchronized boolean closed() {
      return closed;
    }

    @Override
    public synchronized void close() {
      closed = true;
      if (request != null) request.cancel(true);
      if (stream != null)
        try {
          stream.close();
        } catch (IOException ignored) {
        }
    }
  }

  public Map<String, Object> generate(
      Map<String, Object> payload, Consumer<String> delta, Running running) throws Exception {
    var future =
        http.sendAsync(
            request("/internal/v1/recommendations/stream")
                .header("Content-Type", "application/json")
                .header("Accept", "text/event-stream")
                .POST(HttpRequest.BodyPublishers.ofString(Json.write(payload)))
                .build(),
            HttpResponse.BodyHandlers.ofInputStream());
    running.request(future);
    var response = future.get(timeout, TimeUnit.SECONDS);
    running.stream(response.body());
    if (response.statusCode() != 200) throw new Problem(502, 50000, "AI 服务暂时不可用");
    try (var reader =
        new BufferedReader(new InputStreamReader(response.body(), StandardCharsets.UTF_8))) {
      String event = "message";
      StringBuilder data = new StringBuilder();
      String line;
      while ((line = reader.readLine()) != null) {
        if (running.closed()) throw new CancellationException();
        if (line.isEmpty()) {
          if (!data.isEmpty()) {
            var body = Json.object(data.toString());
            if (event.equals("delta")) {
              if (!(body.get("content") instanceof String text))
                throw new IOException("Invalid delta");
              delta.accept(text);
            }
            if (event.equals("error"))
              throw new Problem(
                  body.get("status_code") instanceof Number n ? n.intValue() : 502,
                  50000,
                  Objects.toString(body.get("message"), "AI 生成失败"));
            if (event.equals("complete")) {
              validate(body);
              return body;
            }
          }
          event = "message";
          data.setLength(0);
        } else if (line.startsWith("event:")) event = line.substring(6).trim();
        else if (line.startsWith("data:")) {
          if (!data.isEmpty()) data.append('\n');
          data.append(line.substring(5).stripLeading());
          if (data.length() > 1000000) throw new IOException("AI response too large");
        }
      }
    }
    throw new Problem(502, 50000, "AI 流式响应意外中断，请重试");
  }

  public static void validate(Map<String, Object> result) {
    if (!(result.get("summary") instanceof String summary)
        || summary.isBlank()
        || !(result.get("recommendations") instanceof List<?> items))
      throw new Problem(502, 50000, "AI 返回格式解析失败");
    for (Object item : items) {
      if (!(item instanceof Map<?, ?> r)
          || !(r.get("dish_name") instanceof String)
          || !(r.get("rating") instanceof Number rating)
          || rating.intValue() < 1
          || rating.intValue() > 5) throw new Problem(502, 50000, "AI 推荐格式不合法");
    }
  }
}
