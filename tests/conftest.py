import socket

import pytest
from rulereplay.config import Settings


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch):
    # Tests must never inherit real credentials or paid-operation approvals.
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)

    def no_network(*args, **kwargs):
        raise AssertionError("Tests must use a mock transport; outbound sockets are disabled.")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, data_dir=tmp_path / "reports")
