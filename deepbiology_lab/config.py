from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

DEFAULT_BASE_URL = "https://us-central1-deepbiology-471514.cloudfunctions.net"
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "deepbiology-lab"
CONFIG_PATH = CONFIG_DIR / "config.json"


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {"base_url": DEFAULT_BASE_URL}
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if "base_url" not in data:
        data["base_url"] = DEFAULT_BASE_URL
    return data


def save_config(api_key: str | None = None, base_url: str | None = None) -> Dict[str, Any]:
    config = load_config()
    if api_key is not None:
        config["api_key"] = api_key
    if base_url is not None:
        config["base_url"] = base_url.rstrip("/")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)
    return config
