from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import tempfile


def auth(auth_url: str, auth_cookie_list:dict[str]) -> dict[str]:
    def get_cookie_by_path(driver, key, path):
        cookies = driver.get_cookies()
        for cookie in cookies:
            if (cookie.get("name") == key) and (cookie.get("path") == path):
                return cookie
        return None

    options = webdriver.FirefoxOptions()
    options.add_argument("-profile")
    options.add_argument(tempfile.mkdtemp())
    options.add_argument("-ssb")

    try:
        driver = webdriver.Firefox(options=options)
        driver.get(auth_url)
        
        WebDriverWait(driver, 30).until(
            lambda d: all(
                [
                    (get_cookie_by_path(d, key, value) is not None)
                    for key, value in auth_cookie_list.items()
                ]
            )
        )

        return {
            key: c["value"]
            for key, val in auth_cookie_list.items()
            for c in driver.get_cookies()
            if c["name"] == key and c["path"] == val
        }
    finally:
        driver.quit()
