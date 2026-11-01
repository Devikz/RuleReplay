import pytest
from fastapi.testclient import TestClient
from rulereplay.config import ConfigurationError, Settings, load_settings
from rulereplay.main import create_app


def test_health_without_credentials(settings):
    response = TestClient(create_app(settings)).get("/api/health")
    assert response.status_code == 200
    assert response.json()["integrations"]["meta"] == {"enabled": False, "configured": False}


def test_dotenv_and_environment_precedence(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("MODEL_API_KEY=synthetic-file-secret\nMETA_MODEL=muse-wonder-1.0\n")
    monkeypatch.chdir(tmp_path.parent)
    monkeypatch.setenv("MODEL_API_KEY", "synthetic-environment-secret")
    config = Settings(_env_file=env)
    assert config.model_api_key.get_secret_value() == "synthetic-environment-secret"
    assert "synthetic" not in repr(config)
    assert "synthetic" not in str(config.public_status())


@pytest.mark.parametrize("method", ["require_meta", "require_modal"])
def test_paid_operations_default_disabled(settings, method):
    with pytest.raises(ConfigurationError, match="disabled"):
        getattr(settings, method)()


def test_missing_credentials_is_actionable():
    with pytest.raises(ConfigurationError, match="MODEL_API_KEY"):
        load_settings(_env_file=None, allow_paid_model_requests=True)


def test_invalid_configuration_does_not_expose_input():
    with pytest.raises(ConfigurationError) as caught:
        load_settings(_env_file=None, model_api_base_url="https://synthetic-secret.example")
    assert "synthetic-secret" not in str(caught.value)
    assert "MODEL_API_BASE_URL" in str(caught.value)


def test_no_credential_fields_in_response():
    config = Settings(_env_file=None, model_api_key="synthetic-private-value")
    text = TestClient(create_app(config)).get("/api/health").text
    assert "synthetic-private-value" not in text
    assert "model_api_key" not in text
