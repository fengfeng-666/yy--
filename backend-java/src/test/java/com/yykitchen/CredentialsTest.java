package com.yykitchen;

import static org.junit.jupiter.api.Assertions.*;

import com.yykitchen.common.Problem;
import com.yykitchen.identity.Credentials;
import org.junit.jupiter.api.Test;

class CredentialsTest {
  @Test
  void passwordAndTokensAreCompatible() {
    String hash = Credentials.hash("中文-password");
    assertTrue(Credentials.verify("中文-password", hash));
    assertFalse(Credentials.verify("wrong", hash));
    assertFalse(Credentials.verify("x", "broken"));
    var credentials = new Credentials("test-secret-at-least-32-characters-long", 30);
    String token = credentials.tokens(7).get("access_token").toString();
    assertEquals(7, credentials.decode(token));
    assertThrows(
        Problem.class, () -> credentials.decode(token.substring(0, token.length() - 5) + "xxxxx"));
  }

  @Test
  void expiredTokenIsDistinct() {
    var credentials = new Credentials("test-secret-at-least-32-characters-long", -1);
    var error =
        assertThrows(
            Problem.class,
            () -> credentials.decode(credentials.tokens(7).get("access_token").toString()));
    assertEquals(40101, error.code);
  }
}
