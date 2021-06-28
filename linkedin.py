import argparse
import logging
import os
import string
import subprocess
import time
from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass
from functools import wraps
from pathlib import Path

from crontab import CronTab
from dotenv import load_dotenv
from selenium.webdriver.common.by import By

from selenium_requests import Browser


def ignore_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:  # noqa
            pass

    return wrapper


class LinkedInUser:
    def __init__(self, username):
        self.username = username
        self.total_followers = 0
        self.mutual_connections = 0


@dataclass()
class LinkedInSettings:
    LINKEDIN_ENV_FILE: str = ""
    LINKEDIN_USER: str = ""
    LINKEDIN_PASSWORD: str = ""
    LINKEDIN_BROWSER: str = ""
    LINKEDIN_BROWSER_DRIVER: str = ""
    LINKEDIN_BROWSER_HEADLESS: bool = False
    LINKEDIN_BROWSER_CRON: int = 0
    LINKEDIN_CRON_USER: str = ""
    LINKEDIN_PREFERRED_USER: str = ""
    LINKEDIN_NOT_PREFERRED_USER: str = ""


class LinkedInSettingsName:
    LINKEDIN_ENV_FILE = "LINKEDIN_ENV_FILE"
    LINKEDIN_USER = "LINKEDIN_USER"
    LINKEDIN_PASSWORD = "LINKEDIN_PASSWORD"
    LINKEDIN_BROWSER = "LINKEDIN_BROWSER"
    LINKEDIN_BROWSER_DRIVER = "LINKEDIN_BROWSER_DRIVER"
    LINKEDIN_BROWSER_HEADLESS = "LINKEDIN_BROWSER_HEADLESS"
    LINKEDIN_BROWSER_CRON = "LINKEDIN_BROWSER_CRON"
    LINKEDIN_CRON_USER = "LINKEDIN_CRON_USER"
    LINKEDIN_PREFERRED_USER = "LINKEDIN_PREFERRED_USER"
    LINKEDIN_NOT_PREFERRED_USER = "LINKEDIN_NOT_PREFERRED_USER"


class LinkedInCommandArgs:
    LINKEDIN_ENV_FILE = "--env"
    LINKEDIN_USER = "--email"
    LINKEDIN_PASSWORD = "--password"
    LINKEDIN_BROWSER = "--browser"
    LINKEDIN_BROWSER_DRIVER = "--driver"
    LINKEDIN_BROWSER_HEADLESS = "--headless"
    LINKEDIN_BROWSER_CRON = "--cron"
    LINKEDIN_CRON_USER = "--cronuser"
    LINKEDIN_PREFERRED_USER = "--preferred"
    LINKEDIN_NOT_PREFERRED_USER = "--notpreferred"


class AbstractBaseLinkedin(ABC):
    HOME_PAGE: str
    LOGIN_PAGE: str
    NETWORK_HOME_PAGE: str
    NETWORK_RECEIVED_INVITATIONS_PAGE: str
    NETWORK_SENT_INVITATIONS_PAGE: str

    WEEKLY_MAX_INVITATION: int = 100

    CRON_JOB_COMMENT = "LinkedInJob"

    def __init__(self, username, password, browser, driver_path, headless):
        self.username = username
        self.password = password
        self.browser_name = browser
        self._user_logged_in: bool = False
        self.browser = Browser(name=browser, implicit_wait=10, driver_path=driver_path, headless=headless)
        self.logger = logging.getLogger("LinkedIn")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.close()

    @property
    def tabs(self):
        return self.browser.tabs

    @abstractproperty
    def invitations_sent_last_week(self) -> int:
        pass

    @abstractmethod
    def login(self) -> bool:
        """Should try to log in the user with given credentials.

        returns a bool based on whether the login attempt was successful or not.
        """
        pass

    @abstractmethod
    def send_invitations(
        self,
        max_invitation=20,
        min_mutual=0,
        max_mutual=500,
        view_profile=True,
        preferred_users: list = None,
        not_preferred_users: list = None,
    ):
        pass

    @abstractmethod
    def accept_invitations(self):
        pass

    @abstractmethod
    def remove_sent_invitations(self, older_tha_days=14, max_remove=20):
        pass

    @abstractmethod
    def view_profile(self, username):
        pass

    @abstractmethod
    def smart_follow_unfollow(self):
        pass

    @abstractmethod
    def set_smart_cron(self, passed_arguments):
        pass

    @abstractmethod
    def remove_cron_jobs(self):
        pass


