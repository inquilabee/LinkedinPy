import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Session:
    BROWSER_DRIVER_FUNCTION = {
        "Chrome": webdriver.Chrome,
        "FireFox": webdriver.Firefox,
    }
    
    BROWSER_OPTION_FUNCTION = {
        "Chrome": ChromeOptions,
        "Firefox": FirefoxOptions
    }
    
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
            driver_options.add_argument('--disable-gpu')
            driver_options.add_argument('--disable-extensions')
            driver_options.add_argument("--no-sandbox")
            driver_options.add_argument("no-default-browser-check")
        
        driver = self.BROWSER_DRIVER_FUNCTION[self.browser](self.driver_path, options=driver_options)
        driver.implicitly_wait(self.implicit_wait)
        # driver.set_page_load_timeout(self.implicit_wait)
        
        return driver
    
    def _get_attr_or_env(self, env, raise_exception=True):
        if hasattr(self, env):
            return getattr(self, env)
        
        driver_path = os.getenv(env, None)
        
        if driver_path:
            return os.getenv(env, None)
        
        if raise_exception:
            raise Exception(
                f"Please define {env} as class attribute or environment variable."
            )
    
    def close(self):
        self.__del__()
    
    def __del__(self):
        self.driver.quit()


class Tab:
    def __init__(self, session, tab_handle):
        self._session = session
        self.tab_handle = tab_handle
    
    def __str__(self):
        return f"Tab(tab_handle={self.tab_handle} - title={self.title} - url={self.url}) "
    
    @property
    def title(self) -> str:
        return self.driver.title
    
    @property
    def driver(self) -> webdriver:
        if not self._session.driver.current_window_handle == self.tab_handle:
            self._session.driver.switch_to.window(self.tab_handle)
        return self._session.driver
    
    @property
    def url(self) -> str:
        return self.driver.current_url
    
    def switch(self) -> None:
        if not self.driver.current_window_handle == self.tab_handle:
            self.driver.switch_to.window(self.tab_handle)
    
    def open(self, url):
        self.driver.get(url)
        return self
    
    def click(self, element):
        try:
            self.switch()
            element.click()
        except Exception as e:
            try:
                self.driver.execute_script("arguments[0].click();", element)
            except Exception as e:
                pass
    
    def find_element(self, by, value, multiple=False):
        elements = self.driver.find_elements(by, value)
        
        if multiple:
            return elements
        else:
            if len(elements) > 1:
                raise Exception("Multiple elements found")
            else:
                return elements[0]
    
    def scroll(self, times=3, wait=1):
        
        for _ in range(times):
            html = self.driver.find_element_by_tag_name('html')
            html.send_keys(Keys.END)
            time.sleep(wait)
    
    def infinite_scroll(self, retries=5):
        
        for _ in range(max(1, retries)):
            try:
                last_height = 0
                
                while True:
                    self.scroll()
                    new_height = self.driver.execute_script("return document.documentElement.scrollHeight")
                    
                    if new_height == last_height:
                        break
                    
                    last_height = new_height
            except Exception as e:
                pass
    
    def wait_for_presence_of_element(self, element, wait):
        return WebDriverWait(self.driver, wait).until(
            EC.presence_of_element_located(element)
        )
    
    def wait_for_visibility_of_element(self, element, wait):
        return WebDriverWait(self.driver, wait).until(
            EC.visibility_of_element_located(element)
        )
    
    def wait_for_presence_and_visibility_of_element(self, element, wait):
        self.wait_for_visibility_of_element(element, wait)
        return self.wait_for_presence_of_element(element, wait)
    
    def wait_for_presence(self, by, key, wait):
        return WebDriverWait(self.driver, wait).until(
            EC.presence_of_element_located((by, key))
        )
    
    def wait_for_visibility(self, by, key, wait):
        return WebDriverWait(self.driver, wait).until(
            EC.visibility_of_element_located((by, key))
        )
    
    def wait_for_presence_and_visibility(self, by, key, wait):
        ele = self.wait_for_presence(by, key, wait)
        self.wait_for_visibility(by, key, wait)
        return ele
    
    def wait_until_staleness(self, element, wait=5):
        """Wait until the passed element is no longer present on the page"""
        WebDriverWait(self.driver, wait).until(
            EC.staleness_of(element)
        )
        
        time.sleep(0.5)


