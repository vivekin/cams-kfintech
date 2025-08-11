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



print("Script running ...")

# get configs
print("Fetching configs ...")
config = configparser.ConfigParser()
config.read('config.ini')

# Configure the logger
datetime_object = datetime.now()
formatted_datetime = datetime_object.strftime("%Y_%m_%dT%H_%M_%S")
logging.basicConfig(
    filename=f"kfintech_new_MFSD205_firefox_{formatted_datetime}.log",  # Specify the log file name
    level=logging.INFO,  # Set the logging level to INFO
    format="%(asctime)s - %(levelname)s - %(message)s",  # Define the log message format
)

start_time = time.perf_counter()
logging.info(f"START - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - v.1")

today = date.today()
logging.info(f"Today's date: {formatted_datetime}")
logging.info(f"[config.ini] start_date: {config['kfintech']['start_date']}")
logging.info(f"[config.ini] end_date: {config['kfintech']['end_date']}")
logging.info(f"[config.ini] start_month: {config['kfintech']['start_month']}")
logging.info(f"[config.ini] end_month: {config['kfintech']['end_month']}")
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
# service = Service(executable_path=fr"{config['DEFAULT']['msedgedriver']}")
# Creating an instance webdriver
browser = webdriver.Firefox()
# browser = webdriver.Edge(service=service)

