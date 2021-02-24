import asyncio
import json
import os
import sys
import uuid
import zipfile
from typing import Optional
from urllib.request import urlretrieve

import chromedriver_autoinstaller
from pip._vendor import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DEVICE_AUTH_FILENAME = 'device_auths.json'
DRIVER_DOWNLOAD_URL = 'https://github.com/mozilla/geckodriver/releases/download/v0.28.0/geckodriver-v0.28.0-win64.zip'
IOS_TOKEN = 'MzQ0NmNkNzI2OTRjNGE0NDg1ZDgxYjc3YWRiYjIxNDE6OTIwOWQ0YTVlMjVhNDU3ZmI5YjA3NDg5ZDMxM2I0MWE='
driver = webdriver.Chrome


def download_driver():
    print('Check for installed OS...')
    global driver
    if sys.platform == 'darwin':
        print('Mac OS User. No additional drivers required. Using Safari as browser...')
        driver = webdriver.Safari
    else:
        print('Windows or Linux User. Installing chrome driver...')
        chromedriver_autoinstaller.install()

    # if os.path.isfile('geckodriver.exe'):
    #     return print('Webdriver found!')
    # print('Driver not found. Download driver...')
    # urlretrieve(DRIVER_DOWNLOAD_URL, 'geckodriver.zip')
    # print('Successfully downloaded driver. Unpacking driver....')
    # with zipfile.ZipFile('edgedriver.zip', 'r') as zip_ref:
    #     zip_ref.extractall('temp')
    # os.remove('geckodriver.zip')
    # os.rename('temp/geckodriver.exe', 'geckodriver.exe')
    # os.rmdir('temp')
    # print('Driver successfully unpacked.')


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


def get_device_auth(email, code):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'basic {IOS_TOKEN}',
    }
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'includePerms': False,
    }
    auth_code_url = 'https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token'
    response = requests.post(auth_code_url, data=payload, headers=headers)
    if response.status_code >= 400:
        try:
            error = response.json()
        except ValueError:
            error = {}
        error_code = error.get('errorCode', 'Not provided')
        error_message = error.get('errorMessage', 'Not provided')

        if error_code == 'errors.com.epicgames.account.oauth.authorization_code_not_found':
            print(f'Invalid authorization code found for {email}. Skipping account...')
            return None
        else:
            raise Exception(
                f'An unexpected error occurred while logging in with authorization code. '
                f'Code: {error_code} '
                f'Message: {error_message}'
            )

    data = response.json()
    account_id = data['account_id']
    access_token = data['access_token']
    display_name = data['displayName']

    headers = {'Authorization': f'bearer {access_token}'}
    device_auth_url = \
        f'https://account-public-service-prod.ol.epicgames.com/account/api/public/account/{account_id}/deviceAuth'
    response = requests.post(device_auth_url, headers=headers)
    if response.status_code >= 400:
        try:
            error = response.json()
        except ValueError:
            error = {}
        error_code = error.get('errorCode', 'Not provided')
        error_message = error.get('errorMessage', 'Not provided')

        raise Exception(f'An unexpected error occurred while generating device auth. '
                        f'Code: {error_code} '
                        f'Message: {error_message}')

    data = response.json()
    return {'device_id': data['deviceId'], 'account_id': data['accountId'], 'secret': data['secret']}


def get_code(email, password):
    session_driver = driver()
    session_driver.set_window_size(600, 800)
    session_driver.get('https://www.epicgames.com/id/login/epic')
    WebDriverWait(session_driver, 30).until(EC.presence_of_element_located((By.ID, 'email')))
    email_input = session_driver.find_element_by_id('email')
    email_input.send_keys(email)
    password_input = session_driver.find_element_by_id('password')
    password_input.send_keys(password)
    WebDriverWait(session_driver, 30).until(EC.element_to_be_clickable((By.ID, 'sign-in')))
    signin_button = session_driver.find_element_by_id('sign-in')
    signin_button.click()
    print('Wait for entering 2-FA code and/or solving captcha...')
    WebDriverWait(session_driver, 60 * 60).until(EC.url_matches('https://www.epicgames.com/account/personal'))
    session_driver.get('view-source:https://www.epicgames.com/id/api/redirect?clientId=3446cd72694c4a4485d81b77adbb2141&responseType=code')
    WebDriverWait(session_driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'pre')))
    pre = session_driver.find_element_by_tag_name("pre").text
    session_driver.close()
    url = json.loads(pre)['redirectUrl']
    code = url.split('?code=')[1]
    return code


if __name__ == '__main__':
    download_driver()
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
        device_auth = get_device_auth(email, code)
        store_device_auth_details(email, device_auth)
        print(f'Successfully generated device auth for {email}')
    print('Finished generating device auths.')
