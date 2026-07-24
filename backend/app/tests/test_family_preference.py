from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.dish import Dish
from app.models.family import Family
from app.models.family_member import FamilyMember, FamilyMemberRole
from app.models.ingredient import DishPreference
from app.models.order import MealOrder, MealOrderItem, MealOrderStatus
from app.models.user import User
from app.services.family_preference import build_family_preference_summary


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_build_family_preference_summary_handles_dish_preferences_with_history(
    db_session: AsyncSession,
) -> None:
    owner = User(username="owner_pref", nickname="Owner", password_hash="hashed")
    cook = User(username="cook_pref", nickname="Cook", password_hash="hashed")
    db_session.add_all([owner, cook])
    await db_session.flush()

    family = Family(name="偏好家庭", invite_code="PREF01", owner_id=owner.id, max_members=2)
    db_session.add(family)
    await db_session.flush()

    db_session.add_all(
        [
            FamilyMember(family_id=family.id, user_id=owner.id, role=FamilyMemberRole.OWNER),
            FamilyMember(family_id=family.id, user_id=cook.id, role=FamilyMemberRole.MEMBER),
        ]
    )

    dish = Dish(family_id=family.id, name="番茄炒蛋", description="家常菜", price=18, is_available=True)
    db_session.add(dish)
    await db_session.flush()

    db_session.add(
        DishPreference(
            dish_id=dish.id,
            user_id=owner.id,
            preference_note="少油更清爽",
        )
    )

    order = MealOrder(
        family_id=family.id,
        requester_id=owner.id,
        cook_id=cook.id,
        status=MealOrderStatus.ACCEPTED,
        planned_date=date.today(),
    )
    db_session.add(order)
    await db_session.flush()

    db_session.add(
        MealOrderItem(
            meal_order_id=order.id,
            dish_id=dish.id,
            quantity=1,
            sort_order=0,
        )
    )
    await db_session.commit()

    summary, notes = await build_family_preference_summary(db_session, family_id=family.id)

    assert "番茄炒蛋" in summary
    assert "少油更清爽" in summary
    assert notes == ["少油更清爽"]
