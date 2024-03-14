import json
import os
import sys
from pathlib import Path

import tomli

filepath = Path(__file__).parent


class Config:
    def __init__(self, config):
        for key, value in config.items():
            if isinstance(value, dict):
                setattr(self, key, Config(value))
            else:
                setattr(self, key, value)


with open(filepath.joinpath("model_config.toml"), mode="rb") as fp:
    MODEL_CONFIG = tomli.load(fp)

config = Config(MODEL_CONFIG)

# print(f"Model Config: \n{json.dumps(MODEL_CONFIG, indent=4)}")

if config.network.proxy.enable:
    os.environ["http_proxy"] = (
        config.network.proxy.http_proxy if config.network.proxy.http_proxy else config.network.proxy.default
    )
    os.environ["https_proxy"] = (
        config.network.proxy.https_proxy if config.network.proxy.https_proxy else config.network.proxy.default
    )
    print(f"Set http_proxy={os.environ['http_proxy']}, https_proxy={os.environ['https_proxy']}")
