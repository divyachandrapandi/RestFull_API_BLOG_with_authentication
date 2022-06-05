## concepts -Environement variables are always string so convert the datatype as per need
# create .env text file and add all the variables

from dotenv import load_dotenv
import os
load_dotenv("E:\PYTHON_BOOTCAMP_Dr_ANGELA_YU\EnvironmentVariables\.env")
ADMIN_EMAIL = os.getenv("Adminemail")
ADMIN_PASSWORD= os.getenv("Ad_password")
DEBUG = bool(os.getenv("debug"))
EMAIL_PORT = int(os.getenv("port"))

print(ADMIN_EMAIL)
print(ADMIN_PASSWORD, DEBUG, EMAIL_PORT)