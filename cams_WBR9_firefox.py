import csv
import time
import logging
import re
import configparser
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

def handle_cookie_and_popup(browser):
    try:
        page = browser.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/mat-dialog-container/app-camsterms/div/mat-dialog-content/p[1]")
        logging.info(f"Current page: {page.text}")
        disclaimer = browser.find_element(By.XPATH,'/html/body/div[1]/div[2]/div/mat-dialog-container/app-camsterms/div/mat-dialog-content/div[1]/mat-radio-group/mat-radio-button[1]/label/span[1]/span[2]',)
        browser.execute_script("arguments[0].click();", disclaimer)
        disclaimer_submit = browser.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/mat-dialog-container/app-camsterms/div/mat-dialog-content/div[2]/input",)
        time.sleep(1)
        disclaimer_submit.click()
    except Exception as e:
        logging.error(f"Error handling Disclamer pop-up : {e}")
    try:
        time.sleep(2)
        info = browser.find_element(By.XPATH,"/html/body/div[1]/div[2]/div/mat-dialog-container/app-camsterms/div/div/mat-icon",)
        info.click()
    except Exception as e:
        logging.error(f"Error handling info pop-up : {e}")

print("Script running ...")

# get configs
print("Fetching configs ...")
config = configparser.ConfigParser()
config.read('config.ini')

# Configure the logger
datetime_object = datetime.now()
formatted_datetime = datetime_object.strftime("%Y_%m_%dT%H_%M_%S")
logging.basicConfig(
    filename=f"cams_WBR9_firefox_{formatted_datetime}.log",  # Specify the log file name
    level=logging.INFO,  # Set the logging level to INFO
    format="%(asctime)s - %(levelname)s - %(message)s",  # Define the log message format
)

