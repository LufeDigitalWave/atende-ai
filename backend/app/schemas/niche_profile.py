"""NicheProfile — bundles BusinessProfile (data) + ConversationProfile (behavior).

This is the artifact produced by the Factory and consumed by the agent loop.
It's versioned, validated, and safe to render into a system prompt.
"""
from __future__ import annotations

from app.schemas.business_profile import BusinessProfile
from app.schemas.conversation_profile import ConversationProfile


class NicheProfile:
    """Complete niche package: company data + conversation behavior."""

    def __init__(self, business: BusinessProfile, conversation: ConversationProfile):
        self.business = business
        self.conversation = conversation

    @property
    def niche_name(self) -> str:
        return self.business.company_name

    def to_dict(self) -> dict:
        return {
            "business": self.business.model_dump(),
            "conversation": self.conversation.model_dump(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> NicheProfile:
        return cls(
            business=BusinessProfile(**data["business"]),
            conversation=ConversationProfile(**data["conversation"]),
        )
