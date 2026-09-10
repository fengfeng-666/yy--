package com.yykitchen.catalog;

import com.yykitchen.common.*;
import java.time.Duration;
import java.util.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class CatalogService {
  private final CatalogMapper mapper;
  private final Cache cache;

  public CatalogService(CatalogMapper mapper, Cache cache) {
    this.mapper = mapper;
    this.cache = cache;
  }

  public List<Map<String, Object>> list(long family) {
    return mapper.list(family).stream().map(Json::object).toList();
  }

  // The DB-derived version also notices writes by a rollback instance or administrative SQL.
  public String version(long family) {
    return mapper.version(family);
  }

  public Map<String, Object> detail(long family, long id) {
    String value =
        cache.remember(
            "dish:" + family + ":" + version(family) + ":" + id,
            Duration.ofMinutes(10),
            () -> mapper.detail(family, id));
    if (value == null) throw Problem.missing("菜品不存在");
    return Json.object(value);
  }

  @Transactional
  public Map<String, Object> create(long family, CatalogController.DishRequest p) {
    return Json.object(mapper.detail(family, mapper.create(family, p)));
  }

  @Transactional
  public Map<String, Object> update(long family, long id, CatalogController.DishRequest p) {
    if (mapper.update(family, id, p) == 0) throw Problem.missing("菜品不存在");
    return Json.object(mapper.detail(family, id));
  }

  @Transactional
  public void delete(long family, long id) {
    if (mapper.detail(family, id) == null) throw Problem.missing("菜品不存在");
    if (mapper.orderReferences(id) > 0) throw Problem.conflict("菜品已有点菜记录，不能删除，请改为下架");
    mapper.delete(family, id);
  }

  public List<Map<String, Object>> preferences(long family) {
    String raw =
        cache.remember(
            "preferences:" + family + ":" + version(family),
            Duration.ofMinutes(5),
            () ->
                Json.write(
                    Map.of(
                        "items", mapper.preferences(family).stream().map(Json::object).toList())));
    return (List<Map<String, Object>>) Json.object(raw).get("items");
  }
}
