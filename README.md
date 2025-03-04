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
