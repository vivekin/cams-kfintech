import csv
import time
import logging
import re
import requests
import base64
import sys
from PIL import Image
import io
import configparser
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from ocrapi import solve_captcha

print(sys.argv)
record_type = sys.argv[1]
browser_type = sys.argv[2]
if record_type not in ["MFSD201","MFSD205","MFSD211","MFSD230","MFSD262"]:
    print(f"Invalid record type: {record_type}, must be one of ['MFSD201','MFSD205','MFSD211','MFSD230','MFSD262']")
    sys.exit(1)
if browser_type not in ["chrome", "firefox"]:
    print(f"Invalid browser type: {browser_type}, must be one of ['chrome', 'firefox']")
    sys.exit(1)

MAX_ATTEMPTS=10
URL = "https://dss.kfintech.com/dssweb/"


POPUP_CLOSE_SEL = ".css-19ekb6t"
USER_MENU = 'div:has(> svg[data-testid="AccountCircleRoundedIcon"]):visible'
LOGOUT_SEL = 'a.MuiButtonBase-root:has-text("Logout")'

def close_popup_if_present(page):
    """Close the popup banner only if it shows up."""
    popup = page.locator(POPUP_CLOSE_SEL)
    try:
        popup.first.wait_for(state="visible", timeout=8000)
        popup.first.click()
        print("Popup banner closed")
    except PlaywrightTimeoutError:
        print("No popup banner")
 
def get_captcha_text(page) -> str:
    canvas = page.locator("form canvas").first
    canvas.wait_for(state="visible")

    data_url = canvas.evaluate("el => el.toDataURL('image/png')")
    png_bytes = base64.b64decode(data_url.split(",", 1)[1])

    with open("temp_captcha.png", "wb") as f:
        f.write(png_bytes)

    return solve_captcha("temp_captcha.png")

