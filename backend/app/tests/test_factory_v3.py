"""Tests for Factory v3 (BusinessProfile + ConversationProfile pipeline)."""
import pytest
from unittest.mock import patch, AsyncMock

from app.schemas.business_profile import BusinessProfile
from app.schemas.conversation_profile import (
    ConversationJourney,
    ConversationProfile,
    QualificationField,
)
from app.schemas.niche_profile import NicheProfile
from app.services.prompt_factory_v3 import (
    sanitize_niche,
    generate_niche_profile,
    get_cached_profile,
    clear_cache,
    FALLBACK_PROFILE,
)


class TestSanitization:
    def test_sanitize_normal(self):
        assert sanitize_niche("restaurante") == "restaurante"

    def test_sanitize_strips_newlines(self):
        assert "\n" not in sanitize_niche("restaurante\ne")
        assert "restaurante" in sanitize_niche("restaurante\ne")

    def test_sanitize_max_length(self):
        long = "a" * 100
        assert len(sanitize_niche(long)) == 60

    def test_sanitize_empty_to_fallback(self):
        assert sanitize_niche("") == "consultoria empresarial"


class TestFallbackProfile:
    def test_fallback_is_niche_profile(self):
        assert isinstance(FALLBACK_PROFILE, NicheProfile)

    def test_fallback_business_valid(self):
        assert isinstance(FALLBACK_PROFILE.business, BusinessProfile)
        assert FALLBACK_PROFILE.business.agent_name == "Sofia"

    def test_fallback_conversation_valid(self):
        assert isinstance(FALLBACK_PROFILE.conversation, ConversationProfile)
        assert FALLBACK_PROFILE.conversation.business_mode == "appointment_based"

    def test_fallback_has_journeys(self):
        assert len(FALLBACK_PROFILE.conversation.journeys) >= 1


class TestOfflineMode:
    @pytest.mark.asyncio
    @patch("app.services.prompt_factory_v3.get_settings")
    async def test_no_api_key_returns_fallback(self, mock_settings):
        mock_settings.return_value.llm_provider = "fake"
        mock_settings.return_value.openai_api_key = None

        clear_cache()
        result = await generate_niche_profile("restaurante")
        assert isinstance(result, NicheProfile)
        assert result.business.agent_name == "Sofia"


class TestCache:
    def test_clear_cache(self):
        clear_cache()  # should not raise

    @pytest.mark.asyncio
    @patch("app.services.prompt_factory_v3.get_settings")
    async def test_offline_mode_caches_fallback(self, mock_settings):
        mock_settings.return_value.llm_provider = "fake"
        mock_settings.return_value.openai_api_key = None

        clear_cache()
        result1 = await generate_niche_profile("barbearia")
        cached = get_cached_profile("barbearia")
        assert cached is not None
        assert cached.business.agent_name == result1.business.agent_name

    @pytest.mark.asyncio
    @patch("app.services.prompt_factory_v3.get_settings")
    async def test_different_niches_cached_separately(self, mock_settings):
        mock_settings.return_value.llm_provider = "fake"
        mock_settings.return_value.openai_api_key = None

        clear_cache()
        await generate_niche_profile("academia")
        await generate_niche_profile("pet shop")

        assert get_cached_profile("academia") is not None
        assert get_cached_profile("pet shop") is not None


class TestNicheProfile:
    def test_niche_profile_to_dict(self):
        d = FALLBACK_PROFILE.to_dict()
        assert "business" in d
        assert "conversation" in d
        assert d["business"]["agent_name"] == "Sofia"

    def test_niche_profile_from_dict(self):
        original = FALLBACK_PROFILE.to_dict()
        reconstructed = NicheProfile.from_dict(original)
        assert reconstructed.business.agent_name == FALLBACK_PROFILE.business.agent_name
        assert reconstructed.conversation.business_mode == FALLBACK_PROFILE.conversation.business_mode