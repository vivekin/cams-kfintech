import csv
import time
import logging
import re
import sys
import configparser
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

print(sys.argv)
record_type = sys.argv[1]
browser_type = sys.argv[2]
if record_type not in ["WBR2","WBR9","WBR49","WBR77"]:
    print(f"Invalid record type: {record_type}, must be one of ['WBR2','WBR9','WBR49','WBR77']")
    sys.exit(1)
if browser_type not in ["chrome", "firefox"]:
    print(f"Invalid browser type: {browser_type}, must be one of ['chrome', 'firefox']")
    sys.exit(1)

URL = "https://www.camsonline.com/Distributors/Service-Requests/Distributor-Mailback-Services/Request-Mailback"

POPUP_CLOSE = "mat-dialog-container .close-icon"
SESSION_CLICK_HERE = "h4.clicksession a.clickhere"  # "session is still active... click here"
LOGOUT_ICON = "mat-icon.logout"


def close_popup_if_present(page):
    try:
        page.wait_for_selector(POPUP_CLOSE, state="visible", timeout=8000)
        page.click(POPUP_CLOSE)
        page.wait_for_selector(POPUP_CLOSE, state="detached", timeout=5000)
        print("Popup banner closed")
    except PlaywrightTimeoutError:
        print("No popup banner found, continuing")
 
 
def try_login(page, email):
    """Fill email and submit. Returns True if logged in, False if an old session blocked it."""
    page.get_by_placeholder("Email", exact=True).fill(email)
    print(f"Filled email: {email}")
 
    page.get_by_role("button", name="Submit", exact=True).click()
    print("Clicked submit")
 
    # Wait for whichever appears first: the logout icon (success) or the "click here" session link
    page.locator(f"{LOGOUT_ICON}, {SESSION_CLICK_HERE}").first.wait_for(
        state="visible", timeout=10000
    )
 
    if page.locator(SESSION_CLICK_HERE).is_visible():
        print("Previous session still active, ending it")
        page.click(SESSION_CLICK_HERE)

        page.wait_for_timeout(1000)
        # page.wait_for_selector(EMAIL_INPUT, state="visible", timeout=3000)
        page.get_by_placeholder("Email", exact=True).fill(email)
        print(f"Filled email: {email}")

        page.get_by_role("button", name="Submit", exact=True).click()
        print("Clicked submit")

def download_WBR2_report(page, config, extpass):
    page.get_by_role("tab", name="Customer Services", exact=True).click()
    page.locator("li", has_text="WBR2. Investor Transactions for a Period").click()

    fmt = page.locator('mat-select[formcontrolname="outputformat"]')
    fmt.click()
    
    panel = page.locator("div.mat-select-panel")
    panel.wait_for(state="visible")
    
    panel.get_by_role("option", name="Excel With Headers", exact=True).click()
    panel.wait_for(state="hidden", timeout=5000)
    
    delivery = page.locator('mat-select[formcontrolname="deliveryopt"]')
    delivery.click()
    
    panel = page.locator("div.mat-select-panel")
    panel.wait_for(state="visible")
    
    panel.get_by_role("option", name="Email a download link", exact=True).click()
    panel.wait_for(state="hidden", timeout=5000)

    # ---- From Date ----
    from_date = page.get_by_placeholder("From Date", exact=True)
    from_date.wait_for(state="visible")
    from_date.evaluate("el => el.removeAttribute('readonly')")
    from_date.fill(config["cams"]["start_date"])
    
    # ---- To Date ----
    to_date = page.get_by_placeholder("To Date", exact=True)
    to_date.wait_for(state="visible")
    to_date.evaluate("el => el.removeAttribute('readonly')")
    to_date.fill(config["cams"]["end_date"])
    
    # ---- Next ----
    page.wait_for_timeout(2000)
    page.get_by_role("button", name="Next", exact=True).click()
    
    # ---- Passwords (appear after Next) ----
    pwd = page.locator("#password")
    pwd.wait_for(state="visible", timeout=10000)
    pwd.fill(extpass)
    
    page.locator("#confirmPassword").fill(extpass)
    
    # ---- IMMEDIATE ----
    page.get_by_role("button", name="IMMEDIATE", exact=True).click()
    page.wait_for_timeout(3000)

    # ---- Read the confirmation message ----
    msg = page.locator("p", has_text="submitted").first
    msg.wait_for(state="visible", timeout=10000)
    
    text = " ".join(msg.inner_text().split())   # collapse newlines and extra spaces
    logging.info(f"Mailback request submit response: {text}")
    print("Result:", text)
    return text

