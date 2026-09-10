# Java 业务后端

Java 17、Spring Boot 3.5、Spring Security、MyBatis、PostgreSQL、Redis 和 Flyway。

从项目根目录执行 `mvn -B -ntp -f backend-java/pom.xml verify` 完成单元测试和真实数据库/缓存集成测试，要求 Docker 可用。只执行单元测试用 `test`；启动使用 `mvn spring-boot:run`。

配置通过进程环境变量注入，参见 `.env.example`。默认监听 8001。AI 服务通过 `AI_SERVICE_URL` 与 `AI_SERVICE_TOKEN` 连接，Java 不配置模型密钥。

完整接口约定、迁移步骤、部署与回退说明见 [重构文档](../docs/REFACTOR.md)。
