import json
import re
from pathlib import Path

_CONFIG_PATH = Path("config.jsonc")


def load_config(path: Path = _CONFIG_PATH) -> dict:
    text = path.read_text(encoding="utf-8")
    stripped = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
    return json.loads(stripped)
