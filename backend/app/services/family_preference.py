from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dish import list_dishes_for_family
from app.services.order import list_dining_history_for_family


async def build_family_preference_summary(
    session: AsyncSession,
    *,
    family_id: int,
) -> tuple[str, list[str]]:
    dishes = await list_dishes_for_family(session, family_id=family_id)

    # Read dish preference notes before loading dining history. In async sessions,
    # later queries that rehydrate the same Dish identities can leave this
    # relationship unloaded again and trigger MissingGreenlet on access.
    preference_notes = [
        preference.preference_note
        for dish in dishes
        for preference in dish.preferences
        if preference.preference_note
    ]

    history = await list_dining_history_for_family(session, family_id=family_id)
    recent_dish_names = [
        item.dish.name
        for order in history[:10]
        for item in order.items
        if item.dish and item.dish.name
    ]
    popular = [name for name, _ in Counter(recent_dish_names).most_common(3)]

    lines: list[str] = []
    if popular:
        lines.append(f"最近更常吃：{'、'.join(popular)}")
    if preference_notes:
        lines.append(f"家庭已记录偏好：{'；'.join(preference_notes[:5])}")
    summary = "；".join(lines) if lines else "当前家庭还没有足够的历史偏好数据。"
    return summary, preference_notes[:5]
