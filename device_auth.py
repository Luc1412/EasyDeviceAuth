import asyncio
import json
import os
import uuid
import zipfile
from typing import Optional
from urllib.request import urlretrieve

from pip._vendor import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DEVICE_AUTH_FILENAME = 'device_auths.json'
DRIVER_DOWNLOAD_URL = 'https://github.com/mozilla/geckodriver/releases/download/v0.28.0/geckodriver-v0.28.0-win64.zip'
IOS_TOKEN = 'MzQ0NmNkNzI2OTRjNGE0NDg1ZDgxYjc3YWRiYjIxNDE6OTIwOWQ0YTVlMjVhNDU3ZmI5YjA3NDg5ZDMxM2I0MWE='
OS = 'Windows/10.0.17134.1.768.64bit'
BUILD = '++Fortnite+Release-14.10-CL-14288110'


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


def get_device_auth(email, code):
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
    }
    headers = {
        'Authorization': f'basic {IOS_TOKEN}',
        'User-Agent': f'Fortnite/{BUILD} {OS}',
        'X-Epic-Device-ID': uuid.uuid4().hex
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
    client_id = data['client_id']
    access_token = data['access_token']

    headers['Authorization'] = f'bearer {access_token}'
    device_auth_url = \
        f'https://account-public-service-prod.ol.epicgames.com/account/api/public/account/{client_id}/deviceAuth'
    response = requests.post(device_auth_url, json={}, headers=headers)
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
    print(data)
    return {'device_id': data['deviceId'], 'account_id': data['accountId'], 'secret': data['secret']}


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
    WebDriverWait(driver, 60 * 60).until(EC.url_matches('https://www.epicgames.com/account/personal'))
    driver.get(
        'view-source:https://www.epicgames.com/id/api/redirect?clientId=3446cd72694c4a4485d81b77adbb2141&responseType=code')
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'pre')))
    pre = driver.find_element_by_tag_name("pre").text
    driver.close()
    url = json.loads(pre)['redirectUrl']
    code = url.split('?code=')[1]
    return code


if __name__ == '__main__':
    get_device_auth(None, '5924d3f6f50f4fc4b854745b039d95de')
    pass
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
