"""Loopback-only disposable offline API for browser tests; never loads dotenv."""

from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from rulereplay.config import Settings
from rulereplay.main import create_app

if __name__ == "__main__":
    with TemporaryDirectory(prefix="rulereplay-e2e-") as directory:
        settings = Settings(
            _env_file=None,
            data_dir=Path(directory),
            allow_paid_model_requests=False,
            allow_billable_modal=False,
            model_api_key="",
            modal_token_id="",
            modal_token_secret="",
        )
        uvicorn.run(create_app(settings), host="127.0.0.1", port=8011)
