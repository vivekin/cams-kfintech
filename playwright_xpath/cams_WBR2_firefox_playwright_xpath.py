import csv
import time
import logging
import re
import configparser
from datetime import date, datetime

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# pip install playwright
# playwright install firefox

# ---------------------------------------------------------------------------
# XPath locators (unchanged from the Selenium version; Playwright accepts
# them with the "xpath=" prefix)
# ---------------------------------------------------------------------------
BASE = "/html/body/app-root/div"
MAILBACK = f"{BASE}/app-distributorlayout/div[2]/div/div/div[2]/div/app-distributmailback/div/div/div"
REPORTS = f"{BASE}/app-reports/div"
FORM = f"{REPORTS}/div[2]/div/div[3]/div[2]/div[2]/form/div/div"
PWD_FORM = f"{REPORTS}/div[2]/div/div[3]/div[2]/div[3]/div/div"

URL = "https://www.camsonline.com/Distributors/Service-Requests/Distributor-Mailback-Services/Request-Mailback"


def js_click(locator, timeout=10000):
    """Equivalent of Selenium's execute_script('arguments[0].click();', el)."""
    locator.wait_for(state="attached", timeout=timeout)
    locator.evaluate("el => el.click()")


def handle_cookie_and_popup(page):
    try:
        text = page.locator(
            "xpath=/html/body/div[5]/div[2]/div/mat-dialog-container/app-camsterms/div/mat-dialog-content/p[1]"
        ).text_content(timeout=5000)
        logging.info(f"Current page: {text}")
        disclaimer = page.locator(
            "xpath=/html/body/div[5]/div[2]/div/mat-dialog-container/app-camsterms/div/mat-dialog-content/div[1]/mat-radio-group/mat-radio-button[1]/label/span[1]/span[2]"
        )
        js_click(disclaimer, timeout=5000)
        page.locator(
            "xpath=/html/body/div[5]/div[2]/div/mat-dialog-container/app-camsterms/div/mat-dialog-content/div[2]/input"
        ).click(timeout=5000)
    except Exception as e:
        logging.error(f"Error handling Disclaimer pop-up : {e}")
    try:
        page.locator(
            "xpath=/html/body/div[2]/div[2]/div/mat-dialog-container/app-camsterms/div/div/mat-icon"
        ).click(timeout=5000)
    except Exception as e:
        logging.error(f"Error handling info pop-up : {e}")


def submit_email(page, email_addr):
    email = page.locator(f"xpath={MAILBACK}/form/div[1]/div/mat-form-field/div/div[1]/div[3]/input")
    email.fill(email_addr)
    submit = page.locator(f"xpath={MAILBACK}/form/div[2]/div/input")
    js_click(submit)


