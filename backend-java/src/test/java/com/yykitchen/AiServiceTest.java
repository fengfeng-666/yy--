package com.yykitchen;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import com.yykitchen.ai.*;
import com.yykitchen.catalog.*;
import com.yykitchen.common.*;
import com.yykitchen.order.OrderService;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.springframework.transaction.support.TransactionTemplate;

class AiServiceTest {
  @Test
  void generationFailureDoesNotPersistAssistant() throws Exception {
    var mapper = mock(AiMapper.class);
    var catalog = mock(CatalogService.class);
    var orders = mock(OrderService.class);
    var gateway = mock(AiGateway.class);
    var cache = mock(Cache.class);
    when(catalog.list(1)).thenReturn(List.of());
    when(catalog.preferences(1)).thenReturn(List.of());
    when(orders.list(1, 2, null, null, "accepted", true)).thenReturn(List.of());
    when(gateway.fingerprint()).thenReturn("config");
    when(gateway.generate(anyMap(), any(), any())).thenThrow(new Problem(502, 50000, "failed"));
    var service =
        new AiService(mapper, catalog, orders, cache, gateway, mock(TransactionTemplate.class));
    assertThrows(
        Problem.class,
        () ->
            service.generate(
                new AiService.Turn(1, 2, 3, 4, "hello", null, List.of()),
                s -> {},
                new AiGateway.Running()));
    verifyNoInteractions(mapper);
    verify(cache, never()).put(anyString(), anyString(), any());
  }

  @Test
  void conversationOwnershipIsRequired() {
    var mapper = mock(AiMapper.class);
    var service =
        new AiService(
            mapper,
            mock(CatalogService.class),
            mock(OrderService.class),
            mock(Cache.class),
            mock(AiGateway.class),
            mock(TransactionTemplate.class));
    assertEquals(
        404, assertThrows(Problem.class, () -> service.messages(1, 2, 3, null, 30)).status);
    verify(mapper, never()).messages(anyLong(), anyLong(), anyLong(), any(), anyInt());
  }
}
