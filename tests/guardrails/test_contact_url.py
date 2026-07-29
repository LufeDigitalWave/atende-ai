"""Guardrail: real phone number must NOT appear in production bundle."""
import subprocess
import os

import pytest

REAL_PHONE = "5511913289497"
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
DIST_DIR = os.path.join(FRONTEND_DIR, "dist")


@pytest.fixture(scope="module")
def built_dist():
    """Ensure frontend is built for grep inspection."""
    if not os.path.isdir(DIST_DIR):
        pytest.skip("frontend/dist not built — run npm run build first")
    return DIST_DIR


def test_real_phone_not_in_bundle(built_dist):
    """Real phone number must not appear in any file under dist/."""
    for root, _, files in os.walk(built_dist):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                assert REAL_PHONE not in content, (
                    f"Real phone number found in {fpath}. "
                    "Use VITE_CONTACT_URL env var instead of hardcoding."
                )
            except (IOError, UnicodeDecodeError):
                continue
