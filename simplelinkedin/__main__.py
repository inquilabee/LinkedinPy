import argparse
import os

from simplelinkedin.crons.cron_jobs import LinkedInCron
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
    help="Email of LinkedIn user",
)

parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_PASSWORD,
    type=str,
    default=os.getenv(LinkedInSettingsName.LINKEDIN_PASSWORD, None),
    help="Password of LinkedIn user",
)

parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_BROWSER,
    type=str,
    default=os.getenv(LinkedInSettingsName.LINKEDIN_BROWSER, "Chrome"),
    help="Browser used for LinkedIn",
)


parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_BROWSER_HEADLESS,
    action="store_true",
    help="Whether to run headless (i.e. without the browser visible in the front.)",
    default=os.getenv(LinkedInSettingsName.LINKEDIN_BROWSER_HEADLESS, False),
)

parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_MAX_INVITE,
    type=int,
    default=os.getenv(LinkedInSettingsName.LINKEDIN_MAX_INVITE, 0),
    help="Maximum number of invitations to send",
)

parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_MIN_MUTUAL,
    type=int,
    default=os.getenv(LinkedInSettingsName.LINKEDIN_MIN_MUTUAL, 0),
    help="Minimum number of mutual connections required.",
)

parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_MAX_MUTUAL,
    type=int,
    default=os.getenv(LinkedInSettingsName.LINKEDIN_MAX_MUTUAL, 500),
    help="Maximum number of mutual connections required.",
)

parser.add_argument(
    LinkedInCommandArgs.LINKEDIN_WITHDRAW_INVITE_BEFORE_DAYS,
    type=int,
    default=os.getenv(LinkedInSettingsName.LINKEDIN_WITHDRAW_INVITE_BEFORE_DAYS, 14),
    help="Withdraw invites older than this many days",
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

parser.add_argument(
    "--cronfile",
    type=str,
    default=None,
    help="Path to cronfile",
)


parser.add_argument(
    "--cronuser",
    type=str,
    default=None,
    help="Name of user setting cron on the machine (needed by most OS)",
)

parser.add_argument(
    "--rmcron",
    type=bool,
    action=argparse.BooleanOptionalAction,
    help="Whether to remove existing crons.",
)

parser.add_argument(
    "--cronhour",
    type=int,
    default=None,
    help="hour of the day you want to set cron for each day.",
)


args = parser.parse_args()

if args.rmcron:
    if not args.cronuser:
        print("You must set cronuser to delete crons")
        exit(1)

    LinkedInCron.remove_cron_jobs(args.cronuser)
    exit(0)

if args.cronfile:
    if not args.cronuser or not args.cronhour:
        print("You must set cronuser and cronhour to set crons")
        exit(1)

    LinkedInCron.set_smart_cron(cron_env_file=args.cronfile, cron_user=args.cronuser, hour_of_day=args.cronhour)

    exit(0)

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
        min_mutual=settings.LINKEDIN_MIN_MUTUAL,
        max_mutual=settings.LINKEDIN_MAX_MUTUAL,
        users_preferred=settings.LINKEDIN_PREFERRED_USER,
        users_not_preferred=settings.LINKEDIN_NOT_PREFERRED_USER,
        max_invitations_to_send=settings.LINKEDIN_MAX_INVITE,
        withdraw_invite_older_than_days=settings.LINKEDIN_WITHDRAW_INVITE_BEFORE_DAYS,
        remove_recommendations=True,
    )

exit(0)