user_count = len(userlist)
# Process each user
for user in userlist:
    logging.info(f"Processing {userlist.index(user)+1} of {user_count} users ...")
    print(f"Processing {userlist.index(user)+1} of {user_count} users ...")
    try:
        logging.info(f"Processing user {user[0]} ...")
        browser.get("https://dss.kfintech.com/dssweb/")

        page = browser.find_element(By.XPATH, "/html/body/div/div[2]/div[1]/div[2]/div/h5")
        logging.info(f"Current page: {page.text}")
        userlogin_name = browser.find_element(By.XPATH,"/html/body/div/div[2]/div[1]/div[2]/div/form/div/div/div[1]/div/input",)
        userlogin_name.send_keys(user[0])
        userlogin_pass = browser.find_element(By.XPATH,"/html/body/div/div[2]/div[1]/div[2]/div/form/div/div/div[2]/div/input",)
        userlogin_pass.send_keys(user[1])
        time.sleep(2)
        signin = browser.find_element(By.XPATH, "/html/body/div/div[2]/div[1]/div[2]/div/form/div/button")
        signin.click()
        time.sleep(7)
        webdriver.ActionChains(browser).send_keys(Keys.ESCAPE).perform()
        time.sleep(2)
        page = browser.find_element(By.XPATH, "/html/body/div/div/div/div/div/ul/a[1]")
        logging.info(f"Current page: {page.text}")
        mailback = browser.find_element(By.XPATH, "/html/body/div/div/div/div/div/ul/a[3]")
        mailback.click()
        time.sleep(2)
        page = browser.find_element(By.XPATH,"/html/body/div/div/div/div/div/ul/a[3]",)
        logging.info(f"Current page: {page.text}")
        # MFSD205 - Brokerage Report
        brokerage_tab = browser.find_element(By.XPATH,"/html/body/div/div[2]/main/div/div[2]/div/div[3]/div[1]/div/div[2]",)
        brokerage_tab.click()
        brokerage_report = browser.find_element(By.XPATH,"/html/body/div/div[2]/main/div/div[2]/div/div[3]/div[2]/div/ul/a[1]/li/div",)
        brokerage_report.click()
        time.sleep(2)
        page = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/div[1]/div",)
        logging.info(f"Current page: {page.text}")
        logging.info("Filling mailback request form ...")
        # past_month_date = today - relativedelta(months=1)
        # past_month_date = past_month_date.strftime("%d/%m/%Y")
        # logging.info(f"past_month_date : {past_month_date}")

        funds_drpdwn = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/form/div[2]/div[1]/div[1]/div[1]/div/div",)
        funds_drpdwn.click()
        time.sleep(1)
        funds = browser.find_element(By.XPATH,"/html/body/div[2]/div[3]/ul/li[1]",)
        funds.click()
        time.sleep(1)
        webdriver.ActionChains(browser).send_keys(Keys.ESCAPE).perform()
        time.sleep(7)

        schemes_drpdwn = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/form/div[2]/div[1]/div[1]/div[2]/div/div",)
        schemes_drpdwn.click()
        time.sleep(1)
        schemes = browser.find_element(By.XPATH,"/html/body/div[2]/div[3]/ul/li[1]",)
        schemes.click()
        time.sleep(1)
        webdriver.ActionChains(browser).send_keys(Keys.ESCAPE).perform()
        time.sleep(5)

        brokerage_drpdwn = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/form/div[2]/div[1]/div[1]/div[3]/div/div",)
        brokerage_drpdwn.click()
        time.sleep(1)
        brokerage_type = browser.find_element(By.XPATH,"/html/body/div[2]/div[3]/ul/li[1]",)
        brokerage_type.click()
        time.sleep(1)
        webdriver.ActionChains(browser).send_keys(Keys.ESCAPE).perform()
        time.sleep(7)

        # brokerage_sub_drpdwn = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/form/div[2]/div[1]/div[1]/div[4]/div/div",)
        # brokerage_sub_drpdwn.click()
        # time.sleep(1)
        # brokerage_subtype = browser.find_element(By.XPATH,"/html/body/div[2]/div[3]/ul/li",)
        # brokerage_subtype.click()
        # time.sleep(1)
        # webdriver.ActionChains(browser).send_keys(Keys.ESCAPE).perform()
        # time.sleep(2)

        st_month = browser.find_element(By.XPATH, "/html/body/div/main/div/div[2]/div/div/form/div[2]/div[1]/div[2]/div[1]/div/input")
        browser.execute_script("arguments[0].removeAttribute('readonly')", st_month)
        st_month.send_keys(Keys.CONTROL + 'a', Keys.BACKSPACE)
        st_month.send_keys(config['kfintech']['start_month'])
        time.sleep(0.5)
        en_month= browser.find_element(By.XPATH, "/html/body/div/main/div/div[2]/div/div/form/div[2]/div[1]/div[2]/div[2]/div/input")
        browser.execute_script("arguments[0].removeAttribute('readonly')", en_month)
        en_month.send_keys(Keys.CONTROL + 'a', Keys.BACKSPACE)
        en_month.send_keys(config['kfintech']['end_month'])
        time.sleep(0.5)
        csv_sel = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/form/div[2]/div[1]/div[3]/fieldset/div/div/div[2]/label/span[1]/input",)
        csv_sel.click()

        try:
            logging.info("email check")
            # fieldset = browser.find_element(By.CSS_SELECTOR, "fieldset.MuiFormControl-root.css-l0oyuh")
            # checkboxes = fieldset.find_elements(By.CSS_SELECTOR, "input.css-j8yymo[type='checkbox']")
            checkboxes = browser.find_elements(By.XPATH,"//fieldset[legend[normalize-space(.)='I want this Report for :']]//input[@type='checkbox']")
            for checkbox in checkboxes:
                logging.info(f"email : {checkbox}")
                time.sleep(1)
                if not checkbox.is_selected():
                    checkbox.click()
        except Exception as e:
            logging.error(f"email error: {e}")

        time.sleep(1)
        extraction_pass = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/form/div[2]/div[2]/div[3]/div/div[1]/div/div/div/input",)
        extraction_pass.send_keys(user[2])
        time.sleep(1)
        extraction_pass_confirm = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/form/div[2]/div[2]/div[3]/div/div[2]/div/div/div/input",)
        extraction_pass_confirm.send_keys(user[2])
        time.sleep(1)
        submit = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/form/div[3]/button[1]",)
        submit.click()
        logging.info("Mailback request submitted")
        time.sleep(4)
        try:
            page = browser.find_element(By.XPATH,"/html/body/div/main/div/div[2]/div/div/div[1]/div",)
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
