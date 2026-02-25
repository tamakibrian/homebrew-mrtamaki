"""Pytest fixtures for mrtamaki tests."""
import os

import pytest


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Clear credential env vars to avoid accidental API calls."""
    for key in ("IPROYAL_USER", "IPROYAL_PASS", "OXYLABS_USER", "OXYLABS_PASS",
                "SCAMALYTICS_API_KEY", "ONELOOKUP_API_KEY"):
        monkeypatch.delenv(key, raising=False)
