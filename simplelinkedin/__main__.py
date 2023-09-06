import argparse
import os

from simplelinkedin.linkedin import LinkedIn
from simplelinkedin.ln_settings import LinkedInCommandArgs, LinkedInSettingsName, get_linkedin_settings

parser = argparse.ArgumentParser()

parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_ENV_FILE,
    type=str,
    default=os.getenv(LinkedInSettingsName.LINKEDIN_ENV_FILE, None),
    help="Linkedin environment file",
)

parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_USER,
    type=str,
    default=os.getenv(LinkedInSettingsName.LINKEDIN_USER, None),
    help="Email of linkedin user",
)

parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_PASSWORD,
    type=str,
    default=os.getenv(LinkedInSettingsName.LINKEDIN_PASSWORD, None),
    help="Password of linkedin user",
)

parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_BROWSER,
    type=str,
    default=os.getenv(LinkedInSettingsName.LINKEDIN_BROWSER, "Chrome"),
    help="Browser used for linkedin",
)


parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_BROWSER_HEADLESS,
    action="store_true",
    help="Whether to run headless",
    default=os.getenv(LinkedInSettingsName.LINKEDIN_BROWSER_HEADLESS, False),
)


parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_PREFERRED_USER,
    type=str,
    default=os.getenv(LinkedInSettingsName.LINKEDIN_PREFERRED_USER, ""),
    help="Path to file containing preferred users characteristics",
)

parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_NOT_PREFERRED_USER,
    type=str,
    default=os.getenv(LinkedInSettingsName.LINKEDIN_NOT_PREFERRED_USER, ""),
    help="Path to file containing characteristics of not preferred users",
)


args = parser.parse_args()

settings = get_linkedin_settings(command_args=args)

if not settings.LINKEDIN_USER and not settings.LINKEDIN_PASSWORD:
    print("Please provide username and password")
    exit(1)

with LinkedIn(
    username=settings.LINKEDIN_USER,
    password=settings.LINKEDIN_PASSWORD,
    browser=settings.LINKEDIN_BROWSER,
    headless=bool(settings.LINKEDIN_BROWSER_HEADLESS),
) as ln:
    ln.smart_follow_unfollow(
        users_preferred=settings.LINKEDIN_PREFERRED_USER or [],
        users_not_preferred=settings.LINKEDIN_NOT_PREFERRED_USER or [],
    )