start_time = time.perf_counter()
logging.info(f"START - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - v.7")

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
# Process each user
for user in userlist:
    logging.info(f"Processing {userlist.index(user)+1} of {user_count} users ...")
    print(f"Processing {userlist.index(user)+1} of {user_count} users ...")
    # Creating an instance webdriver
    browser = webdriver.Firefox()
    browser.get("https://www.camsonline.com/Distributors/Service-Requests/Distributor-Mailback-Services/Request-Mailback")
    time.sleep(5)
    try:
        logging.info(f"Processing user {user[0]} ...")
        logging.info("Closing pop-ups ...")
        handle_cookie_and_popup(browser=browser)
        page = browser.find_element(By.XPATH, "/html/body/app-root/div/app-distributorlayout/div[2]/div/div/div[1]/ul/li[1]/p")
        logging.info(f"Current page: {page.text}")
        email=browser.find_element(By.XPATH, "/html/body/app-root/div/app-distributorlayout/div[2]/div/div/div[2]/div/app-distributmailback/div/div/div/form/div[1]/div/mat-form-field/div/div[1]/div[3]/input")
        email.clear()
        email.send_keys(user[0])
        time.sleep(2)
        submit=browser.find_element(By.XPATH, "/html/body/app-root/div/app-distributorlayout/div[2]/div/div/div[2]/div/app-distributmailback/div/div/div/form/div[2]/div/input")
        time.sleep(0.5)
        browser.execute_script("arguments[0].click();", submit)
        time.sleep(5)
        try:
            # end the previous session if open
            end_session=browser.find_element(By.XPATH, "/html/body/app-root/div/app-distributorlayout/div[2]/div/div/div[2]/div/app-distributmailback/div/div/div/div[2]/div/div/h4/a")
            browser.execute_script("arguments[0].click();", end_session)
            time.sleep(2)
        except Exception:
            pass
        else:
            logging.info("Closed previously opened session.")
            email=browser.find_element(By.XPATH, "/html/body/app-root/div/app-distributorlayout/div[2]/div/div/div[2]/div/app-distributmailback/div/div/div/form/div[1]/div/mat-form-field/div/div[1]/div[3]/input")
            email.clear()
            email.send_keys(user[0])
            time.sleep(2)
            submit=browser.find_element(By.XPATH, "/html/body/app-root/div/app-distributorlayout/div[2]/div/div/div[2]/div/app-distributmailback/div/div/div/form/div[2]/div/input")
            time.sleep(0.5)
            browser.execute_script("arguments[0].click();", submit)
            time.sleep(3)
        time.sleep(2)
        dropdown=browser.find_element(By.XPATH, "/html/body/app-root/div/app-reports/div/div[1]/div[1]/form/div/div[2]/mat-form-field/div/div[1]/div[3]/mat-select/div/div[2]")
        browser.execute_script("arguments[0].click();", dropdown)
        time.sleep(5)
        fund=browser.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div/mat-option-select-all/div/mat-pseudo-checkbox")
        browser.execute_script("arguments[0].click();", fund)
        time.sleep(4)
        webdriver.ActionChains(browser).send_keys(Keys.ESCAPE).perform()

        time.sleep(2)
        proprietary=browser.find_element(By.XPATH, "/html/body/app-root/div/app-reports/div/div[2]/div/div[2]/div[2]/div[1]/div/mat-tab-group/mat-tab-header/div[2]/div/div/div[4]")
        browser.execute_script("arguments[0].click();", proprietary)
        time.sleep(3)

        try:
            # time.sleep(2)
            # nav=browser.find_element(By.XPATH, "/html/body/app-root/div/app-reports/div/div[2]/div/div[2]/div[1]/ul/li[2]")
            # browser.execute_script("arguments[0].click();", nav)
            # WBR9. Investor Static details feed - CRMS Format
            time.sleep(5)
            output_opn=browser.find_element(By.XPATH, "/html/body/app-root/div/app-reports/div/div[2]/div/div[2]/div[2]/div[2]/form/div/div/div[3]/div[1]/mat-form-field/div/div[1]/div[3]/mat-select/div/div[1]")
            browser.execute_script("arguments[0].click();", output_opn)
            time.sleep(2)
            output=browser.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div/mat-option[7]/span")
            browser.execute_script("arguments[0].click();", output)
            time.sleep(2)
            delivery_opn=browser.find_element(By.XPATH, "/html/body/app-root/div/app-reports/div/div[2]/div/div[2]/div[2]/div[2]/form/div/div/div[3]/div[2]/mat-form-field/div/div[1]/div[3]/mat-select/div/div[2]/div")
            browser.execute_script("arguments[0].click();", delivery_opn)
            time.sleep(2)
            delivery=browser.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div/mat-option[2]/span")
            browser.execute_script("arguments[0].click();", delivery)
            time.sleep(1)
            st_date = browser.find_element(By.XPATH, "/html/body/app-root/div/app-reports/div/div[2]/div/div[2]/div[2]/div[2]/form/div/div/div[31]/div/div[1]/div[1]/mat-form-field/div/div[1]/div[3]/input")
            browser.execute_script("arguments[0].removeAttribute('readonly')", st_date)
            st_date.send_keys(Keys.CONTROL + 'a', Keys.BACKSPACE)
            st_date.send_keys('01-Jan-1995')
            time.sleep(0.5)
            # en_date = browser.find_element(By.XPATH, "/html/body/app-root/div/app-reports/div/div[2]/div/div[2]/div[2]/div[2]/form/div/div/div[31]/div/div[1]/div[2]/mat-form-field/div/div[1]/div[3]/input")
            # browser.execute_script("arguments[0].removeAttribute('readonly')", en_date)
            # en_date.send_keys(Keys.CONTROL + 'a', Keys.BACKSPACE)
            # en_date.send_keys(config['cams']['end_date'])
            # time.sleep(1)
            next=browser.find_element(By.XPATH, "/html/body/app-root/div/app-reports/div/div[2]/div/div[2]/div[2]/div[2]/form/div/div/div[34]/div/input")
            browser.execute_script("arguments[0].click();", next)
            time.sleep(2)
            pswd=browser.find_element(By.XPATH, "/html/body/app-root/div/app-reports/div/div[2]/div/div[2]/div[2]/div[3]/div/div/form/div/div/div[8]/div[1]/mat-form-field/div/div[1]/div[3]/input")
            pswd.send_keys(user[1])
            time.sleep(2)
            pswd_confirm=browser.find_element(By.XPATH, "/html/body/app-root/div/app-reports/div/div[2]/div/div[2]/div[2]/div[3]/div/div/form/div/div/div[8]/div[2]/mat-form-field/div/div[1]/div[3]/input")
            pswd_confirm.send_keys(user[1])
            time.sleep(2)
            submit=browser.find_element(By.XPATH, "/html/body/app-root/div/app-reports/div/div[2]/div/div[2]/div[2]/div[3]/div/div/form/div/div/div[10]/div[2]/input[1]")
            browser.execute_script("arguments[0].click();", submit)
            time.sleep(15)
            # element wait
            submit_response=browser.find_element(By.XPATH, "/html/body/app-root/div/app-reports/div/div[2]/div/div[2]/div[2]/div[3]/div/div/div[2]/p[1]")
            logging.info(f"Mailback request submit response: {submit_response.text}")
            cf=re.search("is .* and at", submit_response.text)
            if cf:
                status[user[0]]=submit_response.text[cf.span()[0]+3:cf.span()[1]-7]
        except Exception as e:
            logging.error(f"Error : {e}")

        logout=browser.find_element(By.XPATH, "/html/body/app-root/div/app-reports/div/div[1]/div[2]/mat-icon")
        browser.execute_script("arguments[0].click();", logout)
        logging.info(f"Processed user {user[0]}.\n")
        # closing the browser
        browser.delete_all_cookies()
        browser.close()
    except Exception as e:
        logging.error(f"Error processing user {user[0]}: {e}\n")
        # closing the browser
        browser.delete_all_cookies()
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
