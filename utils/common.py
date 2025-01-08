import json
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path("config.json")

def load_config():

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {"shops": []}

def save_config(config):

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)
