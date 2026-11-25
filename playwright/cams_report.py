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

URL = "https://www.camsonline.com/Distributors/Service-Requests/Distributor-Mailback-Services/Request-Mailback"

POPUP_CLOSE = "mat-dialog-container .close-icon"
EMAIL_INPUT = "#mat-input-0"
SUBMIT_BTN = "input.check-now-btn"
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
    page.wait_for_selector(EMAIL_INPUT, state="visible", timeout=30000)
    page.fill(EMAIL_INPUT, email)
    print(f"Filled email: {email}")
 
    page.click(SUBMIT_BTN)
    print("Clicked submit")
 
    # Wait for whichever appears first: the logout icon (success) or the "click here" session link
    page.locator(f"{LOGOUT_ICON}, {SESSION_CLICK_HERE}").first.wait_for(
        state="visible", timeout=60000
    )
 
    if page.locator(SESSION_CLICK_HERE).is_visible():
        print("Previous session still active, ending it")
        page.click(SESSION_CLICK_HERE)

        page.wait_for_selector(EMAIL_INPUT, state="visible", timeout=30000)
        page.fill(EMAIL_INPUT, email)
        print(f"Filled email: {email}")

        page.click(SUBMIT_BTN)
        print("Clicked submit")

def download_WBR2_report(page, config, extpass):
    pass

def download_WBR9_report(page, config, extpass):
    pass

def download_WBR49_report(page, config, extpass):
    pass

def download_WBR77_report(page, config, extpass):
    pass

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
    logging.info(f"START - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - v.12")
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
        browser = p.firefox.launch(headless=False)
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
                            
                page.wait_for_timeout(3000)
                match record_type:
                    case "WBR2":
                        result=download_WBR2_report(page, config, user[1])
                    case "WBR9":
                        result=download_WBR9_report(page, config, user[1])
                    case "WBR49":
                        result=download_WBR49_report(page, config, user[1])
                    case "WBR77":
                        result=download_WBR77_report(page, config, user[1])

                # Click logout
                page.click(LOGOUT_ICON)
                print("Clicked logout")
            
                # Brief pause to see the result (remove when running headless)
                page.wait_for_timeout(3000)
            
                status[user[0]]="success"
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
