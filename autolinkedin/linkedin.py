import os
from contextlib import suppress

from seleniumtabs import Tab

from autolinkedin.base_linkedin import AbstractBaseLinkedin
from autolinkedin.decorators import login_required
from autolinkedin.exceptions import InvalidConnection, LinkedInLoginError
from autolinkedin.settings import getLogger
from autolinkedin.utils.core import find_in_text, get_preferences
from autolinkedin.wait import humanized_wait


class LinkedIn(AbstractBaseLinkedin):
    HOME_PAGE = "https://www.linkedin.com/feed/"
    LOGIN_PAGE = "https://www.linkedin.com/login"
    NETWORK_HOME_PAGE = "https://www.linkedin.com/mynetwork/"
    NETWORK_RECEIVED_INVITATIONS_PAGE = "https://www.linkedin.com/mynetwork/invitation-manager/"
    NETWORK_SENT_INVITATIONS_PAGE = "https://www.linkedin.com/mynetwork/invitation-manager/sent/"
    USER_PROFILE_PAGE = "https://www.linkedin.com/in/{username}/"
    USER_FEED_URL = "https://www.linkedin.com/feed/"
    PEOPLE_SEARCH_URL = (
        "https://www.linkedin.com/search/results/people/"
        "?keywords={words}"
        "&network={connections}"
        "&page={page_number}"
    )

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

    def login(self) -> bool:
        """Try login using given credentials"""

        if self._user_logged_in:
            self.logger.info("User already logged in.")
            return self._user_logged_in

        login_tab = self.browser.open(self.LOGIN_PAGE)

        try:
            self._attempt_login(login_tab)
            login_tab.wait_for_body_tag_presence_and_visibility(10)
            login_tab.scroll(times=3)
        except Exception as e:  # noqa
            self.logger.exception(f"{self.username} Login attempt failed")
        else:
            login_tab.wait_for_url(self.USER_FEED_URL)
            self._user_logged_in = self.USER_FEED_URL in login_tab.url
            self.logger.info(f"{self.username} Login attempt {'successful' if self._user_logged_in else 'failed'}.")

        if not self._user_logged_in:
            raise LinkedInLoginError("Unexpected error occured! Could not login. Check your credentials and try again.")

        return self._user_logged_in

    @login_required
    def get_connection_recommendations(self, tab: Tab = None) -> tuple[Tab, list[dict]]:
        def convert_to_int(int_text: str):
            with suppress(Exception):
                return int(int_text)

            return -1

        name_class = "discover-person-card__name"
        occupation_class = "discover-person-card__occupation"
        connections_class = "member-insights__reason"
        connect_button_text = "Connect"

        scroll_times_on_recommendation_page = 20

        networking_home_tab = tab or self.browser.open(self.NETWORK_HOME_PAGE)
        networking_home_tab.wait_for_body_tag_presence_and_visibility(wait=5)

        networking_home_tab.scroll(times=scroll_times_on_recommendation_page)

        user_connect_buttons = networking_home_tab.jq.find_elements_with_text(selector="span", text=connect_button_text)

        cards = []

        for connect_button in user_connect_buttons:
            user_card = networking_home_tab.jq.find_closest_ancestor("li", connect_button)

            try:
                name = networking_home_tab.jq(f".{name_class}", user_card, first_match=True).text.strip()

                occupation = networking_home_tab.jq(f".{occupation_class}", user_card, first_match=True).text.strip()

                mutual_connections = networking_home_tab.jq(
                    f".{connections_class}", user_card, first_match=True
                ).text.strip()

                profile_link = networking_home_tab.jq("a", user_card, first_match=True).get_attribute("href").strip()

                clickable_connect_button = networking_home_tab.jq.find_closest_ancestor("button", connect_button)

                remove_connection_button = networking_home_tab.jq("button", user_card, first_match=True)

                if name and clickable_connect_button:
                    user = {
                        "name": name,
                        "profile_link": profile_link,
                        "occupation": " ".join(occupation.lower().split()),
                        "mutual_connections": convert_to_int(mutual_connections.strip("mutual connections").strip()),
                        "connect_button": clickable_connect_button,
                        "remove_connection_button": remove_connection_button,
                    }

                    cards.append(user)
            except Exception as e:  # noqa
                self.logger.exception("Could not find user details")

        return networking_home_tab, cards

    @login_required
    def get_sent_invitations(self, sent_invitation_tab: Tab = None) -> (Tab, list[dict]):
        def get_sent_time(button, tab) -> int:
            return self._convert_invitation_sent_text_to_days(
                tab.jq(
                    selector=f"span.{sent_time_class}",
                    element=tab.jq.find_closest_ancestor("li", button),
                    first_match=True,
                ).text.strip()
            )

        sent_invitation_tab: Tab = sent_invitation_tab or self.browser.open(self.NETWORK_SENT_INVITATIONS_PAGE)

        sent_invitation_tab.scroll(times=10)

        withdraw_invitation_button_text = "Withdraw"
        sent_time_class = "time-badge"

        withdraw_buttons = sent_invitation_tab.jq.find_elements_with_text(
            selector="span", text=withdraw_invitation_button_text
        )

        sent_invitation_cards = [
            {
                "withdraw_button": withdraw_button,
                "sent_time": get_sent_time(withdraw_button, sent_invitation_tab),
            }
            for withdraw_button in withdraw_buttons
        ]

        return sent_invitation_tab, sent_invitation_cards

    def send_invitations(
        self,
        max_invitations: int = 20,
        min_mutual: int = 0,
        max_mutual: int = 500,
        view_profile: bool = True,
        preferred_users: list | os.PathLike | str = None,
        not_preferred_users: list | os.PathLike | str = None,
        remove_recommendations: bool = False,
        close_profile_tab: bool = True,
    ) -> int:
        """Send Invitations based on set conditions.

        Additionally and optionally, do the following:
        - view profile of users you send request to
        - remove recommendations who do not match the criteria


        :param close_profile_tab: Whether to close the profile tab of users we sent request to
        :param remove_recommendations: Whether to remove recommendation which does not meet criteria
        :param max_invitations: maximum invitations to send
        :param min_mutual:
        :param max_mutual:
        :param view_profile:
        :param preferred_users:
        :param not_preferred_users:
        :return:
        """

        users_preferred = get_preferences(preferred_users)
        users_not_preferred = get_preferences(not_preferred_users)

        if max_invitations <= 0:
            return 0

        sent_invitation_count, retry_times = 0, 5

        networking_home_tab = self.browser.open(self.NETWORK_HOME_PAGE)

        for _ in range(retry_times):
            if sent_invitation_count >= max_invitations:
                break

            networking_home_tab.refresh()
            networking_home_tab, user_cards = self.get_connection_recommendations(networking_home_tab)

            self.logger.info(f"Found a total of {len(user_cards)} connection recommendations.")

            all_cards = [
                (card, self._is_user_eligible(card, users_preferred, users_not_preferred))
                for card in user_cards
                if min_mutual <= card["mutual_connections"] <= max_mutual
            ]

            valid_cards = [card for card, status in all_cards if status]
            invalid_cards = [card for card, status in all_cards if not status]

            self.logger.info(f"Filtered {len(valid_cards)} valid users recommendations based on set criteria.")
            self.logger.info(f"Filtered {len(invalid_cards)} invalid users recommendations based on set criteria.")

            for card in valid_cards:
                connect_button = card["connect_button"]

                try:
                    networking_home_tab.click(connect_button)
                except Exception as e:  # noqa
                    self.logger.exception(
                        "Sometimes, there is an exception when a user card is available multiple times on a page. "
                        "Have a look!"
                    )
                else:
                    self.logger.info(f"Sent connection request to: {card}")

                    sent_invitation_count = sent_invitation_count + 1

                    view_profile and self.view_profile(
                        username_or_link=card["profile_link"], close_tab=close_profile_tab
                    )

                    networking_home_tab.switch()

                    humanized_wait(3)

                if sent_invitation_count >= max_invitations:
                    break

            remove_recommendations and self._delete_not_matching_recommendations(networking_home_tab, invalid_cards)

        return sent_invitation_count

    @login_required
    def accept_invitations(self):
        invitation_card_actions = "invitation-card__action-container"

        invitation_request_tab = self.browser.open(self.NETWORK_RECEIVED_INVITATIONS_PAGE)

        invitation_buttons = invitation_request_tab.css(f".{invitation_card_actions}")

        self.logger.info(f"Number of invitations received: {len(invitation_buttons)}")

        for invitation_button in invitation_buttons:
            _, accept = invitation_button.css("button")
            invitation_request_tab.click(accept)

            humanized_wait(3)

    @login_required
    def withdraw_sent_invitations(self, older_than_days: int = 10, max_remove=20) -> int:
        """Withdraw invitations sent before this many days.

        :param older_than_days: Withdraw invitations with more than this many days
        :param max_remove: maximum number of invitations to remove
                         (0 => all invitations matching the criteria)
        :return: Count of withdrawn invitations
        """
        sent_invitation_pagination_class_name = "mn-invitation-pagination"
        withdraw_modal_confirm_class = "artdeco-modal"
        withdraw_invitation_button_modal_confirm_text = "Withdraw"

        number_of_removed_invitation = 0
        maximum_invitations_to_remove = max_remove or 1000

        sent_invitation_tab = self.browser.open(self.NETWORK_SENT_INVITATIONS_PAGE)

        while True:
            _, sent_invitations = self.get_sent_invitations(sent_invitation_tab)

            request_to_withdraw = [invite for invite in sent_invitations if invite["sent_time"] > older_than_days]

            for sent_invitation in request_to_withdraw:
                if number_of_removed_invitation >= maximum_invitations_to_remove:
                    break

                sent_invitation_tab.click(sent_invitation["withdraw_button"])

                withdrawal_confirm_modal_button = sent_invitation_tab.jq.find_elements_with_text(
                    selector=f".{withdraw_modal_confirm_class} button",
                    text=withdraw_invitation_button_modal_confirm_text,
                    first_match=True,
                )

                sent_invitation_tab.click(withdrawal_confirm_modal_button)

                number_of_removed_invitation += 1

                with suppress(Exception):
                    # Weird: Sometimes, waiting for staleness raises StaleReference Exception :P

                    sent_invitation_tab.wait_until_staleness(
                        withdrawal_confirm_modal_button, wait=self.MAX_WAIT_STALENESS
                    )
                    sent_invitation_tab.wait_for_body_tag_presence_and_visibility(wait=self.MAX_WAIT_STALENESS)

                humanized_wait(3)

            if number_of_removed_invitation >= maximum_invitations_to_remove:
                break

            if not (
                pagination := sent_invitation_tab.jq(
                    selector=f".{sent_invitation_pagination_class_name}", first_match=True
                )
            ):
                break

            next_button = sent_invitation_tab.jq.find_elements_with_text(
                text="Next", element=pagination, first_match=True
            )

            pagination_disabled_next_button_class_name = "artdeco-button--disabled"

            if sent_invitation_tab.jq.has_class(
                element=next_button, class_name=pagination_disabled_next_button_class_name
            ):
                break

            sent_invitation_tab.click(next_button)
            sent_invitation_tab.wait_for_body_tag_presence_and_visibility(wait=10)

        self.logger.info(f"Withdrew {number_of_removed_invitation} invitations")

        return number_of_removed_invitation

    @login_required
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

        last_week_invitations = len([invite for invite in sent_invitations if invite["sent_time"] <= 7])

        if (
            sent_invitations
            and sent_invitations[-1]["sent_time"] <= 7
            and (pagination := sent_invitation_tab.jq(f".{sent_invitation_pagination_class_name}", first_match=True))
        ):
            pagination_next_button_text = "Next"

            next_button = sent_invitation_tab.jq.find_elements_with_text(
                text=pagination_next_button_text, element=pagination, first_match=True
            )

            pagination_disabled_next_button_class_name = "artdeco-button--disabled"

            if not sent_invitation_tab.jq.has_class(
                element=next_button, class_name=pagination_disabled_next_button_class_name
            ):
                sent_invitation_tab.click(next_button)
                sent_invitation_tab.wait_for_body_tag_presence_and_visibility(wait=10)

                last_week_invitations += self.count_invitations_sent_last_week(
                    force_counting=force_counting,
                    sent_invitation_tab=sent_invitation_tab,
                )

        self.__last_week_invitations = last_week_invitations

        return last_week_invitations

    @login_required
    def view_profile(self, username_or_link: str, wait=5, close_tab: bool = True):
        """
        Given username of the profile, it opens the user profile and waits for the given time period.
        One can close the tab or let that be until the end of the session.

        :param username_or_link: LinkedIn username or profile link
        :param wait: wait time in sec
        :param close_tab: close the tab
        :return: None
        """

        self.logger.info(f"Viewing profile of user: {username_or_link}")

        user_profile_link = (
            username_or_link if "/" in username_or_link else self.USER_PROFILE_PAGE.format(username=username)  # noqa
        )
        user_profile_tab = self.browser.open(user_profile_link)
        user_profile_tab.wait_for_body_tag_presence_and_visibility()
        not close_tab and wait and humanized_wait(wait)
        close_tab and self.browser.close_tab(user_profile_tab)

    @login_required
    def remove_recommendations(self, min_mutual: int, max_mutual: int, max_remove: int = None):
        """Remove recommendations from the recommendation page.

        Note that it takes some time for LinkedIn to remove (and refresh) recommendations
        and removed recommendations may appear again.
        """

        if min_mutual <= 1 and max_mutual <= 1:
            self.logger.info("Removed No recommendations")
            return 0

        recommendation_tab, suggestions = self.get_connection_recommendations()

        self.logger.info(f"Found a total of {len(suggestions)} users recommendations")

        valid_suggestions = [
            suggestion for suggestion in suggestions if min_mutual < suggestion["mutual_connections"] < max_mutual
        ][:max_remove]

        self.logger.info(f"Filtered {len(valid_suggestions)} users recommendations to remove based on set criteria.")

        for suggestion in valid_suggestions:
            remove_button = suggestion["remove_connection_button"]

            if recommendation_tab.click(remove_button):
                humanized_wait(3)

        self.logger.info(f"Removed {len(valid_suggestions)} recommendations")

        return len(valid_suggestions)

    @login_required
    def search_people(self, search_term: str, connections: int | list[int] = 2, page_number: int = 1) -> dict:
        if isinstance(connections, int):
            connections = [connections]

        connection_str = {1: '"F"', 2: '"S"', 3: '"O"'}

        for connection in connections:
            if connection not in [1, 2, 3]:
                raise InvalidConnection(f"Please check connection values. Allowed: {connection_str}")  # noqa

        network = "[" + ",".join([connection_str[connection] for connection in connections]) + "]"

        search_url = self.PEOPLE_SEARCH_URL.format(  # noqa
            words=search_term, connections=network, page_number=page_number
        )

        self.logger.debug(f"Searching url: {search_url}")

        search_tab = self.browser.open(search_url)
        search_tab.scroll()

        search_result_class = "reusable-search__result-container"
        title_class = "entity-result__title-text"
        primary_subtitle_class = "entity-result__primary-subtitle"
        pagination_class = "artdeco-pagination__pages"

        search_result = []

        for res in search_tab.jq(selector=f".{search_result_class}"):
            with suppress(Exception):
                name = search_tab.jq(selector=f".{title_class} a span span", element=res, first_match=True).text
                profile_link = search_tab.get_attribute(
                    element=search_tab.jq(selector=f".{title_class} a", element=res, first_match=True), attr_name="href"
                ).split("?")[0]
                occupation = search_tab.jq(selector=f".{primary_subtitle_class}", element=res, first_match=True).text
                connect_button = search_tab.jq(selector="button", element=res, first_match=True)

                search_result.append(
                    {
                        "name": name,
                        "occupation": occupation,
                        "profile_link": profile_link,
                        "connect_button": connect_button,
                    }
                )

        result = {"items": search_result}

        if pagination := search_tab.jq(f".{pagination_class}"):
            current_page = search_tab.jq("li.active", pagination, first_match=True)
            total_pages = search_tab.jq("li", pagination)[-1].text.strip()

            pagination_next_button_class = "artdeco-pagination__button--next"

            next_page = search_tab.jq(f"button.{pagination_next_button_class}", first_match=True)
            disabled_next_button_class = "artdeco-button--disabled"

            has_more = not search_tab.jq.has_class(element=next_page, class_name=disabled_next_button_class)

            result |= {"current_page": current_page.text.strip(), "total_pages": total_pages, "has_more": has_more}

        return result

    def _convert_invitation_sent_text_to_days(self, invitation_time: str) -> int | float:
        """Find how many days ago an invitation was sent."""

        # Sent <number?> <seconds/minutes/days/months/years/today/yesterday> <ago?>

        self.logger.info(f"Sent ago text: {invitation_time}")

        recently_sent_units = ["second", "minute", "hour", "today", "yesterday"]

        if any(r_units in invitation_time for r_units in recently_sent_units):
            self.logger.info(f"Invitation seems to sent very recently: {invitation_time}")
            return 1

        try:
            _, num, unit, _ = invitation_time.split()
        except ValueError:
            self.logger.error(f"Error in converting to days: {invitation_time}. Returning 1.")
            return 1

        num = int(num)

        # TODO: need addendum for days? 1 month ago can mean 1 to 1 month 29 days ago.

        factor = {
            "day": 1,
            "week": 7,
            "month": 30,
            "year": 365,
        }

        result = next(
            (multi_factor * num for factor, multi_factor in factor.items() if factor in unit),
            -1,
        )

        self.logger.info(f"This invitation ({invitation_time}) was sent approximately {result} days ago")

        return result

    def _is_user_eligible(
        self,
        user_details: dict,
        preferred_users: list = None,
        not_preferred_users: list = None,
    ) -> bool:
        """Know if the user is eligible (based on set preferences)

        :return: True if the user matches criteria, False otherwise
        """

        matching_preference = isinstance(preferred_users, list) and find_in_text(
            user_details["occupation"], preferred_users
        )

        matching_not_preference = (
            not_preferred_users  # !important
            and isinstance(not_preferred_users, list)
            and find_in_text(user_details["occupation"], not_preferred_users)
        )

        self.logger.info(f"""User info: {user_details}""")
        self.logger.info(f"Extracted user data: Preference matched = {matching_preference}")
        self.logger.info(f"Extracted user data: Not-preferred matched = {matching_not_preference}")

        return False if matching_not_preference else bool(matching_preference)

    @staticmethod
    def _delete_not_matching_recommendations(tab: Tab, user_cards):
        for card in user_cards:
            remove_button = card["remove_connection_button"]

            with suppress(Exception):
                if tab.click(remove_button):
                    humanized_wait(3)

    def _attempt_login(self, login_tab):
        username_input = login_tab.jq("#username")
        password_input = login_tab.jq("#password")
        submit_button = login_tab.jq("button", first_match=True)

        username_input.send_keys(self.username)
        password_input.send_keys(self.password)

        login_tab.click(submit_button)

    def smart_follow_unfollow(
        self,
        min_mutual: int = 0,
        max_mutual: int = 500,
        users_preferred: os.PathLike | str | list = None,
        users_not_preferred: os.PathLike | str | list = None,
        withdraw_invite_older_than_days: int = 14,
        max_invitations_to_send: int = 0,
        remove_recommendations: bool = True,
    ):
        """Consolidation of important methods of the class"""

        users_preferred = get_preferences(users_preferred)
        users_not_preferred = get_preferences(users_not_preferred)

        self.withdraw_sent_invitations(older_than_days=withdraw_invite_older_than_days)

        max_invitations_to_send = (
            min(max_invitations_to_send, self.WEEKLY_MAX_INVITATION)
            or self.WEEKLY_MAX_INVITATION - self.count_invitations_sent_last_week()
        )

        self.logger.info(f"Invitations sent last week: {self.count_invitations_sent_last_week()}")
        self.logger.info(f"Max invitations to send: {max_invitations_to_send}")

        self.remove_recommendations(0, min_mutual - 1, max_remove=30)

        self.send_invitations(
            max_invitations=max_invitations_to_send,
            min_mutual=min_mutual,
            max_mutual=max_mutual,
            preferred_users=users_preferred,
            not_preferred_users=users_not_preferred,
            view_profile=True,
            remove_recommendations=remove_recommendations,
        )

        self.accept_invitations()
