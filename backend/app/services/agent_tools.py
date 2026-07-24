from app.schemas.ai_chat import AiToolCallTrace


def build_tool_traces(
    *,
    recipe_source_count: int,
    preference_summary: str,
    has_image: bool,
) -> list[AiToolCallTrace]:
    traces = [
        AiToolCallTrace(
            tool_name="菜谱RAG工具",
            status="success",
            summary=f"已检索 {recipe_source_count} 条家庭菜品知识。",
        ),
        AiToolCallTrace(
            tool_name="家庭偏好工具",
            status="success",
            summary=preference_summary,
        ),
    ]
    if has_image:
        traces.append(
            AiToolCallTrace(
                tool_name="食材分析工具",
                status="success",
                summary="已结合冰箱图片参与本轮多模态分析。",
            )
        )
    return traces
