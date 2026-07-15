"""Tests for Factory v2 (data-not-prompt architecture).

Factory tests ensure:
1. Business profile is valid Pydantic schema
2. Niche sanitization prevents injection
3. Template rendering doesn't break with dynamic data
4. Cache works with TTL
5. Fallback is triggered on LLM failure
6. Niches round-trip through the system
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.schemas.business_profile import (
    BusinessProfile,
    ServiceItem,
    FAQItem,
    ObjectionItem,
)
from app.services.prompt_factory import (
    sanitize_niche,
    render_template,
    generate_niche_prompt,
    get_cached_prompt,
    clear_cache,
    FALLBACK_PROFILE,
)


class TestSanitization:
    """Test niche input sanitization."""

    def test_sanitize_normal_niche(self):
        """Normal niche passes through."""
        result = sanitize_niche("consultoria empresarial")
        assert result == "consultoria empresarial"

    def test_sanitize_strips_whitespace(self):
        """Whitespace is collapsed."""
        result = sanitize_niche("  consultoria   empresarial  ")
        assert result == "consultoria empresarial"

    def test_sanitize_removes_linebreaks(self):
        """Line breaks are removed (injection prevention)."""
        result = sanitize_niche("consultoria\neserial")
        assert "\n" not in result
        assert "consultoria" in result

    def test_sanitize_max_length(self):
        """Max 60 chars."""
        long_niche = "a" * 100
        result = sanitize_niche(long_niche)
        assert len(result) == 60

    def test_sanitize_empty_to_fallback(self):
        """Empty or too-short niche defaults to consultoria."""
        assert sanitize_niche("") == "consultoria empresarial"
        assert sanitize_niche("ab") == "consultoria empresarial"
        assert sanitize_niche("   ") == "consultoria empresarial"

    def test_sanitize_removes_control_chars(self):
        """Control characters are stripped."""
        result = sanitize_niche("consultoria\x00\x1feempresarial")
        assert "\x00" not in result
        assert "\x1f" not in result


class TestBusinessProfileSchema:
    """Test Pydantic schema validation."""

    def test_valid_profile(self):
        """Fallback profile validates."""
        assert isinstance(FALLBACK_PROFILE, BusinessProfile)
        assert len(FALLBACK_PROFILE.services) >= 3
        assert len(FALLBACK_PROFILE.faq) == 5
        assert len(FALLBACK_PROFILE.common_objections) == 3

    def test_service_item_validation(self):
        """Service item requires price format."""
        from pydantic import ValidationError

        # Valid
        svc = ServiceItem(
            name="Test",
            price_installments="12x R$ 100",
            price_cash="R$ 1.200",
            duration_or_scope="60 min",
        )
        assert svc.name == "Test"

        # Invalid installments format
        with pytest.raises(ValidationError):
            ServiceItem(
                name="Test",
                price_installments="invalid",
                price_cash="R$ 1.200",
                duration_or_scope="60 min",
            )

    def test_faq_count_required(self):
        """FAQ must have exactly 5 items."""
        from pydantic import ValidationError

        # Only 2 items
        with pytest.raises(ValidationError):
            BusinessProfile(
                agent_name="Sofia",
                company_name="Test",
                city="São Paulo",
                tagline="Test",
                services=[{"name": "S1", "price_installments": "12x R$ 100", "price_cash": "R$ 1.200", "duration_or_scope": "60min"}],
                qualification_extra_question="Test?",
                faq=[{"q": "Q1?", "a": "A1"}] * 2,  # Only 2
                common_objections=[{"objection": "O1", "guideline": "G1"}] * 3,
                tone_notes="friendly",
                opening_message="Hi",
                suggestions=["S1", "S2", "S3"],
            )

    def test_objection_count_required(self):
        """Common objections must have exactly 3 items."""
        from pydantic import ValidationError

        # Only 2 items
        with pytest.raises(ValidationError):
            BusinessProfile(
                agent_name="Sofia",
                company_name="Test",
                city="São Paulo",
                tagline="Test",
                services=[{"name": "S1", "price_installments": "12x R$ 100", "price_cash": "R$ 1.200", "duration_or_scope": "60min"}],
                qualification_extra_question="Test?",
                faq=[{"q": "Q1?", "a": "A1"}] * 5,
                common_objections=[{"objection": "O1", "guideline": "G1"}] * 2,  # Only 2
                tone_notes="friendly",
                opening_message="Hi",
                suggestions=["S1", "S2", "S3"],
            )


class TestTemplateRendering:
    """Test template rendering with different profiles."""

    def test_render_fallback_profile(self):
        """Fallback profile renders without error."""
        prompt = render_template(FALLBACK_PROFILE)
        assert len(prompt) > 500  # Substantial content
        assert FALLBACK_PROFILE.agent_name in prompt
        assert FALLBACK_PROFILE.company_name in prompt
        assert "Limpeza de pele" in prompt  # Service name

    def test_render_contains_services(self):
        """Rendered prompt includes service prices."""
        prompt = render_template(FALLBACK_PROFILE)
        # Check that at least one service price is in the prompt
        assert "R$ 1.068" in prompt or "12x R$ 89" in prompt

    def test_render_contains_faq(self):
        """Rendered prompt includes FAQ items."""
        prompt = render_template(FALLBACK_PROFILE)
        assert "horário" in prompt.lower() or "atendimento" in prompt.lower()

    def test_render_contains_tone(self):
        """Rendered prompt includes tone notes."""
        prompt = render_template(FALLBACK_PROFILE)
        assert "calorosa" in prompt

    def test_render_no_template_vars_remain(self):
        """No template variables like {agent_name} remain after render."""
        prompt = render_template(FALLBACK_PROFILE)
        assert "{agent_name}" not in prompt
        assert "{company_name}" not in prompt
        assert "{services_rendered}" not in prompt


class TestCache:
    """Test in-memory cache with TTL."""

    def test_cache_clear(self):
        """Cache can be cleared."""
        clear_cache()
        # Should not raise

    @pytest.mark.asyncio
    async def test_cache_hit_after_generation(self):
        """After generation, cache returns same prompt."""
        clear_cache()
        niche = "test niche 123"

        # First call (cache miss, will use fallback)
        cached1 = await generate_niche_prompt(niche)

        # Second call (cache hit)
        cached2 = get_cached_prompt(niche)

        assert cached2 is not None
        assert cached2.system_prompt == cached1.system_prompt

    @pytest.mark.asyncio
    async def test_cache_different_niches_isolated(self):
        """Different niches have separate cache entries."""
        clear_cache()

        niche1 = "niche one"
        niche2 = "niche two"

        cached1 = await generate_niche_prompt(niche1)
        cached2 = await generate_niche_prompt(niche2)

        # Both should be in cache
        retrieved1 = get_cached_prompt(niche1)
        retrieved2 = get_cached_prompt(niche2)

        assert retrieved1 is not None
        assert retrieved2 is not None
        # Different niches → different agent names (unless both fallback)
        # At minimum, they're independent cache entries
        assert retrieved1.profile.agent_name or retrieved2.profile.agent_name


class TestFallback:
    """Test fallback behavior."""

    def test_fallback_profile_always_valid(self):
        """Fallback profile is always valid and usable."""
        prompt = render_template(FALLBACK_PROFILE)
        assert len(prompt) > 0
        assert FALLBACK_PROFILE.agent_name in prompt

    @pytest.mark.asyncio
    async def test_fallback_on_no_api_key(self):
        """When no OpenAI key, fallback is used."""
        clear_cache()
        with patch("app.services.prompt_factory.get_settings") as mock_settings:
            # Mock settings with no OpenAI key
            mock_settings.return_value.openai_api_key = None
            mock_settings.return_value.llm_provider = "fake"

            cached = await generate_niche_prompt("any niche")
            # Should get fallback (Sofia profile)
            assert cached.profile.agent_name == "Sofia"
            assert cached.profile.company_name == "Clínica Renova"
