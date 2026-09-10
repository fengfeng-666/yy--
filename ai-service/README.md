# Python AI 服务

无状态内部 FastAPI 服务，通过 LangChain 进行检索、多模态调用和推荐生成。无业务数据库连接，仅处理 Java 提供的授权家庭上下文。

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e '.[dev]'
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m uvicorn ai_service.main:app --port 8002
```

启动前按 `.env.example` 设置进程环境变量。模型未配置时健康检查仍可用，推理请求返回 503。内部接口需要服务令牌，健康接口无需认证。

详细协议与整体部署见 [重构文档](../docs/REFACTOR.md)。
