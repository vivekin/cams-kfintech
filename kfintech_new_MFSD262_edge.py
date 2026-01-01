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

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ocrml import solve_captcha


print("Script running ...")

# get configs
print("Fetching configs ...")
config = configparser.ConfigParser()
config.read('config.ini')

# Configure the logger
datetime_object = datetime.now()
formatted_datetime = datetime_object.strftime("%Y_%m_%dT%H_%M_%S")
logging.basicConfig(
    filename=f"kfintech_new_MFSD262_edge_{formatted_datetime}.log",  # Specify the log file name
    level=logging.INFO,  # Set the logging level to INFO
    format="%(asctime)s - %(levelname)s - %(message)s",  # Define the log message format
)

start_time = time.perf_counter()
logging.info(f"START - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - v.1")

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
# print(userlist)

# Specify the path to your msedgedriver
service = Service(executable_path=fr"{config['DEFAULT']['msedgedriver']}")
# Creating an instance webdriver
browser = webdriver.Edge(service=service)

user_count = len(userlist)
# Process each user
for user in userlist:
    logging.info(f"Processing {userlist.index(user)+1} of {user_count} users ...")
    print(f"Processing {userlist.index(user)+1} of {user_count} users ...")
    try:
        logging.info(f"Processing user {user[0]} ...")
        browser.get("https://dss.kfintech.com/dssweb/")

        time.sleep(1)
        page = browser.find_element(By.XPATH, "/html/body/div/div[2]/div[1]/div[2]/div/h5")
        logging.info(f"Current page: {page.text}")
        loggedin=False

        while(loggedin==False):
            time.sleep(0.5)
            userlogin_name = browser.find_element(By.XPATH,"/html/body/div/div[2]/div[1]/div[2]/div/form/div/div/div[1]/div/input",)
            userlogin_name.send_keys(Keys.CONTROL + 'a', Keys.BACKSPACE)
            userlogin_name.send_keys(user[0])
            userlogin_pass = browser.find_element(By.XPATH,"/html/body/div/div[2]/div[1]/div[2]/div/form/div/div/div[2]/div/input",)
            userlogin_pass.send_keys(Keys.CONTROL + 'a', Keys.BACKSPACE)
            userlogin_pass.send_keys(user[1])
            time.sleep(1)
            captcha_img = browser.find_element(By.XPATH, "/html/body/div/div[2]/div[1]/div[2]/div/form/div/div/div[3]/div[2]/div/div/canvas")
            # Get the canvas image as a Base64 string via JavaScript
            canvas_base64 = browser.execute_script("""
                var canvas = arguments[0];
                return canvas.toDataURL('image/png').substring(22);
            """, captcha_img)
            
            # Convert Base64 to image
            canvas_png = base64.b64decode(canvas_base64)
            image = Image.open(io.BytesIO(canvas_png))
            image.save("temp_captcha.png")
            captcha_text = solve_captcha("temp_captcha.png")
            time.sleep(1)
            captcha_input = browser.find_element(By.XPATH,"/html/body/div/div[2]/div[1]/div[2]/div/form/div/div/div[3]/div[1]/div/input",)
            # captcha_input.send_keys(Keys.CONTROL + 'a', Keys.BACKSPACE)
            captcha_input.send_keys(captcha_text)
            time.sleep(0.5)
            signin = browser.find_element(By.XPATH, "/html/body/div/div[2]/div[1]/div[2]/div/form/div/button")
            signin.click()
            time.sleep(1)
            try:
                # Wait briefly for captcha error toast
                toast = WebDriverWait(browser, 3).until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/div/div[2]/div[2]/div"))
                )
                logging.info("Wrong captcha, retrying...")
                loggedin=False
            except Exception:
                logging.info("No error toast, login likely succeeded!")
                loggedin=True
   
        time.sleep(7)
        # popup = browser.find_element(By.XPATH, "/html/body/div[2]/div[3]/div/h2/button")
        # popup.click()
        # time.sleep(2)
        webdriver.ActionChains(browser).send_keys(Keys.ESCAPE).perform()
        time.sleep(2)
        page = browser.find_element(By.XPATH, "/html/body/div/div/div/div/div/ul/a[1]")
        logging.info(f"Current page: {page.text}")
        mailback = browser.find_element(By.XPATH, "/html/body/div/div/div/div/div/ul/a[3]")
        mailback.click()
        time.sleep(2)
        page = browser.find_element(By.XPATH,"/html/body/div/div/div/div/div/ul/a[3]",)
        logging.info(f"Current page: {page.text}")
        # MFSD262 - PAN Level KYC Report
        special_tab = browser.find_element(By.XPATH,"/html/body/div/div[2]/main/div/div[2]/div/div[3]/div[1]/div/div[6]",)
        special_tab.click()
        pan_level_report = browser.find_element(By.XPATH,"/html/body/div/div[2]/main/div/div[2]/div/div[3]/div[2]/div/ul/a[4]/li/div",)
        pan_level_report.click()
        time.sleep(2)
        page = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/div[1]",)
        logging.info(f"Current page: {page.text}")
        logging.info("Filling mailback request form ...")
        # past_month_date = today - relativedelta(months=1)
        # past_month_date = past_month_date.strftime("%d/%m/%Y")
        # logging.info(f"past_month_date : {past_month_date}")
        funds_drpdwn = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/form/div/div/div[1]/div[2]/div/div/div",)
        funds_drpdwn.click()
        time.sleep(1)
        funds = browser.find_element(By.XPATH,"/html/body/div[2]/div[3]/ul/li/span[1]",)
        funds.click()
        time.sleep(1)
        webdriver.ActionChains(browser).send_keys(Keys.ESCAPE).perform()
        time.sleep(4)

        try:
            logging.info("email check")
            # fieldset = browser.find_element(By.CSS_SELECTOR, "fieldset.MuiFormControl-root.css-1oz7uu7")
            # checkboxes = fieldset.find_elements(By.CSS_SELECTOR, "input.css-j8yymo[type='checkbox']")
            # checkboxes = browser.find_elements(By.CSS_SELECTOR,"fieldset.MuiFormControl-root.css-1oz7uu7 input.css-j8yymo[type='checkbox']")
            checkboxes = browser.find_elements(By.XPATH,"//fieldset[legend[normalize-space(.)='I want this Report for']]//input[@type='checkbox']")
            for checkbox in checkboxes:
                logging.info(f"email : {checkbox}")
                time.sleep(1)
                if not checkbox.is_selected():
                    checkbox.click()
        except Exception as e:
            logging.error(f"email error: {e}")

        time.sleep(1)
        excel_fmt = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/form/div/div/div[1]/div[3]/div/fieldset/div/div/div[1]/label/span[1]/input",)
        excel_fmt.click()
        time.sleep(1)
        extraction_pass = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/form/div/div/div[2]/div/div[2]/div/div[1]/div/div/div/input",)
        extraction_pass.send_keys(user[2])
        time.sleep(1)
        extraction_pass_confirm = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/form/div/div/div[2]/div/div[2]/div/div[2]/div/div/div/input",)
        extraction_pass_confirm.send_keys(user[2])
        time.sleep(1)
        submit = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/form/div/div/div[3]/div/button[1]",)
        submit.click()
        logging.info("Mailback request submitted")
        time.sleep(4)
        try:
            page = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/div[1]",)
            logging.info(f"Current page: {page.text}")
            submit_response = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/div[2]/p",)
            logging.info(f"Mailback request submit response: {submit_response.text}")
            kf=re.search(r"reference number (\w+)", submit_response.text)
            if kf:
                status[user[0]]=kf.group(1)
        except Exception as e:
            logging.error(f"Could not fetch Mailback request submit response: {e}")

        user_drpdwn = browser.find_element(By.XPATH, "/html/body/div/div/header/div/div[3]/div[2]/div[3]")
        time.sleep(2)
        user_drpdwn.click()
        logout = browser.find_element(By.XPATH, "/html/body/div[2]/div[3]/ul/a[8]")
        time.sleep(1)
        logout.click()
        time.sleep(1)

        logging.info(f"Processed user {user[0]}.\n")
    except Exception as e:
        logging.error(f"Error processing user {user[0]}: {e}\n")

# closing the browser
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

