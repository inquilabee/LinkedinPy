from __future__ import annotations

import os
import time
from collections import OrderedDict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Session:
    """A top level class to manage a browser containing one/more Tabs"""

    BROWSER_DRIVER_FUNCTION = {
        "Chrome": webdriver.Chrome,
        "FireFox": webdriver.Firefox,
    }

    BROWSER_OPTION_FUNCTION = {"Chrome": ChromeOptions, "Firefox": FirefoxOptions}

    def __init__(self, browser_name, driver_path, implicit_wait, user_agent, headless=False):
        self.browser = browser_name

        self.implicit_wait = implicit_wait
        self.user_agent = user_agent
        self.headless = headless

        self.driver_path = driver_path
        self.driver = self._get_driver()

    def _get_driver(self) -> webdriver:
        """returns the driver/browser instance based on set environment variables
        and arguments"""

        driver_options = self.BROWSER_OPTION_FUNCTION[self.browser]()

        if self.headless:
            driver_options.headless = self.headless
            driver_options.add_argument("--disable-gpu")
            driver_options.add_argument("--disable-extensions")
            driver_options.add_argument("--no-sandbox")
            driver_options.add_argument("no-default-browser-check")

        driver = self.BROWSER_DRIVER_FUNCTION[self.browser](
            self.driver_path, options=driver_options
        )
        driver.implicitly_wait(self.implicit_wait)
        # driver.set_page_load_timeout(self.implicit_wait)

        return driver

    def _get_attr_or_env(self, env_var, raise_exception=True):
        if hasattr(self, env_var):
            return getattr(self, env_var)

        driver_path = os.getenv(env_var, None)

        if driver_path:
            return os.getenv(env_var, None)

        if raise_exception:
            raise Exception(f"Please define {env_var} as class attribute or environment variable.")

    def close(self):
        """Close Session"""
        self.__del__()

    def __del__(self):
        self.driver.quit()


class Tab:
    """Single Tab"""

    def __init__(self, session, tab_handle, start_url: str = None):
        self._session = session
        self.tab_handle = tab_handle
        self.start_url = start_url

    def __str__(self):
        return (
            "Tab("
            f"start_url={self.start_url}, "
            f"active={self.is_active}, "
            f"alive={self.is_alive}, "
            f"tab_handle={self.tab_handle}"
            ")"
        )

    @property
    def is_alive(self):
        """Whether the tab is one of the browser tabs"""
        return self.tab_handle in self._session.driver.window_handles

    @property
    def is_active(self):
        """Whether the tab is active tab on the browser"""
        try:
            return self._session.driver.current_window_handle == self.tab_handle
        except:  # noqa
            return False

    @property
    def title(self) -> str:
        """Returns the title of the page at the moment"""
        return self.driver.title

    @property
    def url(self) -> str:
        """Returns the title of the page at the moment"""
        return self.driver.current_url

    @property
    def driver(self) -> webdriver:
        """Switch to tab (if possible) and return driver"""

        if not self.is_alive:
            raise Exception("Current window is dead.")

        if not self.is_active:
            self._session.driver.switch_to.window(self.tab_handle)
        return self._session.driver

    def switch(self) -> None:
        """Switch to tab (if possible)"""

        if self.is_alive:
            self._session.driver.switch_to.window(self.tab_handle)
        else:
            raise Exception(
                f"Current window is dead. Window Handle={self.tab_handle} does not exist"
                f" in all currently open window handles: {self._session.driver.window_handles}"
            )

    def open(self, url):
        """Open a url in the tab"""

        self.driver.get(url)
        return self

    def click(self, element):
        """Click a given element on the page represented by the tab"""

        try:
            self.switch()
            element.click()
        except Exception as e:  # noqa
            try:
                self.driver.execute_script("arguments[0].click();", element)
            except Exception as e:  # noqa
                pass

    def get_all_attributes_of_element(self, element) -> dict:
        """Get all attributes of a given element on the tab's page"""

        attr_dict = self.driver.execute_script(
            "var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) {"
            " items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value };"
            " return items;",
            element,
        )

        return attr_dict

    def get_attribute(self, element, attr_name):
        """Get specific attributes of a given element on the tab's page"""

        attr_dict = self.get_all_attributes_of_element(element=element)
        return attr_dict[attr_name]

    def find_element(self, by, value, multiple=False):
        """Try to find element given a criteria and the value"""

        elements = self.driver.find_elements(by, value)

        if multiple:
            return elements
        elif elements:
            if len(elements) > 1:
                raise Exception("Multiple elements found")
            else:
                return elements[0]
        else:
            return None

    def scroll(self, times=3, wait=1):
        """Usual scroll"""

        for _ in range(times):
            self.scroll_to_bottom(wait=wait)

    def scroll_to_bottom(self, wait=1):
        """Scroll to bottom of the page"""

        html = self.driver.find_element_by_tag_name("html")
        html.send_keys(Keys.END)
        time.sleep(wait)

    def infinite_scroll(self, retries=5):
        """Infinite (so many times) scroll"""

        for _ in range(max(1, retries)):
            try:
                last_height = 0

                while True:
                    self.scroll()
                    new_height = self.driver.execute_script(
                        "return document.documentElement.scrollHeight"
                    )

                    if new_height == last_height:
                        break

                    last_height = new_height
            except Exception as e:  # noqa
                pass

    def wait_for_presence_of_element(self, element, wait):
        return WebDriverWait(self.driver, wait).until(EC.presence_of_element_located(element))

    def wait_for_visibility_of_element(self, element, wait):
        return WebDriverWait(self.driver, wait).until(EC.visibility_of_element_located(element))

    def wait_for_presence_and_visibility_of_element(self, element, wait):
        self.wait_for_visibility_of_element(element, wait)
        return self.wait_for_presence_of_element(element, wait)

    def wait_for_presence(self, by, key, wait):
        return WebDriverWait(self.driver, wait).until(EC.presence_of_element_located((by, key)))

    def wait_for_visibility(self, by, key, wait):
        return WebDriverWait(self.driver, wait).until(EC.visibility_of_element_located((by, key)))

    def wait_for_presence_and_visibility(self, by, key, wait):
        ele = self.wait_for_presence(by, key, wait)
        self.wait_for_visibility(by, key, wait)
        return ele

    def wait_until_staleness(self, element, wait=5):
        """Wait until the passed element is no longer present on the page"""
        WebDriverWait(self.driver, wait).until(EC.staleness_of(element))

        time.sleep(0.5)


