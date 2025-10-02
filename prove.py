from selenium import webdriver
from selenium.webdriver.edge.options import Options
import os
import time

def open_edge_with_profile(command: str):
    # Close all existing Edge instances (optional)
    os.system("taskkill /f /im msedge.exe")

    # Set up Edge options
    edge_options = Options()

    # Use your existing Edge profile
    user_data_dir = os.path.expanduser(r'~\AppData\Local\Microsoft\Edge\User Data')
    profile_directory = 'Default'  # Change this to your profile name

    edge_options.add_argument(f'user-data-dir={user_data_dir}')
    edge_options.add_argument(f'profile-directory={profile_directory}')

    # Disable automation flags to make it less detectable
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)

    # Or let Selenium find it automatically:
    driver = webdriver.Edge(options=edge_options)

    # Navigate to a website
    driver.get('https://wplace.live')

    # Send command to open DevTools
    time.sleep(2)
    driver.execute_script(command)

    # TODO: Do something with the captcha :3

    # Your automation code here
    time.sleep(5)
    driver.quit()