def download_WBR9_report(page, config, extpass):
    page.get_by_role("tab", name="Proprietary data", exact=True).click()
    page.locator("li", has_text="WBR9. Investor Static details feed - CRMS Format").click()

    fmt = page.locator('mat-select[formcontrolname="outputformat"]')
    fmt.click()
    
    panel = page.locator("div.mat-select-panel")
    panel.wait_for(state="visible")
    
    panel.get_by_role("option", name="Excel With Headers", exact=True).click()
    panel.wait_for(state="hidden", timeout=5000)
    
    delivery = page.locator('mat-select[formcontrolname="deliveryopt"]')
    delivery.click()
    
    panel = page.locator("div.mat-select-panel")
    panel.wait_for(state="visible")
    
    panel.get_by_role("option", name="Email a download link", exact=True).click()
    panel.wait_for(state="hidden", timeout=5000)

    from_date = page.get_by_placeholder("From Date", exact=True)
    from_date.wait_for(state="visible")
    from_date.evaluate("el => el.removeAttribute('readonly')")
    from_date.fill("01-Jan-1995")

    # ---- Next ----
    page.wait_for_timeout(2000)
    page.get_by_role("button", name="Next", exact=True).click()
    
    # ---- Passwords (appear after Next) ----
    pwd = page.locator("#password")
    pwd.wait_for(state="visible", timeout=10000)
    pwd.fill(extpass)
    
    page.locator("#confirmPassword").fill(extpass)
    
    # ---- IMMEDIATE ----
    page.get_by_role("button", name="IMMEDIATE", exact=True).click()
    page.wait_for_timeout(3000)

    # ---- Read the confirmation message ----
    msg = page.locator("p", has_text="submitted").first
    msg.wait_for(state="visible", timeout=10000)
    
    text = " ".join(msg.inner_text().split())   # collapse newlines and extra spaces
    logging.info(f"Mailback request submit response: {text}")
    print("Result:", text)
    return text

def download_WBR49_report(page, config, extpass):
    page.get_by_role("tab", name="Grow your Business", exact=True).click()
    page.locator("li", has_text="WBR49. SIP/STP procured for the period").click()

    fmt = page.locator('mat-select[formcontrolname="outputformat"]')
    fmt.click()
    
    panel = page.locator("div.mat-select-panel")
    panel.wait_for(state="visible")
    
    panel.get_by_role("option", name="Excel With Headers", exact=True).click()
    panel.wait_for(state="hidden", timeout=5000)
    
    delivery = page.locator('mat-select[formcontrolname="deliveryopt"]')
    delivery.click()
    
    panel = page.locator("div.mat-select-panel")
    panel.wait_for(state="visible")
    
    panel.get_by_role("option", name="Email a download link", exact=True).click()
    panel.wait_for(state="hidden", timeout=5000)

    # ---- From Date ----
    from_date = page.get_by_placeholder("From Date", exact=True)
    from_date.wait_for(state="visible")
    from_date.evaluate("el => el.removeAttribute('readonly')")
    from_date.fill(config["cams"]["start_date"])
    
    # ---- To Date ----
    to_date = page.get_by_placeholder("To Date", exact=True)
    to_date.wait_for(state="visible")
    to_date.evaluate("el => el.removeAttribute('readonly')")
    to_date.fill(config["cams"]["end_date"])
    
    # ---- Next ----
    page.wait_for_timeout(2000)
    page.get_by_role("button", name="Next", exact=True).click()
    
    # ---- Passwords (appear after Next) ----
    pwd = page.locator("#password")
    pwd.wait_for(state="visible", timeout=10000)
    pwd.fill(extpass)
    
    page.locator("#confirmPassword").fill(extpass)
    
    # ---- IMMEDIATE ----
    page.get_by_role("button", name="IMMEDIATE", exact=True).click()
    page.wait_for_timeout(3000)

    # ---- Read the confirmation message ----
    msg = page.locator("p", has_text="submitted").first
    msg.wait_for(state="visible", timeout=10000)
    
    text = " ".join(msg.inner_text().split())   # collapse newlines and extra spaces
    logging.info(f"Mailback request submit response: {text}")
    print("Result:", text)
    return text