def process_user(page, user, config, status):
    email_addr, password = user

    logging.info("Closing pop-ups ...")
    handle_cookie_and_popup(page)

    heading = page.locator(f"xpath={MAILBACK}/div/div/h1")
    logging.info(f"Current page: {heading.text_content(timeout=10000)}")

    submit_email(page, email_addr)

    # end the previous session if one is open
    end_session = page.locator(f"xpath={MAILBACK}/div[2]/div/div/h4/a")
    try:
        end_session.wait_for(state="attached", timeout=5000)
        end_session.evaluate("el => el.click()")
        logging.info("Closed previously opened session.")
        submit_email(page, email_addr)
    except PlaywrightTimeoutError:
        pass  # no previous session

    # Select all funds
    dropdown = page.locator(
        f"xpath={REPORTS}/div[1]/div[1]/form/div/div[2]/mat-form-field/div/div[1]/div[3]/mat-select/div/div[2]"
    )
    js_click(dropdown, timeout=15000)
    fund = page.locator("xpath=//mat-option-select-all//mat-pseudo-checkbox")
    js_click(fund, timeout=15000)
    page.keyboard.press("Escape")

    # Wait for the loader to go away, then open the "Customer Service" tab
    page.wait_for_selector(".newloadersty", state="hidden", timeout=10000)
    page.locator(
        f"xpath={REPORTS}/div[2]/div/div[2]/div/mat-tab-group/mat-tab-header/div[2]/div/div/div[2]"
    ).click(timeout=10000)

    try:
        # WBR2. Investor Transactions for a Period
        js_click(page.locator(f"xpath={REPORTS}/div[2]/div/div[3]/div[1]/ul/li[2]"))

        # Output option
        js_click(page.locator(f"xpath={FORM}/div[3]/div[1]/mat-form-field/div/div[1]/div[3]/mat-select/div/div[2]"))
        # [last()] = the panel that was opened most recently (a previous panel may still be fading out)
        js_click(page.locator("xpath=(//div[@role='listbox'])[last()]//mat-option[7]/span"))

        # Delivery option
        js_click(page.locator(f"xpath={FORM}/div[3]/div[2]/mat-form-field/div/div[1]/div[3]/mat-select/div/div[2]"))
        js_click(page.locator("xpath=(//div[@role='listbox'])[last()]//mat-option[2]"))

        # Dates (inputs are readonly, so strip the attribute first)
        st_date = page.locator(f"xpath={FORM}/div[39]/div/div[1]/div[1]/mat-form-field/div/div[1]/div[3]/input")
        st_date.evaluate("el => el.removeAttribute('readonly')")
        st_date.fill(config["cams"]["start_date"])

        en_date = page.locator(f"xpath={FORM}/div[39]/div/div[1]/div[2]/mat-form-field/div/div[1]/div[3]/input")
        en_date.evaluate("el => el.removeAttribute('readonly')")
        en_date.fill(config["cams"]["end_date"])

        js_click(page.locator(f"xpath={FORM}/div[44]/div/input"))

        # Password + confirmation
        page.locator(
            f"xpath={PWD_FORM}/form/div/div/div[12]/div[1]/mat-form-field/div/div[1]/div[3]/input"
        ).fill(password)
        page.locator(
            f"xpath={PWD_FORM}/form/div/div/div[12]/div[2]/mat-form-field/div/div[1]/div[3]/input"
        ).fill(password)

        js_click(page.locator(f"xpath={PWD_FORM}/form/div/div/div[14]/div[2]/input[1]"))

        # Wait for the response message (replaces the fixed 15s sleep)
        submit_response = page.locator(f"xpath={PWD_FORM}/div[2]/p[1]")
        submit_response.wait_for(state="visible", timeout=30000)
        response_text = submit_response.text_content()
        logging.info(f"Mailback request submit response: {response_text}")

        cf = re.search("is .* and at", response_text)
        if cf:
            status[email_addr] = response_text[cf.span()[0] + 3 : cf.span()[1] - 7]
    except Exception as e:
        logging.error(f"Error : {e}")

    # Log out
    js_click(page.locator(f"xpath={REPORTS}/div[1]/div[2]/mat-icon"))
    logging.info(f"Processed user {email_addr}.\n")


def main():
    print("Script running ...")

    # get configs
    print("Fetching configs ...")
    config = configparser.ConfigParser()
    config.read("config.ini")

    # Configure the logger
    formatted_datetime = datetime.now().strftime("%Y_%m_%dT%H_%M_%S")
    logging.basicConfig(
        filename=f"cams_WBR2_playwright_{formatted_datetime}.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    start_time = time.perf_counter()
    logging.info(f"START - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - v.12 (playwright)")
    logging.info(f"Today's date: {date.today()}")
    logging.info(f"[config.ini] start_date: {config['cams']['start_date']}")
    logging.info(f"[config.ini] end_date: {config['cams']['end_date']}")

    status = {}

    # Fetching cams user list
    logging.info("Fetching cams user list ...\n")
    userlist = []
    with open("cams_users.csv", newline="") as csvfile:
        for row in csv.reader(csvfile, delimiter=","):
            userlist.append((row[0], row[1]))
            status[row[0]] = "-"

    user_count = len(userlist)

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        for idx, user in enumerate(userlist, start=1):
            logging.info(f"Processing {idx} of {user_count} users ...")
            print(f"Processing {idx} of {user_count} users ...")

            # A fresh context per user = clean cookies/storage
            # (replaces creating a new webdriver + delete_all_cookies)
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(10000)
            try:
                logging.info(f"Processing user {user[0]} ...")
                page.goto(URL)
                page.wait_for_load_state("networkidle")
                process_user(page, user, config, status)
            except Exception as e:
                logging.error(f"Error processing user {user[0]}: {e}\n")
            finally:
                context.close()

        browser.close()

    logging.info(f"END - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    elapsed_time = time.perf_counter() - start_time
    logging.info(f"Execution time: {elapsed_time:.2f} seconds\n")
    logging.info("############## SUMMARY ##############")
    for k, v in status.items():
        logging.info(f"{k}: {v}")
    logging.info("#####################################")
    print("Script exiting ...")


if __name__ == "__main__":
    main()
