import os
from contextlib import suppress
from pathlib import Path

from selenium.webdriver.common.by import By
from simpleselenium import Tab
from simpleselenium.utils.core import find_element_by_text

from simplelinkedin.base_linkedin import AbstractBaseLinkedin
from simplelinkedin.settings import getLogger
from simplelinkedin.wait import humanized_wait


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

    def convert_invitation_sent_text_to_days(self, invitation_time: str):
        """Find how many days ago an invitation was sent."""

        # Sent <number?> <seconds/minutes/days/months/years/today> <ago?>

        self.logger.info(f"Sent ago text: {invitation_time}")

        try:
            _, num, unit, _ = invitation_time.split()
        except ValueError:
            self.logger.info(f"Invitation seems to sent very recently: {invitation_time}")
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

        self.logger.info(f"This invitation ({invitation_time}) was sent approximately {result} days ago")

        return result

    @staticmethod
    def is_matching_user_preference(user_details: dict, preferences: list) -> bool:
        """A simple substring search to know if a given user matches the set preferences."""

        # TODO: Improve matching algorithm

        if not preferences:
            return True

        if user_card_text := user_details["occupation"]:
            return any(pref in user_card_text or user_card_text in pref for pref in preferences)
        else:
            return False

    def is_user_eligible(
        self,
        user_details: dict,
        preferred_users: list = None,
        not_preferred_users: list = None,
    ) -> bool:
        """Know if the user is eligible (based on set preferences)

        :return: True if the user matches criteria, False otherwise
        """

        # Order of the operation is very important
        # filter by mutual connections
        # match with preference
        # match with not preferred
        # None of the above method worked, return False

        matching_preference = isinstance(preferred_users, list) and self.is_matching_user_preference(
            user_details, preferred_users
        )

        matching_not_preference = (
            not_preferred_users  # !important
            and isinstance(not_preferred_users, list)
            and self.is_matching_user_preference(user_details, not_preferred_users)
        )

        self.logger.info(f"""User info: {user_details}""")
        self.logger.info(f"Extracted user data: Preference matched = {matching_preference}")
        self.logger.info(f"Extracted user data: Not-preferred matched = {matching_not_preference}")

        return False if matching_not_preference else bool(matching_preference)

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
        login_tab.wait_for_body_tag_presence_and_visibility()
        login_tab.scroll(times=3)

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

    def get_connection_recommendation_cards(self) -> [Tab, list[dict]]:
        def convert_to_int(int_text: str):
            with suppress(Exception):
                return int(int_text)

            return -1

        name_class = "discover-person-card__name"
        occupation_class = "discover-person-card__occupation"
        connections_class = "member-insights__reason"
        connect_button_text = "Connect"

        scroll_times_on_recommendation_page = 20

        networking_home_tab = self.browser.open(self.NETWORK_HOME_PAGE)
        networking_home_tab.wait_for_body_tag_presence_and_visibility(wait=5)

        networking_home_tab.inject_jquery(by="file", wait=5)
        networking_home_tab.scroll(times=scroll_times_on_recommendation_page)

        user_connect_buttons = networking_home_tab.run_js(
            script=f"""return $("span:contains('{connect_button_text}')")"""
        )

        cards = []

        for connect_button in user_connect_buttons:
            user_card = networking_home_tab.run_jquery(
                script_code="""return $(arguments[0]).closest('li')""", element=connect_button
            )

            name = networking_home_tab.run_jquery(
                script_code=f"""return $(arguments[0]).find(".{name_class}").text()""", element=user_card
            ).strip()

            occupation = networking_home_tab.run_jquery(
                script_code=f"""return $(arguments[0]).find(".{occupation_class}").text()""", element=user_card
            ).strip()

            mutual_connections = networking_home_tab.run_jquery(
                script_code=f"""return $(arguments[0]).find(".{connections_class}").text()""", element=user_card
            ).strip()

            profile_link = networking_home_tab.run_jquery(
                script_code="""return $(arguments[0]).find('a:first-of-type').attr('href')""", element=user_card
            )

            clickable_connect_button = networking_home_tab.run_jquery(
                script_code="""return $(arguments[0]).closest('button')""", element=connect_button
            )

            if name and clickable_connect_button:
                user = {
                    "name": name,
                    "profile_link": profile_link,
                    "occupation": " ".join(occupation.lower().split()),
                    "mutual_connections": convert_to_int(mutual_connections.strip("mutual connections").strip()),
                    "connect_button": clickable_connect_button[0],
                }

                cards.append(user)

        return networking_home_tab, cards

    def send_invitations(
        self,
        max_invitations: int = 20,
        min_mutual: int = 0,
        max_mutual: int = 500,
        view_profile: bool = True,
        preferred_users: list | os.PathLike | str = None,
        not_preferred_users: list | os.PathLike | str = None,
    ):
        """

        :param max_invitations:
        :param min_mutual:
        :param max_mutual:
        :param view_profile:
        :param preferred_users:
        :param not_preferred_users:
        :return:
        """

        users_preferred, users_not_preferred = self.get_user_preferences(preferred_users, not_preferred_users)

        if max_invitations <= 0:
            return 0

        sent_invitation_count = 0
        retry_times = 5

        for _ in range(retry_times):
            if sent_invitation_count >= max_invitations:
                break

            networking_home_tab, user_cards = self.get_connection_recommendation_cards()

            valid_cards = [
                card
                for card in user_cards
                if min_mutual <= card["mutual_connections"] <= max_mutual
                and self.is_user_eligible(card, users_preferred, users_not_preferred)
            ]

            for card in valid_cards:
                connect_button = card["connect_button"]

                try:
                    networking_home_tab.click(connect_button)
                except Exception as e:  # noqa
                    """Sometimes there is an exception when a user card is available multiple times on a page."""
                else:
                    self.logger.info(f"Sent connection request to: {card}")

                    sent_invitation_count = sent_invitation_count + 1

                    if view_profile:
                        self.view_profile(username_or_link=card["profile_link"])
                        networking_home_tab.switch()

                    humanized_wait(3)

                if sent_invitation_count > max_invitations:
                    break

        return sent_invitation_count

    def accept_invitations(self):
        invitation_card_actions = "invitation-card__action-container"

        invitation_request_tab = self.browser.open(self.NETWORK_RECEIVED_INVITATIONS_PAGE)

        invitation_buttons = invitation_request_tab.css(f".{invitation_card_actions}")

        self.logger.info(f"Number of invitations received: {len(invitation_buttons)}")

        for invitation_button in invitation_buttons:
            _, accept = invitation_button.css("button")
            invitation_request_tab.click(accept)

    @staticmethod
    def get_sent_invitations(sent_invitation_tab) -> (Tab, list[dict]):
        sent_invitation_tab.inject_jquery(by="file", wait=5)
        sent_invitation_tab.scroll(times=10)

        withdraw_invitation_button_text = "Withdraw"
        sent_time_class = "time-badge"

        withdraw_buttons = sent_invitation_tab.run_js(
            script=f"""
                return $("span:contains('{withdraw_invitation_button_text}')")
            """
        )

        sent_invitation_cards = [
            {
                "withdraw_button": withdraw_button,
                "sent_time": sent_invitation_tab.run_jquery(
                    f"""
                        return $(arguments[0]).closest('li').find('span.{sent_time_class}').text()
                    """,
                    element=withdraw_button,
                ).strip(),
            }
            for withdraw_button in withdraw_buttons
        ]

        return sent_invitation_tab, sent_invitation_cards

    def remove_sent_invitations(self, older_than_days=10, max_remove=20) -> int:
        """

        :param older_than_days: withdraw invitations with more than this many days
        :param max_remove: maximum number of invitations to remove
                         0 => all invitations matching the criteria
        :return: Count of withdrawn invitations
        """
        sent_invitation_pagination_class_name = "mn-invitation-pagination"
        withdraw_invitation_button_modal_confirm_text = "Withdraw"

        number_of_removed_invitation = 0
        maximum_invitations_to_remove = max_remove or 1000

        sent_invitation_tab = self.browser.open(self.NETWORK_SENT_INVITATIONS_PAGE)

        while True:
            _, sent_invitations = self.get_sent_invitations(sent_invitation_tab)

            request_to_withdraw = [
                invite
                for invite in sent_invitations
                if self.convert_invitation_sent_text_to_days(invitation_time=invite["sent_time"]) >= older_than_days
            ]

            for sent_invitation in request_to_withdraw:
                if number_of_removed_invitation > maximum_invitations_to_remove:
                    break

                sent_invitation_tab.click(sent_invitation["withdraw_button"])

                withdrawal_confirm_modal_button = find_element_by_text(
                    element=sent_invitation_tab.driver, text=withdraw_invitation_button_modal_confirm_text
                )

                sent_invitation_tab.click(withdrawal_confirm_modal_button)

                sent_invitation_tab.wait_for_body_tag_presence_and_visibility(wait=self.MAX_WAIT_STALENESS)
                sent_invitation_tab.wait_until_staleness(withdrawal_confirm_modal_button, wait=self.MAX_WAIT_STALENESS)

                humanized_wait(3)

                number_of_removed_invitation += 1

            if number_of_removed_invitation > maximum_invitations_to_remove:
                break

            if not (pagination := sent_invitation_tab.css(f".{sent_invitation_pagination_class_name}")):
                break

            next_button = find_element_by_text(element=pagination[0], text="Next")
            next_button = next_button.find_element(by=By.XPATH, value="..")

            pagination_disabled_next_button_class_name = "artdeco-button--disabled"

            if pagination_disabled_next_button_class_name in sent_invitation_tab.get_attribute(next_button, "class"):
                sent_invitation_tab.click(next_button)
                sent_invitation_tab.wait_for_body_tag_presence_and_visibility(wait=10)

        return number_of_removed_invitation

    def count_invitations_sent_last_week(self, force_counting: bool = False, sent_invitation_tab: Tab = None) -> int:
        """Estimated number of invitations sent in the last week.

        Since LinkedIn has weekly limits, this can be helpful.
        """
        sent_invitation_pagination_class_name = "mn-invitation-pagination"

        if not force_counting and self.__last_week_invitations:
            self.logger.info("Using cached information for last week's invitation count")
            return self.__last_week_invitations

        sent_invitation_tab = sent_invitation_tab or self.browser.open(self.NETWORK_SENT_INVITATIONS_PAGE)

        _, sent_invitations = self.get_sent_invitations(sent_invitation_tab)

        last_week_invitations = len(
            [
                invite
                for invite in sent_invitations
                if self.convert_invitation_sent_text_to_days(invitation_time=invite["sent_time"]) <= 7
            ]
        )

        if self.convert_invitation_sent_text_to_days(invitation_time=sent_invitations[-1]["sent_time"]) <= 7 and (
            pagination := sent_invitation_tab.css(f".{sent_invitation_pagination_class_name}")
        ):
            pagination_next_button_text = "Next"
            next_button = find_element_by_text(element=pagination[0], text=pagination_next_button_text)
            next_button = next_button.find_element(by=By.XPATH, value="..")

            pagination_disabled_next_button_class_name = "artdeco-button--disabled"

            if pagination_disabled_next_button_class_name in sent_invitation_tab.get_attribute(next_button, "class"):
                sent_invitation_tab.click(next_button)
                sent_invitation_tab.wait_for_body_tag_presence_and_visibility()

                last_week_invitations += self.count_invitations_sent_last_week(
                    force_counting=force_counting,
                    sent_invitation_tab=sent_invitation_tab,
                )

        self.__last_week_invitations = last_week_invitations

        return last_week_invitations

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
        not close_tab and wait and humanized_wait(wait)
        close_tab and self.browser.close_tab(user_profile_tab)

    def smart_follow_unfollow(
        self,
        min_mutual: int = 0,
        max_mutual: int = 500,
        users_preferred: os.PathLike | str = None,
        users_not_preferred: os.PathLike | str = None,
        withdraw_invite_older_than_days: int = 14,
        max_invitations_to_send: int = 0,
    ):
        users_preferred, users_not_preferred = self.get_user_preferences(users_preferred, users_not_preferred)

        self.login()
        self.remove_sent_invitations(older_than_days=withdraw_invite_older_than_days)

        max_invitations_to_send = (
            min(max_invitations_to_send, self.WEEKLY_MAX_INVITATION)
            or self.WEEKLY_MAX_INVITATION - self.count_invitations_sent_last_week()
        )

        self.send_invitations(
            max_invitations=max_invitations_to_send,
            min_mutual=min_mutual,
            max_mutual=max_mutual,
            preferred_users=users_preferred,
            not_preferred_users=users_not_preferred,
            view_profile=True,
        )

        self.accept_invitations()