class TabManager:
    """A manager for multiple tabs associated with a browser"""

    def __init__(self, session):
        self._session = session
        self._all_tabs = OrderedDict()

    @property
    def driver(self):
        """driver object for the tab"""
        return self._session.driver

    def __len__(self):
        return len(self._all_tabs)

    def __del__(self):
        self._all_tabs = {}

    def __str__(self):
        return " ".join(self.all())

    def current_tab(self) -> [Tab, None]:
        """Get current active tab"""

        tab_handle = self.driver.current_window_handle
        return self.get(tab_handle)

    def get_blank_tab(self) -> Tab:
        """Get a blank tab to work with. Switchs to the newly created tab"""
        windows_before = self.driver.current_window_handle
        self.driver.execute_script("""window.open('{}');""".format("about:blank"))
        windows_after = self.driver.window_handles
        new_window = [x for x in windows_after if x != windows_before][-1]
        self.driver.switch_to.window(new_window)
        new_tab = self.create(new_window)
        new_tab.switch()
        return new_tab

    def open_new_tab(self, url):
        """Open a new tab with with a given URL"""

        blank_tab = self.get_blank_tab()
        blank_tab.start_url = url  # Not a recommended way to update object attributes
        blank_tab.switch()
        blank_tab.open(url)
        return blank_tab

    def all(self):
        """All tabs of the browser"""
        curr_tab = self.current_tab()
        all_tabs = [tab for tab in self._all_tabs.values()]
        if curr_tab:
            curr_tab.switch()
        return all_tabs

    def create(self, tab_handle):
        """Create a Tab object"""

        tab = Tab(session=self._session, tab_handle=tab_handle)
        self.add(tab)
        return tab

    def add(self, tab: Tab) -> None:
        """Add a tab to list of tabs"""
        self._all_tabs.update({tab.tab_handle: tab})

    def get(self, tab_handle) -> [Tab, None]:
        """get a Tab object given their handle/id"""
        return self._all_tabs.get(tab_handle, None)

    def exist(self, tab: Tab) -> bool:
        """Check if a tab exist"""

        if isinstance(tab, Tab):
            return tab.tab_handle in self._all_tabs.keys()

        raise Exception("Invalid type for tab.")

    def remove(self, tab: Tab) -> [Tab, None]:
        """Remove a tab from the list of tabs"""

        if isinstance(tab, Tab):
            return self._all_tabs.pop(tab.tab_handle, None)

        raise Exception("Invalid type for tab.")

    def first_tab(self) -> Tab | None:
        """First tab from the list of tabs of the browser"""
        try:
            _, tab = list(self._all_tabs.items())[0]
            return tab
        except:  # noqa
            return None

    def last_tab(self) -> Tab | None:
        """Last tab from the list of tabs of the browser"""
        try:
            _, tab = list(self._all_tabs.items())[-1]
            return tab
        except:  # noqa
            return None

    def switch_to_first_tab(self):
        """Switch to the first tab"""

        first_tab = self.first_tab()
        if first_tab and first_tab.is_alive and self.exist(first_tab):
            first_tab.switch()

    def switch_to_last_tab(self):
        """Switch to the last tab"""

        last_tab = self.last_tab()
        if last_tab and last_tab.is_alive and self.exist(last_tab):
            last_tab.switch()


