package com.yykitchen.identity;

import com.yykitchen.common.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.time.Instant;
import java.util.*;
import javax.crypto.Mac;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class Credentials {
  private final byte[] secret;
  private final long minutes;

  public Credentials(
      @Value("${yy.jwt-secret}") String secret, @Value("${yy.token-minutes}") long minutes) {
    if (secret.getBytes(StandardCharsets.UTF_8).length < 32)
      throw new IllegalArgumentException("JWT secret must contain at least 32 bytes");
    this.secret = secret.getBytes(StandardCharsets.UTF_8);
    this.minutes = minutes;
  }

  private static byte[] derive(String password, String salt, int iterations) throws Exception {
    var spec =
        new PBEKeySpec(
            password.toCharArray(), salt.getBytes(StandardCharsets.UTF_8), iterations, 256);
    try {
      return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded();
    } finally {
      spec.clearPassword();
    }
  }

  public static String hash(String password) {
    try {
      byte[] salt = new byte[16];
      new SecureRandom().nextBytes(salt);
      String s = HexFormat.of().formatHex(salt);
      return "pbkdf2_sha256$600000$"
          + s
          + "$"
          + HexFormat.of().formatHex(derive(password, s, 600000));
    } catch (Exception e) {
      throw new IllegalStateException(e);
    }
  }

  public static boolean verify(String password, String encoded) {
    try {
      String[] parts = encoded.split("\\$");
      int iterations = Integer.parseInt(parts[1]);
      return parts.length == 4
          && parts[0].equals("pbkdf2_sha256")
          && iterations > 0
          && iterations <= 2000000
          && MessageDigest.isEqual(
              derive(password, parts[2], iterations), HexFormat.of().parseHex(parts[3]));
    } catch (Exception e) {
      return false;
    }
  }

  private byte[] sign(String text) {
    try {
      Mac mac = Mac.getInstance("HmacSHA256");
      mac.init(new SecretKeySpec(secret, "HmacSHA256"));
      return mac.doFinal(text.getBytes(StandardCharsets.US_ASCII));
    } catch (Exception e) {
      throw new IllegalStateException(e);
    }
  }

  private String encode(Object object) {
    return Base64.getUrlEncoder()
        .withoutPadding()
        .encodeToString(Json.write(object).getBytes(StandardCharsets.UTF_8));
  }

  public Map<String, Object> tokens(long user) {
    Instant now = Instant.now(), expiry = now.plusSeconds(minutes * 60);
    String content =
        encode(Map.of("alg", "HS256", "typ", "JWT"))
            + "."
            + encode(
                Map.of(
                    "sub",
                    Long.toString(user),
                    "type",
                    "access",
                    "iat",
                    now.getEpochSecond(),
                    "exp",
                    expiry.getEpochSecond()));
    return Map.of(
        "access_token",
        content + "." + Base64.getUrlEncoder().withoutPadding().encodeToString(sign(content)),
        "token_type",
        "Bearer",
        "expires_at",
        expiry.toString());
  }

  public long decode(String token) {
    try {
      String[] parts = token.split("\\.");
      if (parts.length != 3) throw new IllegalArgumentException();
      var header =
          Json.object(new String(Base64.getUrlDecoder().decode(parts[0]), StandardCharsets.UTF_8));
      if (!"HS256".equals(header.get("alg"))
          || !MessageDigest.isEqual(
              sign(parts[0] + "." + parts[1]), Base64.getUrlDecoder().decode(parts[2])))
        throw new IllegalArgumentException();
      var payload =
          Json.object(new String(Base64.getUrlDecoder().decode(parts[1]), StandardCharsets.UTF_8));
      if (!"access".equals(payload.get("type"))) throw new IllegalArgumentException();
      long now = Instant.now().getEpochSecond();
      if (Json.number(payload, "exp") <= now) throw new Problem(401, 40101, "登录已过期，请重新登录");
      if (payload.containsKey("iat") && Json.number(payload, "iat") > now)
        throw new IllegalArgumentException();
      long user = Long.parseLong(payload.get("sub").toString());
      if (user <= 0) throw new IllegalArgumentException();
      return user;
    } catch (Problem p) {
      throw p;
    } catch (Exception e) {
      throw new Problem(401, 40100, "登录凭证无效");
    }
  }
}
