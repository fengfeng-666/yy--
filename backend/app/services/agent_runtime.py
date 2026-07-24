import json
from collections.abc import Sequence
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_chat import AiChatMessage
from app.models.dish import Dish
from app.schemas.agent import AgentResult
from app.services.agent_tools import build_shopping_list_action_draft, build_tool_traces
from app.services.ai_provider import SummaryDeltaHandler, generate_ai_recommendation
from app.services.family_preference import build_family_preference_summary
from app.services.rag_retriever import retrieve_recipe_sources


class DishKnowledgeSnapshot(TypedDict):
    dish_id: int
    name: str
    description: str
    cooking_minutes: int | None
    difficulty: int | None
    spicy_level: int | None
    is_available: bool
    ingredients: list[str]
    steps: list[str]
    preferences: list[str]


def snapshot_dish_knowledge(dishes: Sequence[Dish]) -> list[DishKnowledgeSnapshot]:
    snapshots: list[DishKnowledgeSnapshot] = []
    for dish in dishes:
        snapshots.append(
            {
                "dish_id": dish.id,
                "name": dish.name,
                "description": dish.description or "",
                "cooking_minutes": dish.cooking_minutes,
                "difficulty": dish.difficulty,
                "spicy_level": dish.spicy_level,
                "is_available": dish.is_available,
                "ingredients": [
                    link.ingredient.name for link in dish.ingredients if link.ingredient
                ],
                "steps": [step.content for step in dish.steps],
                "preferences": [
                    item.preference_note for item in dish.preferences if item.preference_note
                ],
            }
        )
    return snapshots


def build_agent_system_prompt(
    *,
    dishes: Sequence[DishKnowledgeSnapshot],
    recipe_sources: list[dict[str, object]],
    preference_summary: str,
) -> str:
    candidate_dishes = [
        {
            "dish_id": dish["dish_id"],
            "name": dish["name"],
            "description": dish["description"],
            "cooking_minutes": dish["cooking_minutes"],
            "difficulty": dish["difficulty"],
            "spicy_level": dish["spicy_level"],
            "is_available": dish["is_available"],
            "ingredients": dish["ingredients"],
            "steps": dish["steps"],
            "preferences": dish["preferences"],
        }
        for dish in dishes
        if dish["is_available"]
    ]
    return (
        "你是 YY私厨 v2.0 的 AI 智能厨房助手。"
        "请优先基于给定的家庭菜品知识、家庭偏好和用户输入推荐适合做的菜。"
        "如果用户上传了图片，请把图片当作冰箱食材线索参与判断。"
        "输出必须是 JSON 对象，不要输出 markdown。"
        'JSON 结构固定为 {"summary": string, "recognized_ingredients": string[], '
        '"recommendations": '
        '[{"dish_name": string, "rating": 1-5, "required_ingredients": string[], '
        '"matched_ingredients": string[], "steps": string[], "reason": string}]}.'
        "如果没有上传图片，recognized_ingredients 必须返回空数组。"
        "推荐时优先命中家庭已有菜品；如果需要参考常见做法，可以补全食材与步骤，但要明确理由。"
        f"家庭偏好摘要：{preference_summary}。"
        f"检索到的家庭菜品知识：{json.dumps(recipe_sources, ensure_ascii=False)}。"
        f"当前家庭菜品全量知识：{json.dumps(candidate_dishes, ensure_ascii=False)}。"
    )


def build_history_messages(messages: Sequence[AiChatMessage]) -> list[dict[str, object]]:
    return [
        {
            "role": message.role,
            "content": [{"type": "text", "text": message.content}],
        }
        for message in messages
    ]


async def execute_agent_turn(
    session: AsyncSession,
    *,
    family_id: int,
    user_content: str,
    image_data_url: str | None,
    recent_messages: Sequence[AiChatMessage],
    dishes: Sequence[Dish],
    on_summary_delta: SummaryDeltaHandler | None = None,
) -> AgentResult:
    # Snapshot relationship-backed dish knowledge before later awaits. In async sessions,
    # subsequent queries can rehydrate the same ORM identities and leave lazy attributes
    # unavailable again, which leads to MissingGreenlet when accessed here.
    dish_knowledge = snapshot_dish_knowledge(dishes)
    retrieval_sources = await retrieve_recipe_sources(
        session,
        family_id=family_id,
        query=user_content,
    )
    preference_summary, _ = await build_family_preference_summary(session, family_id=family_id)
    parsed = await generate_ai_recommendation(
        system_prompt=build_agent_system_prompt(
            dishes=dish_knowledge,
            recipe_sources=[item.model_dump() for item in retrieval_sources],
            preference_summary=preference_summary,
        ),
        history_messages=build_history_messages(recent_messages),
        user_content=user_content,
        image_data_url=image_data_url,
        on_summary_delta=on_summary_delta,
    )
    action_draft = build_shopping_list_action_draft(parsed.recommendations)
    return AgentResult(
        summary=parsed.summary,
        recommendations=parsed.recommendations,
        recognized_ingredients=parsed.recognized_ingredients,
        retrieval_sources=retrieval_sources,
        tool_calls=build_tool_traces(
            recipe_source_count=len(retrieval_sources),
            preference_summary=preference_summary,
            has_image=image_data_url is not None,
        ),
        action_draft=action_draft,
        confidence=0.9 if retrieval_sources else 0.7,
        raw_model_output=parsed.raw_model_output,
    )
