import json
import os


def get_config():
    config_file = os.path.expanduser("~/.config/micnet/config.json")
    try:
        if os.path.exists(config_file):
            with open(config_file) as f:
                return json.load(f)
    except Exception:
        pass
    return {"apikeys": {}}


def get_api_key(service):
    config = get_config()
    return config.get("apikeys", {}).get(service, "")
