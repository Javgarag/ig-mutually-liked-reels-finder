import time, configparser
from urllib.parse import parse_qs
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = None
config = configparser.ConfigParser()
config.read("config.ini")

def wait_for_request(driver, url_part, timeout=30):
    end_time = time.time() + timeout
    while time.time() < end_time:
        for request in driver.requests:
            if request.response and url_part in request.url:
                return request
        time.sleep(1)
    print("Did not receive response in time.")
    raise SystemExit

def login():
    """Setup Chrome webdriver and log-in to Instagram."""
    global driver
    use_cookies = not config.getboolean("Login", "should_use")

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    driver.get("https://www.instagram.com")

    if use_cookies:
        inject_cookies(driver)
    else:
        print("Logging in to Instagram...")

        WebDriverWait(driver, 30).until(EC.invisibility_of_element((By.XPATH, "//div[@class='splash-screen']")))
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='_a9-- _ap36 _a9_0']"))).click() # Accept cookies
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='username']"))).send_keys(config.get("Login", "username", raw = True)) # Username
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='password']"))).send_keys(config.get("Login", "password", raw = True)) # Password
        time.sleep(3)
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click() # Submit
        WebDriverWait(driver, 120).until(EC.url_contains("onetap"))

    print("Login successful")
    return driver

def inject_cookies(driver):
    """Setup Chrome webdriver and inject Instagram account cookies."""
    print("Adding cookies to webdriver...")
    driver.get("https://www.instagram.com")

    driver.add_cookie({"name": "csrftoken", "value": config.get("Cookies", "csrftoken", raw=True)})
    driver.add_cookie({"name": "datr", "value": config.get("Cookies", "datr", raw=True)})
    driver.add_cookie({"name": "ds_user_id", "value": config.get("Cookies", "ds_user_id", raw=True)})
    driver.add_cookie({"name": "ig_did", "value": config.get("Cookies", "ig_did", raw=True)})
    driver.add_cookie({"name": "ig_direct_region_hint", "value": config.get("Cookies", "ig_direct_region_hint", raw=True)})
    driver.add_cookie({"name": "mid", "value": config.get("Cookies", "mid", raw=True)})
    driver.add_cookie({"name": "rur", "value": config.get("Cookies", "rur", raw=True)})
    driver.add_cookie({"name": "sessionid", "value": config.get("Cookies", "sessionid", raw=True)})
    driver.add_cookie({"name": "wd", "value": config.get("Cookies", "wd", raw=True)})

    print("Cookies added")

def get_request_info():
    """Navigates to /your_activity/interactions/likes/ and waits for a request to com.instagram.privacy.activity_center.liked_media_screen, then returns the request headers and parameters, which can be reused for all other requests."""
    if not driver:
        print("ERROR: Login into Instagram before performing first HTTP request.")
        raise SystemExit
    
    print("Getting request headers/cookies...")
    driver.get("https://www.instagram.com/your_activity/interactions/likes/")

    request = wait_for_request(driver, "com.instagram.privacy.activity_center.liked_media_screen")

    print("Successfully got request headers/cookies")
    return request.headers, request.params, parse_qs(request.body.decode("utf8"))