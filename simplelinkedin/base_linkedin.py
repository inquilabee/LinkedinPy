import os
from abc import ABC, abstractmethod

from simpleselenium import Browser

from simplelinkedin import settings


class AbstractBaseLinkedin(ABC):
    HOME_PAGE: str
    LOGIN_PAGE: str
    NETWORK_HOME_PAGE: str
    NETWORK_RECEIVED_INVITATIONS_PAGE: str
    NETWORK_SENT_INVITATIONS_PAGE: str
    USER_PROFILE_PAGE: str
    USER_FEED_URL: str

    WEEKLY_MAX_INVITATION: int = 100
    IMPLICIT_WAIT: int = 10

    def __init__(self, username, password, browser, headless):
        self.username = username
        self.password = password
        self.browser_name = browser
        self._user_logged_in: bool = False
        self.browser = Browser(name=browser, implicit_wait=self.IMPLICIT_WAIT, headless=headless)
        self.logger = settings.getLogger(__name__)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.close()

    @property
    def tabs(self):
        return self.browser.tabs

    @abstractmethod
    def count_invitations_sent_last_week(self, force_counting: bool = False) -> int:
        pass

    @abstractmethod
    def login(self) -> bool:
        """Should try to log in the user with given credentials.

        Returns a bool based on whether the login attempt was successful or not.
        """
        pass

    @abstractmethod
    def send_invitations(
        self,
        max_invitation=20,
        min_mutual=0,
        max_mutual=500,
        view_profile=True,
        preferred_users: list | os.PathLike = None,
        not_preferred_users: list | os.PathLike = None,
    ):
        pass

    @abstractmethod
    def accept_invitations(self):
        pass

    @abstractmethod
    def withdraw_sent_invitations(self, older_tha_days=14, max_remove=20):
        pass

    @abstractmethod
    def view_profile(self, username):
        pass
