# https://github.com/pjialin/django-environ

import logging.config
from pathlib import Path

import environ
import yaml

BASE_DIR = Path(__file__).parent

LOG_CONF_FILE = "log_config/log_config.yaml"
ENV_FILE = "../.env"


# ========
# LOGGING
# ========

# Usage:
# from settings import get_logger
# logger = get_logger(__name__)
# logger.log("message")

with open(BASE_DIR / LOG_CONF_FILE) as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)


def getLogger(name):  # noqa
    return logging.getLogger(name)


get_logger = getLogger

# ===========================
# ENVIRONMENT VARIABLE UTILS
# ===========================

env = environ.Env()

env_file = BASE_DIR / Path(ENV_FILE)
env.read_env(env_file=env_file)

# ============================
# GLOBAL ENVIRONMENT VARIABLES
# ============================

# ENV_VAR = env("ENV_VAR")
