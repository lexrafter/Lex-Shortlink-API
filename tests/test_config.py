from lex_shortlink_api.config import Settings, get_settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert "postgresql://" in settings.database_url
    assert settings.redis_url.startswith("redis://")
    assert settings.app_env == "development"


def test_settings_from_env(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://custom:custom@db:5432/custom")
    monkeypatch.setenv("REDIS_URL", "redis://cache:6379/1")

    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.database_url == "postgresql://custom:custom@db:5432/custom"
        assert settings.redis_url == "redis://cache:6379/1"
    finally:
        get_settings.cache_clear()