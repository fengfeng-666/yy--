package com.yykitchen.common;

public record Api(int code, String message, Object data) {
  public static Api ok(Object data) {
    return new Api(0, "success", data);
  }

  public static Api ok(Object data, String message) {
    return new Api(0, message, data);
  }
}
