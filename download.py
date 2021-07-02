from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import time
import base64
from selenium.webdriver.common.by import By
import os
import pandas as pd
from os import path
from PIL import Image
import pytesseract
from pytesseract import image_to_string
import cv2
import sys
import numpy as np
from io import BytesIO
import re
import urllib
import urllib.request
from pynput.keyboard import Key, Controller
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
url = "https://districts.ecourts.gov.in/agra"  # base url
# Take small runs.. Can create timeouts due to captcha... depends on network speed and chunksize variable..
from_date = '15-12-2019'
# Take small runs.. Can take timeouts due to captcha...
to_date = '15-01-2020'
s_d = 0  # Start index of districts...
e_d = 4  # End index of districts...
# base directory for outputs
base_dir = '/Users/arjunth/Documents/ecourts/ecourts-scraper/data/'
# Thanks to Stackoverflow... https://stackoverflow.com/questions/46026983/how-to-download-the-pdf-by-using-selenium-module-firefox-in-python-3#:~:text=import%20os%2C%20time%20from%20selenium,download


def get_request_session(driver):
    import requests
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])
    return session


def get_districts():
    driver = webdriver.Chrome("./chromedriver")
    wait = WebDriverWait(driver, 180)
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#sateist')))
    districtListDropdown = Select(
        driver.find_element_by_css_selector("#sateist"))
    districts = [i.text for i in districtListDropdown.options][1:]
    driver.quit()
    return districts

# https://stackoverflow.com/questions/13832322/how-to-capture-the-screenshot-of-a-specific-element-rather-than-entire-page-usin/44868231


def get_captcha(element):
    with open("securimage_show.png", "wb") as file:
        file.write(element.screenshot_as_png)
# https://github.com/pawangeek/NER/blob/38b3577ac7c7fa6a27e8763d5f408791bdf9343d/Scraper/Download%20scripts.ipynb


def process_image():
    # reads the image and thresholds it to binary image and removing noise
    img = cv2.imread("securimage_show.png")
    rows, cols, t = img.shape
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    for i in range(rows):
        for j in range(cols):
            if img[i, j] >= 90:
                img[i, j] = 255
    ret, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    cv2.imwrite("securimage_show.png", img)
# https://github.com/pawangeek/NER/blob/38b3577ac7c7fa6a27e8763d5f408791bdf9343d/Scraper/Download%20scripts.ipynb


def imgtotxt(driver):
    img = driver.find_element_by_id("captcha_image")
    get_captcha(img)
    process_image()
    captchaText = image_to_string(Image.open("securimage_show.png"))
    print(captchaText)
    captcha = driver.find_element_by_id('captcha')
    captcha.clear()
    captcha.send_keys(captchaText)
    driver.find_element_by_xpath(
        '//*[@id="caseNoDet"]/div[7]/span[3]/input[1]').click()
    time.sleep(1)


def get_subcourts(district):
    driver = webdriver.Chrome("./chromedriver")
    try:
        wait = WebDriverWait(driver, 10)
        driver.get(url)
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#sateist')))
        Select(driver.find_element_by_id("sateist")
               ).select_by_visible_text(district)
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#block-block-8 > div.right-accordian.english_language > button:nth-child(4)')))
        driver.find_element_by_css_selector(
            "#block-block-8 > div.right-accordian.english_language > button:nth-child(4)").click()
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#block-block-8 > div.right-accordian.english_language > div:nth-child(5) > ul > li:nth-child(4) > a')))
        current = driver.window_handles[0]
        driver.find_element_by_css_selector(
            "#block-block-8 > div.right-accordian.english_language > div:nth-child(5) > ul > li:nth-child(4) > a").click()
        wait.until(EC.number_of_windows_to_be(2))
        newWindow = [
            window for window in driver.window_handles if window != current][0]
        driver.switch_to.window(newWindow)
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#court_complex_code')))
        ListDropdown = Select(driver.find_element_by_css_selector(
            "#court_complex_code")).options
        subcourts = [i.text for i in ListDropdown]
        driver.quit()
    except:
        driver.quit()
        return []
    return subcourts[1:]