def try_login(page, usern, password) -> bool:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"Attempt {attempt}/{MAX_ATTEMPTS}")

        page.fill("#userName", usern)
        page.fill("#password", password)

        captcha_text = get_captcha_text(page)
        if captcha_text== "" or captcha_text is None:
            captcha_text='empty'
        print("Captcha:", captcha_text)
        page.fill("#captcha", captcha_text)

        page.click('button:has-text("Sign In")')
        page.wait_for_timeout(500)

        # If a snackbar appears, the login failed -> retry
        try:
            page.wait_for_selector(".MuiSnackbar-root", state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            print("No snackbar, login looks successful")
            return True

        print("Snackbar:", page.inner_text(".MuiSnackbar-root"))
    print("Failed after max attempts")
    return False

def fill_readonly(locator, value):
    locator.wait_for(state="visible")
    locator.evaluate("el => el.removeAttribute('readonly')")
    locator.fill(value)

def download_MFSD201_report(page, config, extpass):
    cfg = config["kfintech"]

    # Navigate to the report
    page.locator("p", has_text="Procurement Reports").first.click()
    page.get_by_text("MFSD201").click()   # "MFSD201 -Transaction Report"

    # Fund dropdown -> first entry
    combo = page.get_by_role("combobox", name="Select Fund", exact=True)
    combo.click()
    menu = page.locator("#menu-")
    menu.wait_for(state="visible")
    page.wait_for_timeout(1000)
    
    # first li that has a span
    menu.locator("li span").first.click()
    page.keyboard.press("Escape")
    # make sure the menu is really gone before touching anything else
    try:
        menu.wait_for(state="hidden", timeout=5000)
    except PlaywrightTimeoutError:
        page.keyboard.press("Escape")
        menu.wait_for(state="hidden", timeout=5000)

    # Dates
    fill_readonly(page.get_by_label("From Date"), cfg["start_date"])
    fill_readonly(page.get_by_label("To Date"), cfg["end_date"])

    # Radios
    page.get_by_label("Without Split").check()
    page.get_by_label("CSV", exact=True).check()

    # Tick every checkbox under the "Email IDs" fieldset
    checkboxes = page.locator("fieldset", has_text="Email IDs").locator("input[type='checkbox']")
    for i in range(checkboxes.count()):
        checkboxes.nth(i).check()

    # Self extraction password
    # page.get_by_label("Self Extraction Password", exact=True).fill(extpass)
    # page.get_by_label("Self Extraction Confirm Password", exact=True).fill(extpass)
    pw_inputs = page.locator("form input[type='password']")
    pw_inputs.first.wait_for(state="visible")
    pw_inputs.nth(0).fill(extpass)
    pw_inputs.nth(1).fill(extpass)

    # Submit
    page.wait_for_timeout(2000)
    page.get_by_role("button", name="Submit").click()
    page.wait_for_timeout(2000)

    # Read the result message
    msg = page.get_by_text("successfully registered").first
    msg.wait_for(state="visible", timeout=10000)
    text = msg.inner_text()
    logging.info(f"Mailback request submit response: {text}")
    print("Result:", text)
    return text

def download_MFSD205_report(page, config, extpass):
    cfg = config["kfintech"]
    
    # Navigate to the report
    page.locator("p", has_text="Brokerage Reports").first.click()
    page.get_by_text("MFSD205").click()   # "MFSD205 - Brokerage Reports"

    for label_id in ("select-funds-label","select-schemes-label","select-brok-type-label","select-sub-brok-type-label"):
        combo = page.locator(f'[role="combobox"][aria-labelledby="{label_id}"]:not([aria-disabled="true"])')
        combo.wait_for(state="visible", timeout=10000)
        combo.click()
    
        menu = page.locator("#menu-")
        menu.wait_for(state="visible")
        page.wait_for_timeout(1000)
    
        menu.locator("li span").first.click()
        page.wait_for_timeout(1000)
    
        page.keyboard.press("Escape")
        menu.wait_for(state="hidden", timeout=5000)
        page.wait_for_timeout(5000)
    
    # Dates
    fill_readonly(page.get_by_label("From Month"), cfg["start_month"])
    fill_readonly(page.get_by_label("To Month"), cfg["end_month"])


    # Radios
    page.get_by_label("CSV", exact=True).check()
    
    # Tick every checkbox under the "I want this Report for :" fieldset
    checkboxes = page.locator("fieldset", has_text="I want this Report for :").locator("input[type='checkbox']")
    for i in range(checkboxes.count()):
        checkboxes.nth(i).check()

    pw_inputs = page.locator("form input[type='password']")
    pw_inputs.first.wait_for(state="visible")
    pw_inputs.nth(0).fill(extpass)
    pw_inputs.nth(1).fill(extpass)

    # Submit
    page.wait_for_timeout(2000)
    page.get_by_role("button", name="Submit").click()
    page.wait_for_timeout(2000)
    
    # Read the result message
    msg = page.get_by_text("successfully registered").first
    msg.wait_for(state="visible", timeout=10000)
    text = msg.inner_text()
    logging.info(f"Mailback request submit response: {text}")
    print("Result:", text)
    return text

def download_MFSD211_report(page, config, extpass):
    cfg = config["kfintech"]
    
    # Navigate to the report
    page.locator("p", has_text="Procurement Reports").first.click()
    page.get_by_text("MFSD211").click()   # "MFSD211-Investor Master Information"
    
    # Fund dropdown -> first entry
    combo = page.get_by_role("combobox", name="Funds", exact=True)
    combo.click()
    menu = page.locator("#menu-")
    menu.wait_for(state="visible")
    page.wait_for_timeout(1000)
    
    # first li that has a span
    menu.locator("li span").first.click()
    page.keyboard.press("Escape")
    # make sure the menu is really gone before touching anything else
    try:
        menu.wait_for(state="hidden", timeout=5000)
    except PlaywrightTimeoutError:
        page.keyboard.press("Escape")
        menu.wait_for(state="hidden", timeout=5000)
        
    fill_readonly(page.get_by_label("From Date"), '01/01/1994')

    # Radios
    page.get_by_label("CSV", exact=True).check()
        
    # Tick every checkbox under the "I Want this Report for" fieldset
    checkboxes = page.locator("fieldset", has_text="I Want this Report for").locator("input[type='checkbox']")
    for i in range(checkboxes.count()):
        checkboxes.nth(i).check()

    pw_inputs = page.locator("form input[type='password']")
    pw_inputs.first.wait_for(state="visible")
    pw_inputs.nth(0).fill(extpass)
    pw_inputs.nth(1).fill(extpass)

    # Submit
    page.wait_for_timeout(2000)
    page.get_by_role("button", name="Submit").click()
    page.wait_for_timeout(2000)
    
    # Read the result message
    msg = page.get_by_text("successfully registered").first
    msg.wait_for(state="visible", timeout=10000)
    text = msg.inner_text()
    logging.info(f"Mailback request submit response: {text}")
    print("Result:", text)
    return text

def download_MFSD230_report(page, config, extpass):
    cfg = config["kfintech"]
    
    # Navigate to the report
    page.locator("p", has_text="SIP/STP Report").first.click()
    page.get_by_text("MFSD230").click()   # "MFSD230-SIP/STP Report"

    # Fund dropdown -> first entry
    combo = page.get_by_role("combobox", name="Funds", exact=True)
    combo.click()
    menu = page.locator("#menu-")
    menu.wait_for(state="visible")
    page.wait_for_timeout(1000)
    
    # first li that has a span
    menu.locator("li span").first.click()
    page.keyboard.press("Escape")
    # make sure the menu is really gone before touching anything else
    try:
        menu.wait_for(state="hidden", timeout=5000)
    except PlaywrightTimeoutError:
        page.keyboard.press("Escape")
        menu.wait_for(state="hidden", timeout=5000)

    # Dates
    fill_readonly(page.get_by_label("From Date"), cfg["start_date"])
    fill_readonly(page.get_by_label("To Date"), cfg["end_date"])


    # Radios
    page.get_by_label("CSV", exact=True).check()
    
    # Tick every checkbox under the "I want this Report for" fieldset
    checkboxes = page.locator("fieldset", has_text="I want this Report for").locator("input[type='checkbox']")
    for i in range(checkboxes.count()):
        checkboxes.nth(i).check()
    
    pw_inputs = page.locator("form input[type='password']")
    pw_inputs.first.wait_for(state="visible")
    pw_inputs.nth(0).fill(extpass)
    pw_inputs.nth(1).fill(extpass)

    # Submit
    page.wait_for_timeout(2000)
    page.get_by_role("button", name="Submit").click()
    page.wait_for_timeout(2000)
    
    # Read the result message
    msg = page.get_by_text("successfully registered").first
    msg.wait_for(state="visible", timeout=10000)
    text = msg.inner_text()
    logging.info(f"Mailback request submit response: {text}")
    print("Result:", text)
    return text

def download_MFSD262_report(page, config, extpass):
    cfg = config["kfintech"]
    
    # Navigate to the report
    page.locator("p", has_text="Special Reports").first.click()
    page.get_by_text("MFSD262").click()   # "MFSD262-PAN Level KYC Report"

    # Fund dropdown -> first entry
    combo = page.get_by_role("combobox", name="Funds", exact=True)
    combo.click()
    menu = page.locator("#menu-")
    menu.wait_for(state="visible")
    page.wait_for_timeout(1000)
    
    # first li that has a span
    menu.locator("li span").first.click()
    page.keyboard.press("Escape")
    # make sure the menu is really gone before touching anything else
    try:
        menu.wait_for(state="hidden", timeout=5000)
    except PlaywrightTimeoutError:
        page.keyboard.press("Escape")
        menu.wait_for(state="hidden", timeout=5000)

    # Radios
    page.get_by_label("CSV", exact=True).check()
    
    # Tick every checkbox under the "I want this Report for" fieldset
    checkboxes = page.locator("fieldset", has_text="I want this Report for").locator("input[type='checkbox']")
    for i in range(checkboxes.count()):
        checkboxes.nth(i).check()
    
    pw_inputs = page.locator("form input[type='password']")
    pw_inputs.first.wait_for(state="visible")
    pw_inputs.nth(0).fill(extpass)
    pw_inputs.nth(1).fill(extpass)

    # Submit
    page.wait_for_timeout(2000)
    page.get_by_role("button", name="Submit").click()
    page.wait_for_timeout(2000)

    # Read the result message
    msg = page.get_by_text("successfully registered").first
    msg.wait_for(state="visible", timeout=10000)
    text = msg.inner_text()
    logging.info(f"Mailback request submit response: {text}")
    print("Result:", text)
    return text

def logout(page):
    page.locator(USER_MENU).first.click()
    page.wait_for_selector(LOGOUT_SEL, state="visible")
    page.click(LOGOUT_SEL)
    print("Logged out")
  
def main():
    print("Script running ...")

    # get configs
    print("Fetching configs ...")
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Configure the logger
    datetime_object = datetime.now()
    formatted_datetime = datetime_object.strftime("%Y_%m_%dT%H_%M_%S")
    logging.basicConfig(
        filename=f"kfintech_report_{record_type}_{formatted_datetime}.log",  # Specify the log file name
        level=logging.INFO,  # Set the logging level to INFO
        format="%(asctime)s - %(levelname)s - %(message)s",  # Define the log message format
    )
    
    start_time = time.perf_counter()
    logging.info(f"START - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - v1.0")
    logging.info(f"Arguments - browser_type: {browser_type}, record_type: {record_type}")
    
    today = date.today()
    logging.info(f"Today's date: {formatted_datetime}")
    logging.info(f"[config.ini] start_date: {config['kfintech']['start_date']}")
    logging.info(f"[config.ini] end_date: {config['kfintech']['end_date']}")
    status={}

    # Fetching kfintech user list
    logging.info("Fetching kfintech user list ...\n")
    userlist = []
    with open("kfintech_users.csv", newline="") as csvfile:
        userreader = csv.reader(csvfile, delimiter=",")
        for row in userreader:
            userlist.append((row[0], row[1], row[2]))
            status[row[0]]='-'
    
    user_count = len(userlist)
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False) if browser_type=="firefox" else p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        # page.on("response", lambda r: r.status >= 400 and
        # print(f"[{r.status}] {r.request.method} {r.url}"))
        # page.on("request", lambda r: r.url == URL and print(r.headers))
        # page.on("requestfailed", lambda r: print("FAILED", r.url, r.failure))

        # Process each user
        for user in userlist:
            try:
                logging.info(f"Processing {userlist.index(user)+1} of {user_count} users ...")
                print(f"Processing {userlist.index(user)+1} of {user_count} users ...")
        
                logging.info(f"Processing user {user[0]} ...")

                page.goto(URL, wait_until="domcontentloaded")

                ## TO DO After max attempts continue to next user
                login_success = try_login(page, user[0], user[1])
                if not login_success:
                    logging.error(f"Login failed for user {user[0]}")
                    continue
            
                page.wait_for_timeout(2000)
                close_popup_if_present(page)   # banner usually appears after login

                mailback = page.locator(".MuiDrawer-root").get_by_role("link", name="Mail Back Reports")
                mailback.click()

                page.wait_for_timeout(1000)
                match record_type:
                    case "MFSD201":
                        result=download_MFSD201_report(page, config, user[2])
                        kf=re.search(r"reference number (\w+)", result)
                        if kf:
                            status[user[0]]=kf.group(1)
                    case "MFSD205":
                        result=download_MFSD205_report(page, config, user[2])
                        kf=re.search(r"reference number (\w+)", result)
                        if kf:
                            status[user[0]]=kf.group(1)
                    case "MFSD211":
                        result=download_MFSD211_report(page, config, user[2])
                        kf=re.search(r"reference number (\w+)", result)
                        if kf:
                            status[user[0]]=kf.group(1)
                    case "MFSD230":
                        result=download_MFSD230_report(page, config, user[2])
                        kf=re.search(r"reference number (\w+)", result)
                        if kf:
                            status[user[0]]=kf.group(1)
                    case "MFSD262":
                        result=download_MFSD262_report(page, config, user[2])
                        kf=re.search(r"reference number (\w+)", result)
                        if kf:
                            status[user[0]]=kf.group(1)
                    
                page.wait_for_timeout(2000)
                logout(page)
 
           
                # Brief pause to see the result (remove when running headless)
                page.wait_for_timeout(3000)
            
                logging.info(f"Processed user {user[0]}.\n")
                
            except Exception as e:
                logging.error(f"Error processing user {user[0]}: {e}")
        context.close()
        browser.close()

    logging.info(f"END - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    logging.info(f"Execution time: {elapsed_time:.2f} seconds\n")
    logging.info("############## SUMMARY ##############")
    for i in status.keys():
        logging.info(f"{i}: {status[i]}")
    logging.info("#####################################")
    print("Script exiting ...")


if __name__ == "__main__":
    main()