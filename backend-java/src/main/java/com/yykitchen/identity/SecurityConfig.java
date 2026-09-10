package com.yykitchen.identity;

import com.yykitchen.common.*;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import java.io.IOException;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.*;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.*;
import org.springframework.web.filter.OncePerRequestFilter;

@Configuration
@org.springframework.boot.autoconfigure.condition.ConditionalOnWebApplication(
    type =
        org.springframework.boot.autoconfigure.condition.ConditionalOnWebApplication.Type.SERVLET)
public class SecurityConfig {
  static void error(HttpServletResponse response, Problem p) throws IOException {
    response.setStatus(p.status);
    response.setContentType("application/json;charset=UTF-8");
    response.getWriter().write(Json.write(new Api(p.code, p.getMessage(), null)));
  }

  @Bean
  SecurityFilterChain security(
      HttpSecurity http,
      Credentials credentials,
      IdentityMapper users,
      @Value("${yy.cors-origins}") String origins)
      throws Exception {
    CorsConfiguration cors = new CorsConfiguration();
    var values =
        new com.fasterxml.jackson.databind.ObjectMapper().readValue(origins, String[].class);
    cors.setAllowedOrigins(Arrays.asList(values));
    cors.setAllowedMethods(List.of("GET", "POST", "PATCH", "DELETE", "OPTIONS"));
    cors.setAllowedHeaders(List.of("Authorization", "Content-Type", "X-Request-ID"));
    cors.setExposedHeaders(List.of("X-Request-ID"));
    var source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/**", cors);
    return http.csrf(c -> c.disable())
        .cors(c -> c.configurationSource(source))
        .sessionManagement(c -> c.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
        .authorizeHttpRequests(
            a ->
                a.dispatcherTypeMatchers(DispatcherType.ASYNC, DispatcherType.ERROR)
                    .permitAll()
                    .requestMatchers(
                        "/api/v1/health",
                        "/api/v1/auth/login",
                        "/api/v1/auth/register",
                        "/api/v1/auth/wechat/login",
                        "/uploads/**")
                    .permitAll()
                    .anyRequest()
                    .authenticated())
        .exceptionHandling(
            e ->
                e.authenticationEntryPoint(
                    (req, res, ex) -> error(res, new Problem(401, 40100, "请先登录"))))
        .addFilterBefore(
            new OncePerRequestFilter() {
              @Override
              protected void doFilterInternal(
                  HttpServletRequest req, HttpServletResponse res, FilterChain chain)
                  throws ServletException, IOException {
                String rid = req.getHeader("X-Request-ID");
                res.setHeader(
                    "X-Request-ID",
                    rid != null && rid.matches("[A-Za-z0-9_-]{1,128}")
                        ? rid
                        : UUID.randomUUID().toString());
                String auth = req.getHeader("Authorization");
                if (auth != null) {
                  try {
                    if (!auth.regionMatches(true, 0, "Bearer ", 0, 7))
                      throw new Problem(401, 40100, "请先登录");
                    long id = credentials.decode(auth.substring(7));
                    String json = users.user(id);
                    if (json == null || !Boolean.TRUE.equals(Json.object(json).get("is_active")))
                      throw new Problem(401, 40100, "登录状态无效，请重新登录");
                    SecurityContextHolder.getContext()
                        .setAuthentication(
                            new UsernamePasswordAuthenticationToken(id, null, List.of()));
                  } catch (Problem p) {
                    error(res, p);
                    return;
                  }
                }
                chain.doFilter(req, res);
              }
            },
            UsernamePasswordAuthenticationFilter.class)
        .build();
  }

  public static long user() {
    return ((Number) SecurityContextHolder.getContext().getAuthentication().getPrincipal())
        .longValue();
  }
}
