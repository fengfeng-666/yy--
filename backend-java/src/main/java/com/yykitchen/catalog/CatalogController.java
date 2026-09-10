package com.yykitchen.catalog;

import com.yykitchen.common.*;
import com.yykitchen.identity.*;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.io.IOException;
import java.util.Map;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

@RestController
@RequestMapping("/api/v1")
public class CatalogController {
  private final CatalogService service;
  private final IdentityService identity;
  private final Uploads uploads;

  public CatalogController(CatalogService service, IdentityService identity, Uploads uploads) {
    this.service = service;
    this.identity = identity;
    this.uploads = uploads;
  }

  public record DishRequest(
      @NotBlank @Size(max = 100) String name,
      @Size(max = 500) String description,
      @NotNull @DecimalMin("0") @DecimalMax("99999") Double price,
      @Size(max = 500) String image_url,
      Boolean is_available) {
    public DishRequest {
      if (name != null) name = name.trim();
      if (description != null) description = description.trim();
      if (image_url != null) image_url = image_url.trim();
      if (is_available == null) is_available = true;
    }
  }

  private long family() {
    return identity.familyId(SecurityConfig.user());
  }

  @GetMapping("/dishes")
  Api list() {
    return Api.ok(service.list(family()));
  }

  @GetMapping("/dishes/{id}")
  Api detail(@PathVariable long id) {
    return Api.ok(service.detail(family(), id));
  }

  @PostMapping("/dishes")
  Api create(@Valid @RequestBody DishRequest p) {
    return Api.ok(service.create(family(), p), "菜品创建成功");
  }

  @PatchMapping("/dishes/{id}")
  Api update(@PathVariable long id, @Valid @RequestBody DishRequest p) {
    return Api.ok(service.update(family(), id, p), "菜品更新成功");
  }

  @DeleteMapping("/dishes/{id}")
  Api delete(@PathVariable long id) {
    service.delete(family(), id);
    return Api.ok(null, "菜品删除成功");
  }

  @PostMapping("/uploads/images")
  Api upload(@RequestParam MultipartFile file) throws IOException {
    var saved = uploads.save(family(), file);
    return Api.ok(
        Map.of(
            "path",
            saved.path(),
            "url",
            ServletUriComponentsBuilder.fromCurrentContextPath().path(saved.path()).toUriString()),
        "图片上传成功");
  }
}
