from selenium import webdriver
from selenium_stealth import stealth
import json
import gspread
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import logging
from oauth2client.service_account import ServiceAccountCredentials
from time import sleep
from datetime import datetime
import pandas as pd
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
import sys

logging.basicConfig(
    level= logging.INFO,
    format= '%(asctime)s - [%(levelname)s] - %(message)s',
    handlers= [
        logging.FileHandler('test3.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
client = gspread.authorize(creds)
planner = client.open("Planilha books to scrape").sheet1

class Scraper:
    def __init__(self):
        self.datas = []
        self.url = None
        self.bot = None
        self.informations = {}

    def open_json(self):
        while True:
            try:
                with open('config.json', 'r', encoding='utf-8') as v:
                    self.informations = json.load(v)
                logging.info('json opened.')
                break
            except FileNotFoundError:
                logging.error('detected error in open json, trying again in 5 seconds.')
                sleep(5)
                continue

    def acess_site(self):
        while True:
            try:
                self.open_json()

                config = Options()
                config.add_argument("--headless")
                config.add_argument("--incognito")
                config.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")

                self.bot = webdriver.Chrome(options=config)
                self.bot.get(self.informations["url"])
                logging.info('site opened with success.')
                break
            except ConnectionError:
                logging.critical('detected error in acess site, verify the internet, trying again in 5 seconds.')
                sleep(5)
                continue

    def take_datas(self):
        logging.info('starting the process of collect datas.')
        while True:
            try:
                wait = WebDriverWait(self.bot, 15)
                try:
                    boxes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//article[contains(@class, 'product_pod')]")))
                except TimeoutException:
                    logging.critical('boxes din´t find, verify the XPATH')
                    sys.exit()

                for box in boxes:
                    title = box.find_element(By.XPATH, ".//h3/a").get_attribute('title')
                    stars = box.find_element(By.XPATH, ".//p[contains(@class, 'star-rating')]").get_attribute('class')
                    clean_stars = stars.replace('star-rating', '').strip()
                    price = box.find_element(By.XPATH, ".//p[contains(@class, 'price_color')]").text
                    clean_price = price.replace('£', '')
                    link = box.find_element(By.XPATH, ".//a[@href]").get_attribute('href')

                    product = {
                        'title': title,
                        'stars': clean_stars,
                        'price': clean_price,
                        'datetime': datetime.now().strftime("%d/%m/%Y %H:%M"),
                        'link': link
                    }

                    if product not in self.datas:
                        if product['stars'] in self.informations["stars"]:
                            self.datas.append(product)  

                try:
                    button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'next')]")))
                    button.click()
                    sleep(1)

                except TimeoutException:
                    logging.info('end of the pages, loading informations.')
                    break

            except AttributeError:
                logging.error('information undetected, trying again in 5 seconds.')
                sleep(5)
                continue

        if self.bot:    
            self.bot.quit()
            logging.info('the bot finished the process of take datas.')
                

    def save_datas(self, name_file="test3.xlsx"):
        while True:
            try:
                df = pd.DataFrame(self.datas)
                df.to_excel(name_file, index=False)
                df.to_csv("test3.csv", encoding="utf-8-sig", sep=";", index=False)
                google_datas = [list(item.values()) for item in self.datas]
                planner.append_rows(google_datas)
                logging.info('process os save datas was finished with success.')
                break

            except FileNotFoundError:
                logging.critical('function save datas din´t find the locate to save, trying again in 10 seconds.')
                sleep(10)
                continue

scrap3 = Scraper()
scrap3.acess_site()
scrap3.take_datas()
scrap3.save_datas()
