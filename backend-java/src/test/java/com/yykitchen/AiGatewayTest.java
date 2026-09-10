package com.yykitchen;

import static org.junit.jupiter.api.Assertions.*;

import com.sun.net.httpserver.HttpServer;
import com.yykitchen.ai.AiGateway;
import com.yykitchen.common.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import org.junit.jupiter.api.Test;

class AiGatewayTest {
  @Test
  void parsesFragmentedSseAndChecksServiceToken() throws Exception {
    var server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
    server.createContext(
        "/internal/v1/recommendations/stream",
        exchange -> {
          if (!"Bearer secret".equals(exchange.getRequestHeaders().getFirst("Authorization"))) {
            exchange.sendResponseHeaders(401, -1);
            exchange.close();
            return;
          }
          exchange.getResponseHeaders().add("Content-Type", "text/event-stream");
          exchange.sendResponseHeaders(200, 0);
          var output = exchange.getResponseBody();
          String sse =
              "event: ready\ndata: {}\n\n: keep-alive\n\nevent: delta\ndata: {\"content\":\"你好\"}\n\nevent: complete\ndata: {\"summary\":\"你好\",\"recommendations\":[]}\n\n";
          for (byte b : sse.getBytes(StandardCharsets.UTF_8)) {
            output.write(b);
            output.flush();
          }
          exchange.close();
        });
    server.start();
    try (var running = new AiGateway.Running()) {
      var gateway =
          new AiGateway("http://127.0.0.1:" + server.getAddress().getPort(), "secret", true, 5);
      var text = new StringBuilder();
      var result = gateway.generate(Map.of("request_id", "test"), text::append, running);
      assertEquals("你好", text.toString());
      assertEquals("你好", result.get("summary"));
    } finally {
      server.stop(0);
    }
  }

  @Test
  void partialStreamNeverReturnsSuccess() throws Exception {
    var server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
    server.createContext(
        "/internal/v1/recommendations/stream",
        exchange -> {
          exchange.sendResponseHeaders(200, 0);
          exchange
              .getResponseBody()
              .write(
                  "event: delta\ndata: {\"content\":\"partial\"}\n\n"
                      .getBytes(StandardCharsets.UTF_8));
          exchange.close();
        });
    server.start();
    try (var running = new AiGateway.Running()) {
      var gateway =
          new AiGateway("http://127.0.0.1:" + server.getAddress().getPort(), "secret", true, 5);
      assertThrows(Problem.class, () -> gateway.generate(Map.of(), d -> {}, running));
    } finally {
      server.stop(0);
    }
  }
}
