import asyncio
import json
import os
import zipfile
from typing import Optional
from urllib.request import urlretrieve

import fortnitepy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DEVICE_AUTH_FILENAME = 'device_auths.json'
DRIVER_DOWNLOAD_URL = 'https://github.com/mozilla/geckodriver/releases/download/v0.28.0/geckodriver-v0.28.0-win64.zip'
current_client: Optional[fortnitepy.Client] = None


def get_device_auth_details():
    if os.path.isfile(DEVICE_AUTH_FILENAME):
        with open(DEVICE_AUTH_FILENAME, 'r') as fp:
            return json.load(fp)
    return {}


def store_device_auth_details(email, details):
    existing = get_device_auth_details()
    existing[email] = details

    with open(DEVICE_AUTH_FILENAME, 'w') as fp:
        json.dump(existing, fp)


async def event_ready():
    print('----------------')
    print('Generated Device Auth for')
    print(current_client.user.display_name)
    print(current_client.user.id)
    print('----------------')
    await current_client.close()


async def event_device_auth_generate(details, email):
    store_device_auth_details(email, details)


def download_driver():
    print('Check for web driver...')
    if os.path.isfile('geckodriver.exe'):
        return print('Webdriver found!')
    print('Driver not found. Download driver...')
    urlretrieve(DRIVER_DOWNLOAD_URL, 'geckodriver.zip')
    print('Successfully downloaded driver. Unpacking driver....')
    with zipfile.ZipFile('geckodriver.zip', 'r') as zip_ref:
        zip_ref.extractall('temp')
    os.remove('geckodriver.zip')
    os.rename('temp/geckodriver.exe', 'geckodriver.exe')
    os.rmdir('temp')
    print('Driver successfully unpacked.')


async def get_device_auth(email, password, code):
    device_auth_details = get_device_auth_details().get(email.lower(), {})
    auth = fortnitepy.AdvancedAuth(email=email, password=password, authorization_code=code,
                                   delete_existing_device_auths=True, **device_auth_details)
    client = fortnitepy.Client(auth=auth)
    client.add_event_handler('event_device_auth_generate', event_device_auth_generate)
    client.add_event_handler('event_ready', event_ready)
    global current_client
    current_client = client
    await client.start()


def get_code(email, password):
    driver = webdriver.Firefox()
    driver.set_window_size(600, 800)
    driver.get('https://www.epicgames.com/id/login/epic')
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'email')))
    email_input = driver.find_element_by_id('email')
    email_input.send_keys(email)
    password_input = driver.find_element_by_id('password')
    password_input.send_keys(password)
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'sign-in')))
    signin_button = driver.find_element_by_id('sign-in')
    signin_button.click()
    print('Wait for entering 2-FA code and/or solving captcha...')
    WebDriverWait(driver, 60*60).until(EC.url_matches('https://www.epicgames.com/account/personal'))
    driver.get('view-source:https://www.epicgames.com/id/api/redirect?clientId=3446cd72694c4a4485d81b77adbb2141&responseType=code')
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'pre')))
    pre = driver.find_element_by_tag_name("pre").text
    driver.close()
    url = json.loads(pre)['redirectUrl']
    code = url.split('?code=')[1]
    return code


if __name__ == '__main__':
    download_driver()
    loop = asyncio.get_event_loop()
    print('Load credentials...')
    if not os.path.isfile('credentials.json'):
        with open('credentials.json', 'w') as fp:
            json.dump({}, fp)
    with open('credentials.json') as f:
        credentials = json.load(f)
    print(f'Found {len(credentials)} accounts.')
    for email, password in credentials.items():
        print(f'Getting authorization code for {email}...')
        code = get_code(email, password)
        print(f'Generating device auth for {email}')
        get_device_auth(email, password, code)
        loop.run_until_complete(get_device_auth(email, password, code))
    print('Finished generating device auths.')
