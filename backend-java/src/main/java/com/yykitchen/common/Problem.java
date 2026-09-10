package com.yykitchen.common;

public class Problem extends RuntimeException {
  public final int status;
  public final int code;

  public Problem(int status, int code, String message) {
    super(message);
    this.status = status;
    this.code = code;
  }

  public static Problem bad(String message) {
    return new Problem(400, 40000, message);
  }

  public static Problem missing(String message) {
    return new Problem(404, 40001, message);
  }

  public static Problem forbidden(String message) {
    return new Problem(403, 40300, message);
  }

  public static Problem conflict(String message) {
    return new Problem(409, 40900, message);
  }
}