def download_WBR77_report(page, config, extpass):
    page.get_by_role("tab", name="Your earnings", exact=True).click()
    page.locator("li", has_text="WBR77. Consolidated Brokerage Payout Details").click()

    fmt = page.locator('mat-select[formcontrolname="outputformat"]')
    fmt.click()
    
    panel = page.locator("div.mat-select-panel")
    panel.wait_for(state="visible")
    
    panel.get_by_role("option", name="Excel With Headers", exact=True).click()
    panel.wait_for(state="hidden", timeout=5000)
    
    delivery = page.locator('mat-select[formcontrolname="deliveryopt"]')
    delivery.click()
    
    panel = page.locator("div.mat-select-panel")
    panel.wait_for(state="visible")
    
    panel.get_by_role("option", name="Email a download link", exact=True).click()
    panel.wait_for(state="hidden", timeout=5000)

    # ---- All checkbox ----
    all_cb = page.locator("mat-checkbox", has_text="All")
    all_cb.wait_for(state="visible")
    
    if all_cb.locator("input").get_attribute("aria-checked") != "true":
        all_cb.locator("label.mat-checkbox-layout").click()
        
    # ---- Select Month ----
    month = page.locator('mat-select[formcontrolname="monthon"]')
    month.click()
    
    panel = page.locator("div.mat-select-panel")
    panel.wait_for(state="visible")
    
    panel.get_by_role("option", name=config["cams"]["month_yr"], exact=True).click()
    panel.wait_for(state="hidden", timeout=5000)
    
    # ---- Next ----
    page.wait_for_timeout(2000)
    page.get_by_role("button", name="Next", exact=True).click()
    
    # ---- Passwords (appear after Next) ----
    pwd = page.locator("#password")
    pwd.wait_for(state="visible", timeout=10000)
    pwd.fill(extpass)
    
    page.locator("#confirmPassword").fill(extpass)
    
    # ---- IMMEDIATE ----
    page.get_by_role("button", name="IMMEDIATE", exact=True).click()
    page.wait_for_timeout(3000)

    # ---- Read the confirmation message ----
    msg = page.locator("p", has_text="submitted").first
    msg.wait_for(state="visible", timeout=10000)
    
    text = " ".join(msg.inner_text().split())   # collapse newlines and extra spaces
    logging.info(f"Mailback request submit response: {text}")
    print("Result:", text)
    return text

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
        filename=f"cams_report_{record_type}_{formatted_datetime}.log",  # Specify the log file name
        level=logging.INFO,  # Set the logging level to INFO
        format="%(asctime)s - %(levelname)s - %(message)s",  # Define the log message format
    )
    
    start_time = time.perf_counter()
    logging.info(f"START - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - v1.0")
    logging.info(f"Arguments - browser_type: {browser_type}, record_type: {record_type}")
    
    today = date.today()
    logging.info(f"Today's date: {formatted_datetime}")
    logging.info(f"[config.ini] start_date: {config['cams']['start_date']}")
    logging.info(f"[config.ini] end_date: {config['cams']['end_date']}")
    status={}

    # Fetching cams user list
    logging.info("Fetching cams user list ...\n")
    userlist = []
    with open("cams_users.csv", newline="") as csvfile:
        userreader = csv.reader(csvfile, delimiter=",")
        for row in userreader:
            userlist.append((row[0], row[1]))
            status[row[0]]='-'
    # print(userlist)
    
    user_count = len(userlist)
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False) if browser_type=="firefox" else p.chromium.launch(headless=False)
        # Process each user
        for user in userlist:
            try:
                logging.info(f"Processing {userlist.index(user)+1} of {user_count} users ...")
                print(f"Processing {userlist.index(user)+1} of {user_count} users ...")
        
                logging.info(f"Processing user {user[0]} ...")
                context = browser.new_context()
                page = context.new_page()
            
                page.goto(URL, wait_until="domcontentloaded")
                close_popup_if_present(page)
            
                try_login(page, user[0])

                fund = page.get_by_role("combobox", name="Mutual Fund", exact=True)
                fund.click()
                
                panel = page.locator("div.mat-select-panel")
                panel.wait_for(state="visible")
                page.wait_for_timeout(1000)
                
                all_opt = panel.locator("div.mat-option", has_text="All Mutual Funds")
                all_opt.wait_for(state="visible")
                all_opt.click()
                page.wait_for_timeout(1000)
                page.keyboard.press("Escape")
                panel.wait_for(state="hidden", timeout=5000)

                page.wait_for_timeout(3000)
                match record_type:
                    case "WBR2":
                        result=download_WBR2_report(page, config, user[1])
                        cf=re.search("is .* and at", result)
                        if cf:
                            status[user[0]]=result[cf.span()[0]+3:cf.span()[1]-7]
                    case "WBR9":
                        result=download_WBR9_report(page, config, user[1])
                        cf=re.search("is .* and at", result)
                        if cf:
                            status[user[0]]=result[cf.span()[0]+3:cf.span()[1]-7]
                    case "WBR49":
                        result=download_WBR49_report(page, config, user[1])
                        cf=re.search("is .* and at", result)
                        if cf:
                            status[user[0]]=result[cf.span()[0]+3:cf.span()[1]-7]
                    case "WBR77":
                        result=download_WBR77_report(page, config, user[1])
                        cf=re.search("is .* and at", result)
                        if cf:
                            status[user[0]]=result[cf.span()[0]+3:cf.span()[1]-7]

                # Click logout
                page.click(LOGOUT_ICON)
                print("Clicked logout")
            
                # Brief pause to see the result (remove when running headless)
                page.wait_for_timeout(3000)
            
                logging.info(f"Processed user {user[0]}.\n")
                
            except Exception as e:
                logging.error(f"Error processing user {user[0]}: {e}")
            finally:
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
