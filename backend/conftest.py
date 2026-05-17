"""Глобальные фикстуры pytest."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def use_temp_media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
