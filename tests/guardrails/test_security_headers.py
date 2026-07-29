"""Guardrail: security headers must be present in production nginx response.

This test requires the production site to be reachable.
If not reachable, the test is skipped (not falsely passed).
"""
import subprocess
import pytest

PRODUCTION_URL = "https://atendeai.lufedigitalwave.com.br/"

EXPECTED_HEADERS = {
    "content-security-policy": "frame-ancestors",
    "strict-transport-security": "max-age=31536000",
    "x-content-type-options": "nosniff",
    "x-frame-options": "SAMEORIGIN",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "geolocation=()",
}


@pytest.fixture(scope="module")
def response_headers():
    """Fetch headers from production."""
    try:
        result = subprocess.run(
            ["curl", "-sI", PRODUCTION_URL, "--max-time", "10"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            pytest.skip(f"curl failed: {result.stderr}")
        return result.stdout.lower()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip("curl not available or production unreachable")


@pytest.mark.parametrize("header,expected_value", EXPECTED_HEADERS.items())
def test_security_header_present(response_headers, header, expected_value):
    """Each security header is present with expected value."""
    assert header in response_headers, f"Header '{header}' missing from production response"
    assert expected_value.lower() in response_headers, (
        f"Header '{header}' present but expected value '{expected_value}' not found"
    )
