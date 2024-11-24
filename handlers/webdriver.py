import time, json
from urllib.parse import parse_qs
from seleniumwire import webdriver
from seleniumwire.utils import decode as sw_decode
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = None

def wait_for_request(driver, url_part, timeout=30):
    end_time = time.time() + timeout
    while time.time() < end_time:
        for request in driver.requests:
            if request.response and url_part in request.url:
                return request
        time.sleep(1)
    print("Did not receive response in time.")
    raise SystemExit

def login(use_cookies=False):
    """Setup Chrome webdriver and log-in to Instagram."""
    global driver

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    #options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    print("Logging in to Instagram...")
    driver.get("https://www.instagram.com")

    if use_cookies:
        inject_cookies(driver)
    else:
        WebDriverWait(driver, 30).until(EC.invisibility_of_element((By.XPATH, "//div[@class='splash-screen']")))
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='_a9-- _ap36 _a9_0']"))).click() # Accept cookies
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='username']"))).send_keys("") # Username
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='password']"))).send_keys(open("credentials.txt", "r").read()) # Password
        time.sleep(3)
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click() # Submit
        WebDriverWait(driver, 120).until(EC.url_contains("onetap"))

    print("Login successful")
    return driver

def inject_cookies(driver):
    """Setup Chrome webdriver and inject Instagram account cookies."""
    print("Adding cookies...")
    driver.get("https://www.instagram.com")

    driver.add_cookie({"name": "csrftoken", "value": ""})
    driver.add_cookie({"name": "datr", "value": ""})
    driver.add_cookie({"name": "ds_user_id", "value": ""})
    driver.add_cookie({"name": "ig_did", "value": ""})
    driver.add_cookie({"name": "ig_direct_region_hint", "value": ""})
    driver.add_cookie({"name": "mid", "value": ""})
    driver.add_cookie({"name": "rur", "value": ""})
    driver.add_cookie({"name": "sessionid", "value": ""})
    driver.add_cookie({"name": "wd", "value": ""})

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