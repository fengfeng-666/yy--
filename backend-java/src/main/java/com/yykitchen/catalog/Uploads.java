package com.yykitchen.catalog;

import com.yykitchen.common.Problem;
import java.io.IOException;
import java.nio.file.*;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.config.annotation.*;

@Service
public class Uploads implements WebMvcConfigurer {
  private final Path root;
  private final long max;

  public Uploads(@Value("${yy.upload-dir}") String dir, @Value("${MAX_UPLOAD_SIZE_MB:10}") long max)
      throws IOException {
    root = Path.of(dir).toAbsolutePath().normalize();
    this.max = max * 1024 * 1024;
    Files.createDirectories(root);
  }

  public record Image(String path, String dataUrl) {}

  public Image save(long family, MultipartFile file) throws IOException {
    if (file == null || file.isEmpty() || file.getSize() > max) throw Problem.bad("上传图片为空或超过大小限制");
    byte[] bytes = file.getBytes();
    String mime;
    if (bytes.length >= 3
        && (bytes[0] & 255) == 255
        && (bytes[1] & 255) == 216
        && (bytes[2] & 255) == 255) mime = "image/jpeg";
    else if (bytes.length >= 8
        && Arrays.equals(
            Arrays.copyOf(bytes, 8), new byte[] {(byte) 137, 80, 78, 71, 13, 10, 26, 10}))
      mime = "image/png";
    else if (bytes.length >= 12
        && new String(bytes, 0, 4, java.nio.charset.StandardCharsets.US_ASCII).equals("RIFF")
        && new String(bytes, 8, 4, java.nio.charset.StandardCharsets.US_ASCII).equals("WEBP"))
      mime = "image/webp";
    else throw Problem.bad("仅支持 JPG、PNG、WEBP 图片上传");
    String suffix =
        Map.of("image/jpeg", ".jpg", "image/png", ".png", "image/webp", ".webp").get(mime);
    String relative = "families/" + family + "/images/" + UUID.randomUUID() + suffix;
    Path path = root.resolve(relative);
    Files.createDirectories(path.getParent());
    Files.write(path, bytes, StandardOpenOption.CREATE_NEW);
    return new Image(
        "/uploads/" + relative,
        "data:" + mime + ";base64," + Base64.getEncoder().encodeToString(bytes));
  }

  @Override
  public void addResourceHandlers(ResourceHandlerRegistry registry) {
    registry.addResourceHandler("/uploads/**").addResourceLocations(root.toUri().toString());
  }
}
