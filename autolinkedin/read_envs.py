"""Read .env file"""
from pathlib import Path

from dotenv import load_dotenv


def read_environment_vars(filename: str | Path = ".env"):
    env_file_path = Path(filename).resolve()
    load_dotenv(env_file_path)