class LinkedIn(AbstractBaseLinkedin):
    HOME_PAGE = "https://www.linkedin.com/feed/"
    LOGIN_PAGE = "https://www.linkedin.com/login"
    NETWORK_HOME_PAGE = "https://www.linkedin.com/mynetwork/"
    NETWORK_RECEIVED_INVITATIONS_PAGE = "https://www.linkedin.com/mynetwork/invitation-manager/"
    NETWORK_SENT_INVITATIONS_PAGE = "https://www.linkedin.com/mynetwork/invitation-manager/sent/"
    USER_PROFILE_PAGE = "https://www.linkedin.com/in/{username}/"

    def __init__(self, username, password, driver_path, browser="Chrome", headless=False):
        super().__init__(
            username=username, password=password, browser=browser, driver_path=driver_path, headless=headless
        )

    @staticmethod
    def invitation_sent_days_ago(invitation):
        mutual_connection_button_class_name = "time-badge"

        sent_ago = invitation.find_element(by=By.CLASS_NAME, value=mutual_connection_button_class_name).text
        num, unit, _ = sent_ago.split()

        num = int(num)

        if "second" in unit or "minute" in unit or "hour" in unit:
            return 0
        if "day" in unit:
            return num
        elif "week" in unit:
            return 7 * num
        elif "month" in unit:
            return 30 * num
        elif "year" in unit:
            return 365 * num

        return 0

    def match(self, user_card, preferences: list):
        """A simple substring search to match

        TODO: Improve matching algorithm
        """

        try:
            for pref in preferences:
                if user_card.text and (pref in user_card.text or user_card.text in pref):
                    return True
        except:  # noqa
            pass

        return False

    def login(self):
        if not self._user_logged_in:

            login_tab = self.browser.open(self.LOGIN_PAGE)

            try:
                username_input = login_tab.wait_for_presence_and_visibility(by=By.ID, key="username", wait=10)
                password_input = login_tab.wait_for_presence_and_visibility(by=By.ID, key="password", wait=10)
                submit_button = login_tab.wait_for_presence_and_visibility(
                    by=By.CLASS_NAME, key="btn__primary--large", wait=10
                )

                username_input.send_keys(self.username)
                password_input.send_keys(self.password)

                login_tab.click(submit_button)

            except Exception as e:  # noqa
                self.logger.info(f"{self.username} Login Attempt Failed")
            else:
                self._user_logged_in = True
                self.logger.info(f"{self.username} Login Attempt successful")
        else:
            self.logger.info("User already logged in.")

        return self._user_logged_in

    def send_invitations(
        self,
        max_invitation=20,
        min_mutual=0,
        max_mutual=500,
        view_profile=True,
        preferred_users: list = None,
        not_preferred_users: list = None,
    ):
        user_connect_button_text = "Connect"
        user_connection_card_class_name = "discover-entity-card"
        user_card_mutual_connection_class_name = "member-insights"
        scroll_times_on_recommendation_page = 20

        def mutual_connections(user_card):
            try:
                user_insights = user_card.find_element(by=By.CLASS_NAME, value=user_card_mutual_connection_class_name)

                mutual_connection = int(
                    "".join([character for character in user_insights.text if character in string.digits]) or "0"
                )
                return mutual_connection
            except:  # noqa
                return -1

        networking_home_tab = self.browser.open(self.NETWORK_HOME_PAGE)

        networking_home_tab.scroll(times=scroll_times_on_recommendation_page)

        all_cards = networking_home_tab.find_element(
            by=By.CLASS_NAME, value=user_connection_card_class_name, multiple=True
        )

        all_cards = [
            card
            for card in all_cards
            if user_connect_button_text in card.text and min_mutual < mutual_connections(card) < max_mutual
        ]

        # all_cards = random.sample(all_cards, min(max_invitation, len(all_cards)))

        invitations = 0

        # print("Possible requests ", len(all_cards))

        for user_card in all_cards:

            if preferred_users and not self.match(user_card, preferred_users):
                # print("""User does not match or fulfil specified criteria""", user_card.text, preferred_users)
                continue

            if not_preferred_users and self.match(user_card, not_preferred_users):
                # print("""User matched with not preferred criteria""", user_card.text, not_preferred_users)
                continue

            if view_profile:
                link = user_card.find_element_by_tag_name("a")
                user_profile_link = link.get_attribute("href")
                self.browser.open(user_profile_link)  # user_profile_tab
                networking_home_tab.switch()

            connect_button = user_card.find_element(by=By.XPATH, value=f".//*[text()='{user_connect_button_text}']")
            networking_home_tab.click(connect_button)
            invitations = invitations + 1

            # print(f"Sent invitation to {user_card.text}")

            if invitations > max_invitation:
                break

    def accept_invitations(self):
        user_accept_button_class_name = "invite-accept-btn"

        invitation_request_tab = self.browser.open(self.NETWORK_RECEIVED_INVITATIONS_PAGE)

        invitation_buttons = invitation_request_tab.find_element(
            by=By.CLASS_NAME, value=user_accept_button_class_name, multiple=True
        )

        for invitation_button in invitation_buttons:
            invitation_request_tab.click(invitation_button)

    def remove_sent_invitations(self, older_than_days=10, max_remove=20):

        withdraw_invitation_button_text = "Withdraw"
        withdraw_invitation_button_modal_text = "Withdraw invitation"
        withdraw_invitation_button_modal_confirm_text = "Withdraw"
        withdraw_invitation_button_modal_cancel_text = "Cancel"

        sent_invitation_class_name = "invitation-card"

        sent_invitation_tab = self.browser.open(self.NETWORK_SENT_INVITATIONS_PAGE)

        sent_invitation_tab.infinite_scroll()

        all_sent_invitations = sent_invitation_tab.find_element(
            by=By.CLASS_NAME, value=sent_invitation_class_name, multiple=True
        )

        number_of_removed_invitation = 0

        while all_sent_invitations and number_of_removed_invitation < max_remove:
            sent_invitation = all_sent_invitations.pop()

            if self.invitation_sent_days_ago(invitation=sent_invitation) >= older_than_days:
                withdraw_btn = sent_invitation.find_element(
                    by=By.XPATH, value=f".//*[text()='{withdraw_invitation_button_text}']"
                )
                sent_invitation_tab.click(withdraw_btn)

                confirm_withdrawal_pop_up = sent_invitation_tab.find_element(
                    by=By.XPATH, value=f"//*[text()='{withdraw_invitation_button_modal_text}']"
                )

                while withdraw_invitation_button_modal_cancel_text not in confirm_withdrawal_pop_up.text:
                    confirm_withdrawal_pop_up = confirm_withdrawal_pop_up.find_element(by=By.XPATH, value="..")

                withdrawal_confirm_modal_button = confirm_withdrawal_pop_up.find_element(
                    by=By.XPATH, value=f".//*[text()='{withdraw_invitation_button_modal_confirm_text}']"
                )

                sent_invitation_tab.click(withdrawal_confirm_modal_button)

                sent_invitation_tab.wait_until_staleness(withdrawal_confirm_modal_button)
                sent_invitation_tab.wait_until_staleness(confirm_withdrawal_pop_up)
                sent_invitation_tab.wait_until_staleness(withdraw_btn)

                number_of_removed_invitation = number_of_removed_invitation + 1

    @property
    def invitations_sent_last_week(self) -> int:
        sent_invitation_class_name = "invitation-card"

        sent_invitation_tab = self.browser.open(self.NETWORK_SENT_INVITATIONS_PAGE)

        sent_invitation_tab.infinite_scroll()

        all_sent_invitations = sent_invitation_tab.find_element(
            by=By.CLASS_NAME, value=sent_invitation_class_name, multiple=True
        )

        return sum([self.invitation_sent_days_ago(invitation) <= 7 for invitation in all_sent_invitations])

    def view_profile(self, username, wait=5):
        user_profile_link = self.USER_PROFILE_PAGE.format(username=username)
        user_profile_tab = self.browser.open(user_profile_link)
        time.sleep(wait)
        self.browser.close_tab(user_profile_tab)

    def smart_follow_unfollow(self, users_preferred=None, users_not_preferred=None):

        if users_preferred and not isinstance(users_preferred, list) and Path(users_preferred).exists():
            with open(users_preferred) as f:
                users_preferred = f.readlines()

        if users_not_preferred and not isinstance(users_not_preferred, list) and Path(users_not_preferred).exists():
            with open(users_not_preferred) as f:
                users_not_preferred = f.readlines()

        users_preferred = [line.strip() for line in users_preferred if line.strip()]
        users_not_preferred = [line.strip() for line in users_not_preferred if line.strip()]

        self.login()
        self.remove_sent_invitations(older_than_days=14)
        self.send_invitations(
            max_invitation=max(self.WEEKLY_MAX_INVITATION - self.invitations_sent_last_week, 0),
            min_mutual=100,
            max_mutual=400,
            preferred_users=users_preferred,
            not_preferred_users=users_not_preferred,
            view_profile=True,
        )

        self.accept_invitations()

    def set_smart_cron(self, settings: LinkedInSettings):

        python_path = [
            path.strip()
            for path in subprocess.run("which python", shell=True, capture_output=True).stdout.decode().split("\n")
        ][0]

        current_file_path = os.path.abspath(__file__)

        command = (
            f"{python_path or 'python'} "
            f"{current_file_path} "
            f"--email {settings.LINKEDIN_USER} "
            f"--password {settings.LINKEDIN_PASSWORD} "
            f"--browser {settings.LINKEDIN_BROWSER} "
            f"--driver {settings.LINKEDIN_BROWSER_DRIVER} "
            f"--headless "
            f"--cronuser {settings.LINKEDIN_CRON_USER} "
            f"{'--preferred' if settings.LINKEDIN_PREFERRED_USER else ''} "
            f"{settings.LINKEDIN_PREFERRED_USER or ''} "
            f"{'--notpreferred' if settings.LINKEDIN_NOT_PREFERRED_USER else ''} "
            f"{settings.LINKEDIN_NOT_PREFERRED_USER or ''} "
        )

        cron = CronTab(user=settings.LINKEDIN_CRON_USER)

        even_day_job = cron.new(command=command, comment=self.CRON_JOB_COMMENT)
        even_day_job.hour.on(21)
        even_day_job.dow.on(0, 2, 4, 6)

        odd_day_job = cron.new(command=command, comment=self.CRON_JOB_COMMENT)
        odd_day_job.hour.on(22)
        odd_day_job.dow.on(1, 3, 5)

        cron.write()

    def remove_cron_jobs(self):
        cron = CronTab(user=settings.LINKEDIN_CRON_USER)
        cron.remove_all(comment=self.CRON_JOB_COMMENT)
        cron.write()


