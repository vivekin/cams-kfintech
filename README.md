kfintech mailback

Install Python on Windows
https://www.python.org/downloads/release/python-3127/

Verify Python [CMD]:

    python --version


Install packages  [CMD]

    pip install selenium python-dateutil


Create folder "kfintech_python" in Documents
Place the files config.ini, kfintech_users.csv, kfintech_firefox.py, kfintech_edge.py in folder
"C:\Users\<username>\Documents\kfintech_python\kfintech_users.csv"

kfintech_users.csv should have data like below:
user1,user1pass@101,extpass1
user2,user2pass@101,extpass2
user3,user3pass@101,extpass3

Modify date values in config.ini under kfintech section (format should be dd/mm/yyyy)
[DEFAULT]

[kfintech]
start_date = 23/10/2024
end_date = 25/10/2024

[cams]
start_date = 05-Nov-2024
end_date = 15-Nov-2024


Open [CMD] and navigate to kfintech_python folder and run:

    python .\kfintech_firefox.py


Log file will be generated like below:
kfintech_firefox_yyyy_mm_ddThh_mm_ss.log


cams mailback

Create folder "cams_python" in Documents
Place the files config.ini, cams_users.csv, cams_firefox.py, cams_edge.py in folder
"C:\Users\<username>\Documents\cams_python\cams_users.csv"

cams_users.csv should have data like below:
user1@email.com,extpass1
user2@email.com,extpass2
user3@email.com,extpass3

Modify date values in config.ini under cams section (format should be dd-MMM-yyyy)
[DEFAULT]

[kfintech]
start_date = 23/10/2024
end_date = 25/10/2024

[cams]
start_date = 05-Nov-2024
end_date = 15-Nov-2024


Open [CMD] and navigate to cams_python folder and run:

    python .\cams_firefox.py


Log file will be generated like below:
cams_firefox_yyyy_mm_ddThh_mm_ss.log

## For Edge browser

Download edge driver from:
https://developer.microsoft.com/en-in/microsoft-edge/tools/webdriver

Extract "edgedriver_win64.zip"

In config.ini file, add this line under [DEFAULT]
msedgedriver=<path to msedgedriver.exe>

pip install selenium --upgrade

===========================================

## CAMS Scripts
##### WBR2. Investor Transactions for a Period
cams_WBR2_edge.py
cams_WBR2_firefox.py
##### WBR9. Investor Static details feed - CRMS Format
cams_WBR9_edge.py
cams_WBR9_firefox.py
##### WBR49. SIP/STP procured for the period
cams_WBR49_edge.py
cams_WBR49_firefox.py
##### WBR77. Consolidated Brokerage Payout Details
cams_WBR77_edge.py
cams_WBR77_firefox.py

## Kfintech Old Scripts
##### MFSD201 - Transaction Report
kfintech_old_MFSD201_edge.py
kfintech_old_MFSD201_firefox.py
##### MFSD205 - Brokerage Report
kfintech_old_MFSD205_edge.py
kfintech_old_MFSD205_firefox.py
##### MFSD230 - SIP/STP Report
kfintech_old_MFSD230_edge.py
kfintech_old_MFSD230_firefox.py
##### MFSD262 - PAN Level KYC Report
kfintech_old_MFSD262_edge.py
kfintech_old_MFSD262_firefox.py

## Kfintech New Scripts
##### MFSD201 - Transaction Report
kfintech_new_MFSD201_edge.py
kfintech_new_MFSD201_firefox.py
##### MFSD205 - Brokerage Report
kfintech_new_MFSD205_edge.py
kfintech_new_MFSD205_firefox.py
##### MFSD230 - SIP/STP Report
kfintech_new_MFSD230_edge.py
kfintech_new_MFSD230_firefox.py
##### MFSD262 - PAN Level KYC Report
kfintech_new_MFSD262_edge.py
kfintech_new_MFSD262_firefox.py
