from collections import OrderedDict

from app.schemas.ai_chat import AiActionDraft, AiActionDraftItem, AiRecommendationItem, AiToolCallTrace


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


def build_shopping_list_action_draft(
    recommendations: list[AiRecommendationItem],
) -> AiActionDraft | None:
    pending_items: "OrderedDict[str, AiActionDraftItem]" = OrderedDict()
    for recommendation in recommendations:
        missing = [
            ingredient
            for ingredient in recommendation.required_ingredients
            if ingredient and ingredient not in set(recommendation.matched_ingredients)
        ]
        for ingredient in missing:
            pending_items.setdefault(
                ingredient,
                AiActionDraftItem(
                    name=ingredient,
                    source_dish_name=recommendation.dish_name,
                    note="根据 AI 推荐结果估算的缺失食材",
                ),
            )

    if not pending_items:
        return None

    return AiActionDraft(
        action_type="shopping_list",
        title="生成购物清单",
        summary="这些食材可能还需要补齐，确认后会生成购物清单。",
        status="pending",
        items=list(pending_items.values()),
    )
