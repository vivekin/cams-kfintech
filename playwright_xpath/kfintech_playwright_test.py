import csv
import time
import logging
import re
import requests
import base64
from PIL import Image
import io
import configparser
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from ocrapi import solve_captcha

MAX_ATTEMPTS=10
URL = "https://dss.kfintech.com/dssweb/"


CANVAS_SEL = ".css-k008qs > canvas:nth-child(1)"
POPUP_CLOSE_SEL = ".css-19ekb6t"          # the svg inside it is clickable too: ".css-19ekb6t > svg:nth-child(1)"
DROPDOWN_SEL = ".css-vqps55 > div:nth-child(2) > div:nth-child(4)"
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
    canvas = page.locator(CANVAS_SEL)
    canvas.wait_for(state="visible")

    # Same as your Selenium JS: canvas.toDataURL(...) minus the "data:image/png;base64," prefix
    data_url = canvas.evaluate("el => el.toDataURL('image/png')")
    png_bytes = base64.b64decode(data_url.split(",", 1)[1])

    with open("temp_captcha.png", "wb") as f:
        f.write(png_bytes)

    return solve_captcha("temp_captcha.png")

def try_login(page, usern, password):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"Attempt {attempt}/{MAX_ATTEMPTS}")

        page.fill("#userName", usern)
        page.fill("#password", password)

        captcha_text = get_captcha_text(page)
        print("Captcha:", captcha_text)
        page.fill("#captcha", captcha_text)

        page.click('button:has-text("Sign In")')

        # If a snackbar appears, the login failed -> retry
        try:
            page.wait_for_selector(".MuiSnackbar-root", state="visible", timeout=3000)
            print("Snackbar:", page.inner_text(".MuiSnackbar-root"))
            page.wait_for_selector(".MuiSnackbar-root", state="hidden", timeout=10000)
            continue
        except PlaywrightTimeoutError:
            print("No snackbar, login looks successful")
            break
    else:
        print("Failed after max attempts")

def logout(page):
    page.click(DROPDOWN_SEL)
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
        filename=f"kfintech_playwright_test_{formatted_datetime}.log",  # Specify the log file name
        level=logging.INFO,  # Set the logging level to INFO
        format="%(asctime)s - %(levelname)s - %(message)s",  # Define the log message format
    )
    
    start_time = time.perf_counter()
    logging.info(f"START - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - v.12")
    
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
            userlist.append((row[0], row[1]))
            status[row[0]]='-'
    # print(userlist)
    
    user_count = len(userlist)
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        # Process each user
        for user in userlist:
            try:
                logging.info(f"Processing {userlist.index(user)+1} of {user_count} users ...")
                print(f"Processing {userlist.index(user)+1} of {user_count} users ...")
        
                logging.info(f"Processing user {user[0]} ...")

                page.goto(URL, wait_until="domcontentloaded")
                try_login(page, user[0], user[1])
            
                close_popup_if_present(page)   # banner usually appears after login


                page.wait_for_timeout(3000)
                logout(page)
 
           
                # Brief pause to see the result (remove when running headless)
                page.wait_for_timeout(3000)
            
                status[user[0]]="success"
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
