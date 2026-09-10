package com.yykitchen.order;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.time.*;
import java.util.List;

public record OrderRequest(
    @Positive long cook_id,
    @NotNull LocalDate planned_date,
    LocalTime planned_time,
    @Size(max = 500) String note,
    @NotEmpty @Size(max = 20) List<@Valid Item> items,
    @Size(min = 1, max = 128) String requestId) {
  public OrderRequest {
    if (note != null) note = note.trim().isEmpty() ? null : note.trim();
  }

  public record Item(
      @Positive long dish_id,
      @Min(1) @Max(20) Integer quantity,
      @Size(max = 255) String note,
      @Min(0) @Max(999) Integer sort_order) {
    public Item {
      if (quantity == null) quantity = 1;
      if (sort_order == null) sort_order = 0;
      if (note != null) note = note.trim().isEmpty() ? null : note.trim();
    }
  }
}
