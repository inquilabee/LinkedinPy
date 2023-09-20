import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass()
class LinkedInSettings:
    LINKEDIN_ENV_FILE: str = ""
    LINKEDIN_USER: str = ""
    LINKEDIN_PASSWORD: str = ""
    LINKEDIN_BROWSER: str = "Chrome"
    LINKEDIN_BROWSER_HEADLESS: bool = False
    LINKEDIN_PREFERRED_USER: str = None
    LINKEDIN_NOT_PREFERRED_USER: str = None

    LINKEDIN_MAX_INVITE: int = 0

    LINKEDIN_MIN_MUTUAL: int = 0
    LINKEDIN_MAX_MUTUAL: int = 500

    LINKEDIN_WITHDRAW_INVITE_BEFORE_DAYS: int = 14


class LinkedInSettingsName:
    LINKEDIN_ENV_FILE = "LINKEDIN_ENV_FILE"
    LINKEDIN_USER = "LINKEDIN_USER"
    LINKEDIN_PASSWORD = "LINKEDIN_PASSWORD"  # nosec
    LINKEDIN_BROWSER = "LINKEDIN_BROWSER"
    LINKEDIN_MIN_MUTUAL = "LINKEDIN_MIN_MUTUAL"
    LINKEDIN_MAX_MUTUAL = "LINKEDIN_MAX_MUTUAL"
    LINKEDIN_BROWSER_HEADLESS = "LINKEDIN_BROWSER_HEADLESS"
    LINKEDIN_PREFERRED_USER = "LINKEDIN_PREFERRED_USER"
    LINKEDIN_NOT_PREFERRED_USER = "LINKEDIN_NOT_PREFERRED_USER"

    LINKEDIN_MAX_INVITE = "LINKEDIN_MAX_INVITE"
    LINKEDIN_WITHDRAW_INVITE_BEFORE_DAYS = "LINKEDIN_WITHDRAW_INVITE_BEFORE_DAYS"


class LinkedInCommandArgs:
    LINKEDIN_ENV_FILE = "--env"
    LINKEDIN_USER = "--email"
    LINKEDIN_PASSWORD = "--password"  # nosec
    LINKEDIN_BROWSER = "--browser"
    LINKEDIN_BROWSER_HEADLESS = "--headless"
    LINKEDIN_PREFERRED_USER = "--preferred"
    LINKEDIN_NOT_PREFERRED_USER = "--notpreferred"

    LINKEDIN_MIN_MUTUAL = "--minmutual"
    LINKEDIN_MAX_MUTUAL = "--maxmutual"

    LINKEDIN_MAX_INVITE = "--maxinvite"

    LINKEDIN_WITHDRAW_INVITE_BEFORE_DAYS = "--withdrawdays"


class LinkedInUser:
    def __init__(self, username):
        self.username = username
        self.total_followers = 0
        self.mutual_connections = 0


class LinkedInSettingsException(Exception):
    pass


def get_linkedin_settings(command_args=None) -> LinkedInSettings:
    """Get all settings or variables set by the user"""

    if env_file := getattr(command_args, LinkedInCommandArgs.LINKEDIN_ENV_FILE.strip("--"), None):
        if not Path(env_file).exists():
            raise LinkedInSettingsException("Env file does not exist. Please pass a valid env file.")
        load_dotenv(env_file)

    settings = LinkedInSettings()

    for arg_name in dir(LinkedInCommandArgs):
        if arg_name.startswith("LINKEDIN"):
            value = os.getenv(arg_name, None) or getattr(
                command_args, getattr(LinkedInCommandArgs, arg_name).strip("--")
            )

            setattr(settings, arg_name, value)

    # TODO: Manual typecasting? too bad ';(

    settings.LINKEDIN_BROWSER_HEADLESS = int(settings.LINKEDIN_BROWSER_HEADLESS)
    settings.LINKEDIN_MAX_MUTUAL = int(settings.LINKEDIN_MAX_MUTUAL)
    settings.LINKEDIN_MIN_MUTUAL = int(settings.LINKEDIN_MIN_MUTUAL)
    settings.LINKEDIN_MAX_INVITE = int(settings.LINKEDIN_MAX_INVITE)
    settings.LINKEDIN_WITHDRAW_INVITE_BEFORE_DAYS = int(settings.LINKEDIN_WITHDRAW_INVITE_BEFORE_DAYS)

    settings.LINKEDIN_PREFERRED_USER = str(Path(settings.LINKEDIN_PREFERRED_USER).absolute())
    settings.LINKEDIN_NOT_PREFERRED_USER = str(Path(settings.LINKEDIN_NOT_PREFERRED_USER).absolute())

    return settings