class TabManager:
    def __init__(self, session):
        self._session = session
        self._all_tabs = {}
    
    @property
    def driver(self):
        return self._session.driver
    
    def __len__(self):
        return len(self._all_tabs)
    
    def __del__(self):
        self._all_tabs = {}
    
    def __str__(self):
        return " ".join(self.all())
    
    def current_tab(self) -> [Tab, None]:
        tab_handle = self.driver.current_window_handle
        return self.get(tab_handle)
    
    def get_blank_tab(self) -> Tab:
        windows_before = self.driver.current_window_handle
        self.driver.execute_script('''window.open('{}');'''.format("about:blank"))
        windows_after = self.driver.window_handles
        new_window = [x for x in windows_after if x != windows_before][-1]
        self.driver.switch_to.window(new_window)
        new_tab = self.create(new_window)
        return new_tab
    
    def open_new_tab(self, url):
        blank_tab = self.get_blank_tab()
        blank_tab.open(url)
        return blank_tab
    
    def all(self):
        return [str(tab) for tab in self._all_tabs.values()]
    
    def create(self, tab_handle):
        tab = Tab(session=self._session, tab_handle=tab_handle)
        self.add(tab)
        return tab
    
    def add(self, tab: Tab) -> None:
        self._all_tabs.update({
            tab.tab_handle: tab
        })
    
    def get(self, tab_handle) -> [Tab, None]:
        return self._all_tabs.get(tab_handle, None)
    
    def exist(self, tab_handle) -> bool:
        return tab_handle in self._all_tabs
    
    def remove(self, tab_handle) -> [Tab, None]:
        return self._all_tabs.pop(tab_handle, None)


class Browser:
    BROWSER_DRIVER_PATH_ENV = {
        "Chrome": "CHROME_DRIVER_PATH",
        "FireFox": "FIREFOX_DRIVER_PATH",
    }
    
    def __init__(self, name, driver_path=None, implicit_wait: int = 0, user_agent: str = "", headless=False):
        self.name = name
        
        self.implicit_wait = implicit_wait or self._get_attr_or_env("IMPLICIT_WAIT_TIME")
        self.user_agent = user_agent or self._get_attr_or_env("SELENIUM_USER_AGENT", raise_exception=False)
        self.driver_path = driver_path or self.get_driver_path()
        
        self._session = Session(name, driver_path, headless=headless, implicit_wait=self.implicit_wait,
                                user_agent=self.user_agent)
        self.tabs = TabManager(self._session)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def get_driver_path(self):
        driver_env = self.BROWSER_DRIVER_PATH_ENV[self.name]
        return self._get_attr_or_env(driver_env)
    
    def get_current_tab(self):
        return self.tabs.current_tab()
    
    def _get_attr_or_env(self, env, raise_exception=True):
        if hasattr(self, env):
            return getattr(self, env)
        
        driver_path = os.getenv(env, None)
        
        if driver_path:
            return os.getenv(env, None)
        
        if raise_exception:
            raise Exception(
                f"Please define {env} as class attribute or environment variable."
            )
    
    def open(self, url):
        return self.tabs.open_new_tab(url)
    
    def get_all_tabs(self):
        return "\n".join(self.tabs.all())
    
    def close_tab(self, tab: Tab):
        tab.switch()
        self._session.driver.close()
        self.tabs.remove(tab.tab_handle)
    
    def close(self):
        self.tabs = {}
        self._session.close()


if __name__ == '__main__':
    chrome_driver = r"/Users/dayhatt/workspace/drivers/chromedriver"
    
    with Browser(name="Chrome", driver_path=chrome_driver, implicit_wait=10) as browser:
        google = browser.open("https://google.com")
        yahoo = browser.open("https://yahoo.com")
        bing = browser.open("https://bing.com")
        
        print(browser.get_current_tab())
        time.sleep(5)
        
        yahoo.switch()
        print(browser.get_current_tab())
        time.sleep(5)
        
        google.switch()
        print(browser.get_current_tab())
        time.sleep(5)
        
        browser.close_tab(bing)
        time.sleep(5)
        
        print(yahoo.driver.title)
        print(google.driver.title)
        
        print(browser.get_all_tabs())