def run(district, subcourt):
    save_dir = f'{base_dir}{district.lower().replace(" ","_")}/{subcourt.lower().replace(" ","_").replace(",","")}/'
    metafile = f"{save_dir}meta_{from_date}_{to_date}.csv"
    if path.exists(metafile):
        print("This has already finished..skipping..")
        return
    try:
        os.makedirs(save_dir)
    except:
        pass
    try:
        options = webdriver.ChromeOptions()
        profile = {"plugins.plugins_list": [{"enabled": False, "name": "Chrome PDF Viewer"}],
                   "download.default_directory": save_dir,
                   # "download.prompt_for_download": False,
                   # "download.directory_upgrade": True,
                   # "safebrowsing.enabled": True,
                   "download.extensions_to_open": "applications/pdf"}
        options.add_experimental_option("prefs", profile)
        # chrome_options.add_argument("--mute-audio")
        driver = webdriver.Chrome("./chromedriver", options=options)
        driver.maximize_window()
        wait = WebDriverWait(driver, 25)
        swait = WebDriverWait(driver, 10)
        driver.get(url)
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#sateist')))
        Select(driver.find_element_by_id("sateist")
               ).select_by_visible_text(district)
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#block-block-8 > div.right-accordian.english_language > button:nth-child(4)')))
        driver.find_element_by_css_selector(
            "#block-block-8 > div.right-accordian.english_language > button:nth-child(4)").click()
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#block-block-8 > div.right-accordian.english_language > div:nth-child(5) > ul > li:nth-child(4) > a')))
        current = driver.window_handles[0]
        driver.find_element_by_css_selector(
            "#block-block-8 > div.right-accordian.english_language > div:nth-child(5) > ul > li:nth-child(4) > a").click()
        wait.until(EC.number_of_windows_to_be(2))
        newWindow = [
            window for window in driver.window_handles if window != current][0]
        driver.switch_to.window(newWindow)
        wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#court_complex_code')))
        Select(driver.find_element_by_css_selector(
            "#court_complex_code")).select_by_visible_text(subcourt)
        fpath = '//*[@id="from_date"]'
        fDate = driver.find_element_by_xpath(fpath)
        fDate.clear()
        fDate.send_keys(from_date)
        # choosing To Date
        tpath = '//*[@id="to_date"]'
        tDate = driver.find_element_by_xpath(tpath)
        tDate.clear()
        tDate.send_keys(to_date)
        tDate.send_keys(u'\ue007')
        imgtotxt(driver)
        this = driver.current_window_handle
        while True:
            try:
                swait.until(EC.alert_is_present())
                driver.switch_to.alert.accept()
                driver.switch_to.window(this)
                driver.find_element_by_css_selector(
                    '#captcha_container_2 > div:nth-child(1) > div > span.secondcolumn > a > img').click()
                time.sleep(1)
                print('alert was present')
                time.sleep(2)
                imgtotxt(driver)
            except:
                print('no alert')
                w = 0
                while driver.find_element_by_css_selector('#waitmsg').is_displayed():
                    w += 1
                    time.sleep(1)
                    print("waiting...", end="\r")
                    if w//60 > 5:
                        break
                invalidCaptcha = "Invalid Captcha"
                norecord = "Record not found"
                try:
                    swait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '#errSpan > p')))
                    if driver.find_element_by_css_selector('#errSpan > p').is_displayed():
                        print("error")
                        incorrect = driver.find_element_by_css_selector(
                            '#errSpan > p').text
                        # print("text:",incorrect)
                        if incorrect == invalidCaptcha:
                            print('invalid captcha')
                            imgtotxt(driver)
                            continue
                        else:
                            if incorrect == norecord:
                                driver.quit()
                                return print('record not found')
                    else:
                        raise Exception("Record Might be available...")
                except:
                    print('record fun started')
                    try:
                        WebDriverWait(driver, 30).until(
                            EC.element_to_be_clickable((By.TAG_NAME, "tr")))
                        trs = driver.find_elements(By.TAG_NAME, "tr")
                        length = len(trs)
                        srlist = []
                        typeList = []
                        orderDateList = []
                        oList = []
                        oNumberList = []
                        for i in range(length):
                            tds = trs[i].find_elements(By.TAG_NAME, "td")
                            if(len(tds) >= 4):
                                try:
                                    url2 = (tds[3].find_element_by_css_selector(
                                        'a')).get_attribute("href")
                                except:
                                    continue
                                srlist.append(tds[0].text)
                                typeList.append(tds[1].text)
                                orderDateList.append(tds[2].text)
                                oList.append(tds[3].text)
                                session = get_request_session(driver)
                                r = session.get(url2, stream=True)
                                chunk_size = 40000
                                new_name = (str(tds[1].text).replace(
                                    "/", "_")).replace(".", "_")+str(tds[2].text)+".pdf"
                                with open(f"{save_dir}{new_name}", 'wb') as file:
                                    for chunk in r.iter_content(chunk_size):
                                        file.write(chunk)

                                oNumberList.append(f"{new_name}")

                        df = pd.DataFrame({"Sr No": srlist,
                                           "Case Type/Case Number/Case Year": typeList,
                                           "Order Date	": orderDateList,
                                           "Order Number": oList,
                                           "Order Number": oNumberList})
                        df.to_csv(f"{save_dir}meta_{from_date}_{to_date}.csv")
                        print('record function finished')
                    except:
                        print("no records found...")
                    driver.quit()
                    return
        driver.quit()
    except:
        print("Somekind of network error occured... Might need to re-run...")
        try:
            driver.quit()
        except:
            pass


def main():
    import json
    with open("districts.json") as f:
        districts = json.load(f)
    print("Districs are:", districts)
    for district in districts[s_d: e_d]:
        with open("subcourts.json") as f:
            subcourts = json.load(f)
        # get data for each subcourt and district combo...
        for subcourt in subcourts[district]:
            print("Doing:", district, subcourt)
            run(district, subcourt)


if __name__ == "__main__":
    main()
