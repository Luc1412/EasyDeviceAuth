# EasyDeviceAuth
[![Discord](https://img.shields.io/discord/341939185051107330?color=%237289DA&label=Discord&logo=discord&logoColor=white&style=for-the-badge)](https://discord.gg/Sw5RbXD)
![GitHub all releases](https://img.shields.io/github/downloads/luc1412/EasyDeviceAuth/total?logo=github&style=for-the-badge)

EasyDeviceAuth is a tool to automate the process to generate a `device_auths.json` file for multiple EpicGames Accounts, which for example is used by the popular [fortnitepy](https://github.com/Terbau/fortnitepy) library.


### **Only Windows and Firefox are supported atm! Linux, MacOS and Chrome and Safari comming soon.**

This is an example how the result looks like:
```json
{
  "sample_email1": {
    "device_id": "sample_device_id1", 
    "account_id": "sample_account_id1", 
    "secret": "sample_secret1"
  },
  "sample_email2": {
    "device_id": "sample_device_id2",
    "account_id": "sample_account_id2",
    "secret": "sample_secret2"
  }
}
```

## How to use?

1.) Download and install Firefox from [here](https://www.mozilla.org/en-US/firefox/new/).

2.) Download the latest executable from [here](https://github.com/Luc1412/EasyDeviceAuth/releases/latest) and place it into a folder

3.) Create a `credentials.json` file where you can insert your account details. Here is an example:
```json
{
  "email1": "password1",
  "email2": "password2"
}
```

3.) Run the executable and solve the captchas in the browser windows that open.

4.) As result you get a `device_auths.json` file.

## How to compile it yourself?

1.) Clone this repo.

2.) Install PyInstaller.

3.) Create a venv and install all requirements from the `requirements.txt`

4.) Switch to the downloaded directory and compile the file with `pyinstaller --paths venv/Lib/site-packages --onefile -i icon.ico -n EasyDeviceAuth device_auth.py`