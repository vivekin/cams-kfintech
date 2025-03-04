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
    filename=f"kfintech_firefox_{formatted_datetime}.log",  # Specify the log file name
    level=logging.INFO,  # Set the logging level to INFO
    format="%(asctime)s - %(levelname)s - %(message)s",  # Define the log message format
)

start_time = time.perf_counter()
logging.info(f"START - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - v.8")

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

# Creating an instance webdriver
browser = webdriver.Firefox()

user_count = len(userlist)
# Process each user
for user in userlist:
    logging.info(f"Processing {userlist.index(user)+1} of {user_count} users ...")
    print(f"Processing {userlist.index(user)+1} of {user_count} users ...")
    try:
        logging.info(f"Processing user {user[0]} ...")
        browser.get("https://mfs.kfintech.com/mfs/distributor/distributor_Login.aspx")

        page = browser.find_element(By.XPATH, "/html/body/div[3]/div/div[3]/div[2]/div[1]/form/div[3]")
        logging.info(f"Current page: {page.text}")
        userlogin_name = browser.find_element(By.XPATH,"/html/body/div[3]/div/div[3]/div[2]/div[1]/form/div[4]/div[1]/div[2]/input",)
        userlogin_name.send_keys(user[0])
        userlogin_pass = browser.find_element(By.XPATH,"/html/body/div[3]/div/div[3]/div[2]/div[1]/form/div[4]/div[2]/div[2]/input",)
        userlogin_pass.send_keys(user[1])
        userlogin_capcha = browser.find_element(By.XPATH,"/html/body/div[3]/div/div[3]/div[2]/div[1]/form/div[5]/table/tbody/tr[3]/td/label",)
        userlogin_capchainput = browser.find_element(By.XPATH,"/html/body/div[3]/div/div[3]/div[2]/div[1]/form/div[5]/table/tbody/tr[1]/td[2]/input",)
        userlogin_capchainput.send_keys(userlogin_capcha.text)
        time.sleep(2)
        signin = browser.find_element(By.XPATH, "/html/body/div[3]/div/div[3]/div[2]/div[1]/form/div[5]/input")
        signin.click()
        page = browser.find_element(By.XPATH, "/html/body/form/div[3]/article/section[1]/h1")
        logging.info(f"Current page: {page.text}")
        mailback = browser.find_element(By.XPATH, "/html/body/form/div[3]/div[1]/div/div[2]/div/ul[1]/li/a")
        mailback.click()
        time.sleep(2)
        page = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table/tbody/tr[1]/td/table/tbody/tr[2]/td/h3",)
        logging.info(f"Current page: {page.text}")
        transaction_report = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table/tbody/tr[1]/td/table/tbody/tr[4]/td[1]/table/tbody/tr[1]/td[1]/table/tbody/tr[2]/td[2]/a",)
        transaction_report.click()
        time.sleep(2)
        page = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[1]/tbody/tr[1]/td/table/tbody/tr/td[1]",)
        logging.info(f"Current page: {page.text}")
        logging.info("Filling mailback request form ...")
        # past_month_date = today - relativedelta(months=1)
        # past_month_date = past_month_date.strftime("%d/%m/%Y")
        # logging.info(f"past_month_date : {past_month_date}")
        start_date = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[1]/tbody/tr[2]/td/div/table/tbody/tr/td[2]/input",)
        start_date.clear()
        time.sleep(1)
        start_date.send_keys(config['kfintech']['start_date'])
        end_date = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[1]/tbody/tr[2]/td/div/table/tbody/tr/td[4]/input",)
        end_date.clear()
        time.sleep(1)
        end_date.send_keys(config['kfintech']['end_date'])
        time.sleep(1)
        funds = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[1]/tbody/tr[3]/td/table/tbody/tr/td[2]/div/table/tbody/tr[1]/td/input",)
        funds.click()
        time.sleep(1)
        without_split = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[1]/tbody/tr[4]/td[2]/input[2]",)
        without_split.click()
        time.sleep(1)
        email = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[1]/tbody/tr[7]/td[2]/div/input[1]",)
        email.click()
        try:
            time.sleep(0.5)
            email2 = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[1]/tbody/tr[7]/td[2]/div/input[2]",)
            email2.click()
            time.sleep(0.5)
            email3 = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[1]/tbody/tr[7]/td[2]/div/input[3]",)
            email3.click()
            time.sleep(0.5)
            email4 = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[1]/tbody/tr[7]/td[2]/div/input[4]",)
            email4.click()
            time.sleep(0.5)
            email5 = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[1]/tbody/tr[7]/td[2]/div/input[5]",)
            email5.click()
        except Exception as e:
            pass
        time.sleep(1)
        extraction_pass = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[1]/tbody/tr[9]/td/table/tbody/tr[5]/td[2]/input",)
        extraction_pass.send_keys(user[2])
        time.sleep(1)
        extraction_pass_confirm = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[1]/tbody/tr[9]/td/table/tbody/tr[6]/td[2]/input",)
        extraction_pass_confirm.send_keys(user[2])
        time.sleep(1)
        submit = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[1]/tbody/tr[11]/td/input",)
        # submit.click()
        logging.info("Mailback request submitted")
        time.sleep(4)
        try:
            page = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[2]/tbody/tr[1]/td/table/tbody/tr/td[1]",)
            logging.info(f"Current page: {page.text}")
            submit_response = browser.find_element(By.XPATH,"/html/body/form/div[6]/div/table[1]/tbody/tr[2]/td/table[2]/tbody/tr[2]/td/p[1]",)
            logging.info(f"Mailback request submit response: {submit_response.text}")
            kf=re.search("number .* \\.", submit_response.text)
            if kf:
                status[user[0]]=submit_response.text[kf.span()[0]+7:kf.span()[1]-2]
        except Exception as e:
            logging.error(f"Could not fetch Mailback request submit response: {e}")

        logout = browser.find_element(By.XPATH, "/html/body/form/div[3]/div/div[2]/div[1]/a[3]")
        time.sleep(5)
        logout.click()

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
