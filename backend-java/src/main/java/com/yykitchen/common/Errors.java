package com.yykitchen.common;

import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

@RestControllerAdvice
public class Errors {
  @ExceptionHandler(Problem.class)
  ResponseEntity<Api> problem(Problem e) {
    return ResponseEntity.status(e.status).body(new Api(e.code, e.getMessage(), null));
  }

  @ExceptionHandler({
    MethodArgumentNotValidException.class,
    HttpMessageNotReadableException.class,
    org.springframework.web.bind.MissingServletRequestParameterException.class,
    org.springframework.web.method.annotation.MethodArgumentTypeMismatchException.class,
    org.springframework.web.multipart.support.MissingServletRequestPartException.class,
    IllegalArgumentException.class
  })
  ResponseEntity<Api> invalid(Exception e) {
    return ResponseEntity.status(422).body(new Api(40000, "请求参数不合法", null));
  }

  @ExceptionHandler(MaxUploadSizeExceededException.class)
  ResponseEntity<Api> upload(Exception e) {
    return ResponseEntity.status(413).body(new Api(40000, "图片超过大小限制", null));
  }

  @ExceptionHandler(DataIntegrityViolationException.class)
  ResponseEntity<Api> integrity(Exception e) {
    return ResponseEntity.status(409).body(new Api(40900, "数据冲突，请刷新后重试", null));
  }

  @ExceptionHandler(Exception.class)
  ResponseEntity<Api> unexpected(Exception e) {
    LoggerFactory.getLogger(Errors.class).error("Request failed", e);
    return ResponseEntity.status(500).body(new Api(50000, "服务暂时不可用", null));
  }

  @ExceptionHandler(org.springframework.web.servlet.resource.NoResourceFoundException.class)
  ResponseEntity<Api> missing(Exception e) {
    return ResponseEntity.status(404).body(new Api(40001, "资源不存在", null));
  }
}
