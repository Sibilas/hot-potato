import os
import json
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Config:
    def __init__(self, amqp_url: str, http_port: int, sqlite_backup_path: str, log_level: str):
        self.AMQP_URL = amqp_url
        self.HTTP_PORT = http_port
        self.SQLITE_BACKUP_PATH = sqlite_backup_path
        self.LOG_LEVEL = log_level

    def __repr__(self):
        return (f"Config(AMQP_URL={self.AMQP_URL}, HTTP_PORT={self.HTTP_PORT}, "
                f"SQLITE_BACKUP_PATH={self.SQLITE_BACKUP_PATH}, LOG_LEVEL={self.LOG_LEVEL})")

def load_config() -> Config:
    """
    Loads configuration from environment variables and optionally from a config file.
    Priority: Environment Variable > Config File > Default.
    
    The config file must be a JSON file. Its path should be provided in the CONFIG_FILE env variable.
    """
    # Default configuration values.
    defaults = {
        "AMQP_URL": "amqp://sibilas:sibilasserver2024@sibimq:5672",
        "HTTP_PORT": "8080",
        "SQLITE_BACKUP_PATH": "hotpotato.sqlite",
        "LOG_LEVEL": "INFO"
    }

    # Load file-based configuration if CONFIG_FILE env variable is set.
    config_file = os.getenv("CONFIG_FILE")
    file_config = {}
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                file_config = json.load(f)
            logger.info("Loaded configuration from file: %s", config_file)
        except Exception as e:
            logger.error("Failed to load config file '%s': %s", config_file, e)
    else:
        if config_file:
            logger.warning("CONFIG_FILE '%s' not found. Using defaults.", config_file)

    # For each configuration key, check: env var > file config > default.
    amqp_url = os.getenv("AMQP_URL", file_config.get("AMQP_URL", defaults["AMQP_URL"]))
    http_port = int(os.getenv("HTTP_PORT", file_config.get("HTTP_PORT", defaults["HTTP_PORT"])))
    sqlite_backup_path = os.getenv("SQLITE_BACKUP_PATH", file_config.get("SQLITE_BACKUP_PATH", defaults["SQLITE_BACKUP_PATH"]))
    log_level = os.getenv("LOG_LEVEL", file_config.get("LOG_LEVEL", defaults["LOG_LEVEL"]))

    return Config(amqp_url, http_port, sqlite_backup_path, log_level)