def get_linkedin_settings(command_args=None) -> LinkedInSettings:
    if env_file := getattr(command_args, LinkedInCommandArgs.LINKEDIN_ENV_FILE.strip("--"), None):
        if not Path(env_file).exists():
            raise Exception("Env file does not exist. Please pass a valid env file.")
        load_dotenv(env_file)

    settings = LinkedInSettings()

    for arg_name in dir(LinkedInCommandArgs):
        if arg_name.startswith("LINKEDIN"):
            value = os.getenv(arg_name, None) or getattr(
                command_args, getattr(LinkedInCommandArgs, arg_name).strip("--")
            )

            setattr(settings, arg_name, value)

    settings.LINKEDIN_BROWSER_CRON = int(settings.LINKEDIN_BROWSER_CRON)
    settings.LINKEDIN_BROWSER_HEADLESS = int(settings.LINKEDIN_BROWSER_HEADLESS)

    settings.LINKEDIN_PREFERRED_USER = Path(settings.LINKEDIN_PREFERRED_USER).absolute()
    settings.LINKEDIN_NOT_PREFERRED_USER = Path(settings.LINKEDIN_NOT_PREFERRED_USER).absolute()

    return settings


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        LinkedInCommandArgs.LINKEDIN_ENV_FILE,
        type=str,
        default=os.getenv(LinkedInSettingsName.LINKEDIN_ENV_FILE, None),
        help="Linkedin environment file",
    )

    parser.add_argument(
        "--email", type=str, default=os.getenv(LinkedInSettingsName.LINKEDIN_USER, None), help="Email of linkedin user"
    )

    parser.add_argument(
        "--password",
        type=str,
        default=os.getenv(LinkedInSettingsName.LINKEDIN_PASSWORD, None),
        help="Password of linkedin user",
    )

    parser.add_argument(
        "--browser",
        type=str,
        default=os.getenv(LinkedInSettingsName.LINKEDIN_BROWSER, "Chrome"),
        help="Browser used for linkedin",
    )

    parser.add_argument(
        "--driver",
        type=str,
        default=os.getenv(LinkedInSettingsName.LINKEDIN_BROWSER_DRIVER, None),
        help="Path to Chrome/Firefox driver",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Whether to run headless",
        default=os.getenv(LinkedInSettingsName.LINKEDIN_BROWSER_HEADLESS, False),
    )

    parser.add_argument(
        "--cron",
        action="store_true",
        help="Whether to create a cron job",
        default=os.getenv(LinkedInSettingsName.LINKEDIN_BROWSER_CRON, False),
    )

    parser.add_argument(
        "--cronuser",
        type=str,
        default=os.getenv(LinkedInSettingsName.LINKEDIN_CRON_USER, None),
        help="Run cron jobs as this user",
    )

    parser.add_argument(
        "--rmcron",
        action="store_true",
        default=False,
        help="Whether to remove existing cron",
    )

    parser.add_argument(
        "--preferred",
        type=str,
        default=os.getenv(LinkedInSettingsName.LINKEDIN_PREFERRED_USER, ""),
        help="Path to file containing preferred users characteristics",
    )

    parser.add_argument(
        "--notpreferred",
        type=str,
        default=os.getenv(LinkedInSettingsName.LINKEDIN_NOT_PREFERRED_USER, ""),
        help="Path to file containing characteristics of not preferred users",
    )

    args = parser.parse_args()

    settings = get_linkedin_settings(command_args=args)

    # print(settings)

    if not (
        settings.LINKEDIN_USER
        and settings.LINKEDIN_PASSWORD
        and settings.LINKEDIN_BROWSER
        and settings.LINKEDIN_BROWSER_DRIVER
    ):
        exit(1)

    if settings.LINKEDIN_BROWSER_CRON and not settings.LINKEDIN_CRON_USER:
        exit(2)

    with LinkedIn(
        username=settings.LINKEDIN_USER,
        password=settings.LINKEDIN_PASSWORD,
        browser=settings.LINKEDIN_BROWSER,
        driver_path=settings.LINKEDIN_BROWSER_DRIVER,
        headless=bool(settings.LINKEDIN_BROWSER_HEADLESS),
    ) as ln:

        if args.rmcron:
            ln.remove_cron_jobs()

        if settings.LINKEDIN_BROWSER_CRON:
            ln.set_smart_cron(settings)
        else:
            ln.smart_follow_unfollow(
                users_preferred=settings.LINKEDIN_PREFERRED_USER or [],
                users_not_preferred=settings.LINKEDIN_NOT_PREFERRED_USER or [],
            )
