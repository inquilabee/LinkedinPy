import os
import string
import time
from contextlib import suppress
from pathlib import Path

from selenium.webdriver.common.by import By

from simplelinkedin.base_linkedin import AbstractBaseLinkedin
from simplelinkedin.settings import getLogger


class LinkedIn(AbstractBaseLinkedin):
    HOME_PAGE = "https://www.linkedin.com/feed/"
    LOGIN_PAGE = "https://www.linkedin.com/login"
    NETWORK_HOME_PAGE = "https://www.linkedin.com/mynetwork/"
    NETWORK_RECEIVED_INVITATIONS_PAGE = "https://www.linkedin.com/mynetwork/invitation-manager/"
    NETWORK_SENT_INVITATIONS_PAGE = "https://www.linkedin.com/mynetwork/invitation-manager/sent/"
    USER_PROFILE_PAGE = "https://www.linkedin.com/in/{username}/"

    MAX_WAIT_STALENESS = 10

    def __init__(self, username, password, browser="Chrome", headless=False):
        super().__init__(
            username=username,
            password=password,
            browser=browser,
            headless=headless,
        )

        self.__last_week_invitations: int = 0
        self.logger = getLogger(__name__)

    def invitation_sent_days_ago(self, invitation):
        """Find how many days ago an invitation was sent."""

        mutual_connection_button_class_name = "time-badge"

        sent_ago = invitation.find_element(by=By.CLASS_NAME, value=mutual_connection_button_class_name).text

        # Sent <number?> <seconds/minutes/days/months/years/today> <ago?>

        self.logger.info(f"Sent ago text: {sent_ago}")

        try:
            _, num, unit, _ = sent_ago.split()
        except ValueError:
            self.logger.info(f"Invitation seems to sent very recently: {sent_ago}")
            return 1

        num = int(num)

        if any(_unit in unit for _unit in ["second", "minute", "hour", "today"]):
            return 1

        factor = {
            "day": 1,
            "week": 7,
            "month": 30,
            "year": 365,
        }

        result = next(
            (multi_factor * num for _unit, multi_factor in factor.items() if _unit in unit),
            -1,
        )

        self.logger.info(f"This invitation ({invitation}) was sent approximately {result} days ago")

        return result

    @staticmethod
    def is_matching_user_preference(user_card, preferences: list) -> bool:
        """A simple substring search to know if a given user matches the set preferences."""

        # TODO: Improve matching algorithm

        if not preferences:
            return True

        if user_card_text := " ".join(user_card.text.split()).lower():
            return any(pref.lower() in user_card_text or user_card_text in pref.lower() for pref in preferences)
        else:
            return False

    def mutual_connections(self, user_card) -> int:
        """Find the number of mutual connections"""

        user_card_mutual_connection_class_name = "member-insights"

        with suppress(Exception):
            user_insights = user_card.find_element(by=By.CLASS_NAME, value=user_card_mutual_connection_class_name)

            mutual_connection = int(
                "".join([character for character in user_insights.text if character in string.digits]) or "0"
            )

            self.logger.info(f"Mutual connections={mutual_connection} ({user_card.text})")

            return mutual_connection

        self.logger.info(f"Mutual connections could not be found: {user_card.text}")
        return -1

    def is_user_eligible(
        self,
        user_crd,
        min_mutual: int,
        max_mutual: int,
        preferred_users: list = None,
        not_preferred_users: list = None,
    ) -> bool:
        """Know if the user is eligible (based on set preferences)

        :return: True if the user matches criteria, False otherwise
        """

        # Order of the ops is very important
        # filter by mutual connections
        # match with preference
        # match with not preferred
        # None of the above method worked, return False

        user_card_text = " ".join(user_crd.text.split())

        self.logger.info(f"""User info: {user_card_text}""")

        matching_preference = isinstance(preferred_users, list) and self.is_matching_user_preference(
            user_crd, preferred_users
        )

        matching_not_preference = (
            not_preferred_users  # !important
            and isinstance(not_preferred_users, list)
            and self.is_matching_user_preference(user_crd, not_preferred_users)
        )

        mutual_connections = self.mutual_connections(user_crd)

        self.logger.info(f"Extracted user data: mutual connections = {mutual_connections}")
        self.logger.info(f"Extracted user data: Preference matched = {matching_preference}")
        self.logger.info(f"Extracted user data: Not-preferred matched = {matching_not_preference}")

        if min_mutual < mutual_connections < max_mutual:
            if matching_not_preference:
                return False

            if matching_preference:
                return True

        return False

    def login(self) -> bool:
        """Try login using given credentials"""

        if not self._user_logged_in:
            login_tab = self.browser.open(self.LOGIN_PAGE)

            try:
                self._attempt_login(login_tab)
            except Exception as e:  # noqa
                self.logger.info(f"{self.username} Login Attempt Failed")
            else:
                self._user_logged_in = True
                self.logger.info(f"{self.username} Login Attempt successful")
        else:
            self.logger.info("User already logged in.")

        return self._user_logged_in

    def _attempt_login(self, login_tab):
        username_input = login_tab.wait_for_presence_and_visibility(by=By.ID, key="username", wait=10)
        password_input = login_tab.wait_for_presence_and_visibility(by=By.ID, key="password", wait=10)
        submit_button = login_tab.wait_for_presence_and_visibility(by=By.CLASS_NAME, key="btn__primary--large", wait=10)

        username_input.send_keys(self.username)
        password_input.send_keys(self.password)

        login_tab.click(submit_button)

    @staticmethod
    def get_user_preferences(preferred_users, not_preferred_users) -> (list, list):
        if preferred_users and not isinstance(preferred_users, list):
            if not Path(preferred_users).exists():
                raise FileNotFoundError(f"File not found: {Path(preferred_users).absolute()}")

            with open(preferred_users) as f:
                users_preferred = f.readlines()
        elif preferred_users:
            users_preferred = preferred_users
        else:
            users_preferred = []

        if not_preferred_users and not isinstance(not_preferred_users, list):
            if not Path(not_preferred_users).exists():
                raise FileNotFoundError(f"File not found: {Path(not_preferred_users).absolute()}")

            with open(not_preferred_users) as f:
                users_not_preferred = f.readlines()
        elif not_preferred_users:
            users_not_preferred = not_preferred_users
        else:
            users_not_preferred = []

        preferred = [line.strip().lower() for line in users_preferred if line.strip()]
        not_preferred = [line.strip().lower() for line in users_not_preferred if line.strip()]

        return preferred, not_preferred

    def send_invitations(
        self,
        max_invitation: int = 20,
        min_mutual: int = 0,
        max_mutual: int = 500,
        view_profile: bool = True,
        preferred_users: list | os.PathLike | str = None,
        not_preferred_users: list | os.PathLike | str = None,
    ):
        users_preferred, users_not_preferred = self.get_user_preferences(preferred_users, not_preferred_users)

        if max_invitation <= 0:
            return 0

        user_connect_button_text = "Connect"

        user_connection_card_class_names = [
            "discover-entity-card",
            "discover-entity-type-card",
        ]

        scroll_times_on_recommendation_page = 20
        invitations = 0
        retry_times = 5

        for _ in range(retry_times):
            if invitations > max_invitation:
                break

            networking_home_tab = self.browser.open(self.NETWORK_HOME_PAGE)

            networking_home_tab.scroll(times=scroll_times_on_recommendation_page)

            for user_connection_card_class_name in user_connection_card_class_names:
                if all_cards := networking_home_tab.find_element(
                    by=By.CLASS_NAME, value=user_connection_card_class_name, multiple=True
                ):
                    break
            else:
                return invitations

            for card in all_cards:
                user_card_text = " ".join(card.text.split())

                if user_connect_button_text in user_card_text and self.is_user_eligible(
                    card, min_mutual, max_mutual, users_preferred, users_not_preferred
                ):
                    try:
                        connect_button = card.find_element(
                            by=By.XPATH, value=f".//*[text()='{user_connect_button_text}']"
                        )
                        networking_home_tab.click(connect_button)
                        self.logger.info(f"Sent connection request to: {user_card_text}")
                        invitations = invitations + 1

                        if view_profile:
                            link = card.find_element(by=By.TAG_NAME, value="a")
                            user_profile_link = link.get_attribute("href")
                            # self.browser.open(user_profile_link)
                            self.view_profile(username_or_link=user_profile_link)
                            networking_home_tab.switch()

                    except Exception as e:  # noqa
                        """Sometimes there is an exception when a user card is available multiple times on a page."""

                    if invitations > max_invitation:
                        break

        return invitations

    def accept_invitations(self):
        invitation_card_actions = "invitation-card__action-container"

        invitation_request_tab = self.browser.open(self.NETWORK_RECEIVED_INVITATIONS_PAGE)

        invitation_buttons = invitation_request_tab.css(f".{invitation_card_actions}")

        self.logger.info(f"Number of invitations received: {len(invitation_buttons)}")

        for invitation_button in invitation_buttons:
            _, accept = invitation_button.css("button")
            invitation_request_tab.click(accept)

    def remove_sent_invitations(self, older_than_days=10, max_remove=20) -> int:
        """

        :param older_than_days: withdraw invitations with more than this many days
        :param max_remove: maximum number of invitations to remove
                         0 => all invitations matching the criteria
        :return: Count of withdrawn invitations
        """
        withdraw_invitation_button_text = "Withdraw"
        withdraw_invitation_button_modal_text = "Withdraw invitation"
        withdraw_invitation_button_modal_confirm_text = "Withdraw"
        withdraw_invitation_button_modal_cancel_text = "Cancel"
        sent_invitation_class_name = "invitation-card"
        sent_invitation_pagination_class_name = "mn-invitation-pagination"
        pagination_next_button_test = "Next"
        pagination_disabled_next_button_class_name = "artdeco-button--disabled"

        sent_invitation_tab = self.browser.open(self.NETWORK_SENT_INVITATIONS_PAGE)
        sent_invitation_tab.inject_jquery(by="cdn", wait=10)

        number_of_removed_invitation = 0
        maximum_invitations_to_remove = max_remove or 1000

        while True:
            # paginate until you can
            # break when you can't.

            sent_invitations = sent_invitation_tab.find_element(
                by=By.CLASS_NAME, value=sent_invitation_class_name, multiple=True
            )

            while number_of_removed_invitation < maximum_invitations_to_remove:
                sent_invitation = sent_invitations.pop()

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
                        by=By.XPATH,
                        value=f".//*[text()='{withdraw_invitation_button_modal_confirm_text}']",
                    )

                    sent_invitation_tab.click(withdrawal_confirm_modal_button)

                    # The waiting game begins

                    sent_invitation_tab.wait_for_body_tag_presence_and_visibility(wait=self.MAX_WAIT_STALENESS)
                    sent_invitation_tab.wait_until_staleness(
                        withdrawal_confirm_modal_button, wait=self.MAX_WAIT_STALENESS
                    )
                    sent_invitation_tab.wait_until_staleness(confirm_withdrawal_pop_up, wait=self.MAX_WAIT_STALENESS)
                    sent_invitation_tab.wait_until_staleness(withdraw_btn, wait=self.MAX_WAIT_STALENESS)

                    time.sleep(1)

                    number_of_removed_invitation += 1

            if not (
                pagination := sent_invitation_tab.find_element(
                    by=By.CLASS_NAME, value=sent_invitation_pagination_class_name, multiple=False
                )
            ):
                break

            next_button = pagination.find_element(by=By.XPATH, value=f".//*[text()='{pagination_next_button_test}']")

            next_button = next_button.find_element(by=By.XPATH, value="..")

            if pagination_disabled_next_button_class_name in sent_invitation_tab.get_attribute(next_button, "class"):
                break

            sent_invitation_tab.click(next_button)

            time.sleep(5)

            sent_invitation_tab.wait_for_body_tag_presence_and_visibility(wait=10)

        return number_of_removed_invitation

    def invitations_sent_last_week(self, force_counting: bool = False) -> int:
        """Estimated number of invitations sent in the last week.

        Since LinkedIn has weekly limits, this can be helpful.
        """

        if not force_counting and self.__last_week_invitations:
            self.logger.info("Using cached information for last week's invitation count")
            return self.__last_week_invitations

        sent_invitation_class_name = "invitation-card"
        sent_invitation_pagination_class_name = "mn-invitation-pagination"
        pagination_next_button_test = "Next"
        pagination_disabled_next_button_class_name = "artdeco-button--disabled"

        sent_invitation_tab = self.browser.open(self.NETWORK_SENT_INVITATIONS_PAGE)

        total_sent_invitations = 0

        while True:
            try:
                sent_invitation_tab.scroll_to_bottom()

                all_sent_invitations = sent_invitation_tab.find_element(
                    by=By.CLASS_NAME, value=sent_invitation_class_name, multiple=True
                )

                total_sent_invitations = total_sent_invitations + sum(
                    0 <= self.invitation_sent_days_ago(invitation) <= 7 for invitation in all_sent_invitations
                )

                pagination = sent_invitation_tab.find_element(
                    by=By.CLASS_NAME, value=sent_invitation_pagination_class_name, multiple=False
                )

                if not pagination:
                    break

                next_button = pagination.find_element(
                    by=By.XPATH, value=f".//*[text()='{pagination_next_button_test}']"
                )

                next_button = next_button.find_element(by=By.XPATH, value="..")

                if pagination_disabled_next_button_class_name in sent_invitation_tab.get_attribute(
                    next_button, "class"
                ):
                    break

                sent_invitation_tab.click(next_button)

                time.sleep(5)

                sent_invitation_tab.wait_for_body_tag_presence_and_visibility(wait=10)
            except Exception as e:  # noqa
                self.logger.exception("Something went wrong!")
                break

        self.__last_week_invitations = total_sent_invitations

        return total_sent_invitations

    def view_profile(self, username_or_link: str, wait=5, close_tab: bool = False):
        """
        Given username of the profile, it opens the user profile and waits for the given time period.
        One can close the tab or let that be until the end of the session.

        :param username_or_link: LinkedIn username or profile link
        :param wait: wait time in sec
        :param close_tab: close the tab
        :return: None
        """

        user_profile_link = (
            username_or_link if "/" in username_or_link else self.USER_PROFILE_PAGE.format(username=username)  # noqa
        )
        user_profile_tab = self.browser.open(user_profile_link)
        not close_tab and wait and time.sleep(wait)
        close_tab and self.browser.close_tab(user_profile_tab)

    def smart_follow_unfollow(
        self, users_preferred: os.PathLike | str = None, users_not_preferred: os.PathLike | str = None
    ):
        users_preferred, users_not_preferred = self.get_user_preferences(users_preferred, users_not_preferred)

        self.login()
        self.remove_sent_invitations(older_than_days=14)

        self.send_invitations(
            max_invitation=max(self.WEEKLY_MAX_INVITATION - self.invitations_sent_last_week(), 0),
            min_mutual=100,
            max_mutual=400,
            preferred_users=users_preferred,
            not_preferred_users=users_not_preferred,
            view_profile=True,
        )

        self.accept_invitations()
