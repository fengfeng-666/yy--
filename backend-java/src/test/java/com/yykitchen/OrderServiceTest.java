package com.yykitchen;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import com.yykitchen.catalog.CatalogMapper;
import com.yykitchen.common.*;
import com.yykitchen.identity.IdentityMapper;
import com.yykitchen.notification.NotificationService;
import com.yykitchen.order.*;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.transaction.support.TransactionTemplate;

class OrderServiceTest {
  @Test
  void requestKeyConflictNeverMutatesOrder() {
    var mapper = mock(OrderMapper.class);
    when(mapper.existing(1, 2, "same")).thenReturn("{\"id\":8,\"request_hash\":\"different\"}");
    var service =
        new OrderService(
            mapper,
            mock(CatalogMapper.class),
            mock(IdentityMapper.class),
            mock(NotificationService.class),
            mock(Cache.class),
            mock(TransactionTemplate.class));
    var request =
        new OrderRequest(
            3, LocalDate.now(), null, null, List.of(new OrderRequest.Item(4, 1, null, 0)), "same");
    assertEquals(409, assertThrows(Problem.class, () -> service.create(1, 2, request)).status);
    verify(mapper, never()).create(anyLong(), anyLong(), any(), anyString());
  }

  @Test
  void batchLoadUsesTwoMapperQueries() {
    var mapper = mock(OrderMapper.class);
    when(mapper.headers(1, 2, null, null, null, false))
        .thenReturn(List.of("{\"id\":1}", "{\"id\":2}"));
    when(mapper.items(1, List.of(1L, 2L)))
        .thenReturn(List.of("{\"id\":3,\"meal_order_id\":1}", "{\"id\":4,\"meal_order_id\":2}"));
    var service =
        new OrderService(
            mapper,
            mock(CatalogMapper.class),
            mock(IdentityMapper.class),
            mock(NotificationService.class),
            mock(Cache.class),
            mock(TransactionTemplate.class));
    assertEquals(2, service.list(1, 2, null, null, null, false).size());
    verify(mapper).headers(1, 2, null, null, null, false);
    verify(mapper).items(1, List.of(1L, 2L));
    verifyNoMoreInteractions(mapper);
  }
}