class Browser:
    """
    A browser containing session and all the available tabs.
    Most users will just interact with (objects of) this class.
    """

    BROWSER_DRIVER_PATH_ENV = {
        "Chrome": "CHROME_DRIVER_PATH",
        "FireFox": "FIREFOX_DRIVER_PATH",
    }

    def __init__(
        self, name, driver_path=None, implicit_wait: int = 0, user_agent: str = "", headless=False
    ):
        self.name = name

        self.implicit_wait = implicit_wait or self._get_attr_or_env("IMPLICIT_WAIT_TIME")
        self.user_agent = user_agent or self._get_attr_or_env(
            "SELENIUM_USER_AGENT", raise_exception=False
        )
        self.driver_path = driver_path or self.get_driver_path()

        self._session = Session(
            name,
            driver_path,
            headless=headless,
            implicit_wait=self.implicit_wait,
            user_agent=self.user_agent,
        )
        self.tabs = TabManager(self._session)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_driver_path(self):
        """Get path of the driver from env or settings"""

        driver_env = self.BROWSER_DRIVER_PATH_ENV[self.name]
        return self._get_attr_or_env(driver_env)

    def get_current_tab(self):
        """get current tab from the list of the tabs"""
        return self.tabs.current_tab()

    def _get_attr_or_env(self, env, raise_exception=True):
        if hasattr(self, env):
            return getattr(self, env)

        driver_path = os.getenv(env, None)

        if driver_path:
            return os.getenv(env, None)

        if raise_exception:
            raise Exception(f"Please define {env} as class attribute or environment variable.")

    def open(self, url):
        """Starts a new tab with the given url at end of list of tabs."""
        self.tabs.switch_to_last_tab()
        curr_tab = self.tabs.open_new_tab(url)
        curr_tab.switch()
        return curr_tab

    def get_all_tabs(self) -> list:
        return self.tabs.all()

    def _remove_tab(self, tab: Tab):
        """For Internal Use Only:

        The order of operation is extremely important here. Practice extreme caution while editing this."""
        assert tab.is_alive is True
        assert self.tabs.exist(tab) is True
        tab.switch()
        self.tabs.remove(tab)
        self._session.driver.close()
        assert tab.is_alive is False
        assert self.tabs.exist(tab) is False

    def close_tab(self, tab: Tab):
        """Close a given tab"""
        if self.tabs.exist(tab):
            tab.switch()
            self._remove_tab(tab=tab)

            self.tabs.switch_to_last_tab()
            return True
        else:
            raise Exception("Tab does not exist.")

    def close(self):
        """Close browser"""
        self.tabs = {}
        self._session.close()


if __name__ == "__main__":
    chrome_driver = r"/Users/dayhatt/workspace/drivers/chromedriver"

    with Browser(name="Chrome", driver_path=chrome_driver, implicit_wait=10) as browser:
        google = browser.open("https://google.com")
        yahoo = browser.open("https://yahoo.com")
        bing = browser.open("https://bing.com")
        duck_duck = browser.open("https://duckduckgo.com/")

        print(browser.get_all_tabs())

        browser.close_tab(bing)
        print(browser.get_all_tabs())

        print(browser.get_current_tab())
        time.sleep(5)

        yahoo.switch()
        print(browser.get_current_tab())
        time.sleep(5)

        google.switch()
        print(browser.get_current_tab())
        time.sleep(5)

        browser.close_tab(yahoo)
        time.sleep(5)

        print(google.driver.title, google.title)

        print(browser.get_all_tabs())
