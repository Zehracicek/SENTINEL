"""auth.py testleri — yazma uçlarını koruyan paylaşımlı token.

Üç davranış kritik: token tanımlı değilse uç kapalı olmalı (açık değil),
yanlış token reddedilmeli, doğru token geçmeli.
"""

import pytest
from fastapi import HTTPException

from auth import require_api_token


def test_missing_env_var_closes_the_endpoint(monkeypatch):
    """Token yapılandırılmadıysa uç 503 vermeli — kimlik doğrulamasız açılmamalı."""
    monkeypatch.delenv("SENTINEL_API_TOKEN", raising=False)

    with pytest.raises(HTTPException) as exc:
        require_api_token(x_api_token="herhangi-bir-sey")

    assert exc.value.status_code == 503


def test_wrong_token_is_rejected(monkeypatch):
    monkeypatch.setenv("SENTINEL_API_TOKEN", "dogru-token")

    with pytest.raises(HTTPException) as exc:
        require_api_token(x_api_token="yanlis-token")

    assert exc.value.status_code == 401


def test_absent_header_is_rejected(monkeypatch):
    """FastAPI başlık yoksa boş dize geçirir."""
    monkeypatch.setenv("SENTINEL_API_TOKEN", "dogru-token")

    with pytest.raises(HTTPException) as exc:
        require_api_token(x_api_token="")

    assert exc.value.status_code == 401


def test_whitespace_only_token_is_rejected(monkeypatch):
    monkeypatch.setenv("SENTINEL_API_TOKEN", "dogru-token")

    with pytest.raises(HTTPException) as exc:
        require_api_token(x_api_token="   ")

    assert exc.value.status_code == 401


def test_correct_token_passes(monkeypatch):
    monkeypatch.setenv("SENTINEL_API_TOKEN", "dogru-token")

    require_api_token(x_api_token="dogru-token")  # exception atmamalı
