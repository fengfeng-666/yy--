from typing import Literal

from pydantic import BaseModel, Field

NotificationEventType = Literal["new_order", "order_accepted"]


class GrantSubscriptionsRequest(BaseModel):
    event_types: list[NotificationEventType] = Field(min_length=1, max_length=2)


class SubscriptionProfile(BaseModel):
    event_type: NotificationEventType
    available_count: int
