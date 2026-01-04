import json
from pathlib import Path
from typing import Any, Dict

_config: Dict[str, Any] = {}

def load_config(path: str = None) -> Dict[str, Any]:
	global _config
	if _config:
		return _config
	# default file alongside project
	base = Path(__file__).parent.parent
	cfg_path = Path(path) if path else base / "enterprise_config.json"
	if cfg_path.exists():
		try:
			with open(cfg_path, "r", encoding="utf-8") as f:
				_config = json.load(f)
		except Exception:
			_config = {}
	else:
		_config = {}
	return _config

def get_config() -> Dict[str, Any]:
	return load_config()
