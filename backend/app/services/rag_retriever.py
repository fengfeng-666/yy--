from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.ai_chat import AiRetrievalSource
from app.services.dish import list_dishes_for_family


def _build_dish_summary_text(dish) -> str:
    ingredient_text = "、".join(link.ingredient.name for link in dish.ingredients[:6] if link.ingredient)
    step_text = "；".join(step.content for step in dish.steps[:3])
    preference_text = "；".join(preference.preference_note for preference in dish.preferences[:2])
    fragments = [dish.name]
    if dish.description:
        fragments.append(dish.description)
    if ingredient_text:
        fragments.append(f"食材：{ingredient_text}")
    if step_text:
        fragments.append(f"做法：{step_text}")
    if preference_text:
        fragments.append(f"偏好：{preference_text}")
    return "；".join(fragments)


async def retrieve_recipe_sources(
    session: AsyncSession,
    *,
    family_id: int,
    query: str,
    limit: int = 4,
) -> list[AiRetrievalSource]:
    query_tokens = {token for token in query.lower().split() if token}
    dishes = await list_dishes_for_family(session, family_id=family_id)
    scored: list[tuple[float, object]] = []
    for dish in dishes:
        text = _build_dish_summary_text(dish).lower()
        score = 0.0
        for token in query_tokens:
            if token in text:
                score += 1.0
        if not query_tokens:
            score = 1.0
        if score > 0:
            scored.append((score, dish))

    scored.sort(key=lambda item: (item[0], item[1].updated_at.timestamp(), item[1].id), reverse=True)
    if not scored:
        scored = [(1.0, dish) for dish in dishes[:limit]]

    return [
        AiRetrievalSource(
            source_type="family_dish",
            source_id=str(dish.id),
            title=dish.name,
            snippet=_build_dish_summary_text(dish),
            score=score,
        )
        for score, dish in scored[:limit]
    ]
