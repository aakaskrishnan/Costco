import re
import sys
import time
import csv
import pandas as pd
import numpy as np
import zipfile
import argparse
import config
from get_gecko_driver import GetGeckoDriver
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from proxy_setup import manifest_json, get_background_js
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

class costco_scraper:

    def __init__(self, input_file_path, proxy_username, proxy_password, output_file_path):
        dict = []
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        driver = self.get_driver(proxy_username, proxy_password)
        row_list, _ = self.read_csv(input_file_path)
        end_result = list()
        for row in row_list:
            link = row['link']
            result = self.link_search(driver, link,dict)
            end_result.append(result)
        self.write_csv(output_file_path, end_result)

    def read_csv(self,input_file_path):
        row_list = []
        with open(input_file_path, 'r', newline="") as bf:
            csvf = csv.DictReader(bf, delimiter=',', quotechar='"')
            field_names = csvf.fieldnames
            for row in csvf:
                row_list.append(row)
            return row_list, field_names

    def write_csv(self,output_file_path, final_dataset):
        field_names = ["Root","SKU","Product Link","Price","Produt Rating","Review Count"]
        with open(output_file_path, 'w') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=field_names, delimiter=',', quotechar='"')
            writer.writeheader()
            for lines in final_dataset:
                for row in lines:
                    writer.writerow(row)

    def get_driver(self,proxy_username: str, proxy_password: str, debug=True):
        options = Options()

        options.add_argument("--window-size=1366,768")
        options.add_argument("--disable-notifications")
        options.add_argument('--no-sandbox')
        options.add_argument("--lang=en")

        pluginfile = 'proxy_auth_plugin.zip'
        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", get_background_js(username=proxy_username, password=proxy_password))
        options.add_extension(pluginfile)

        input_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        return input_driver

    def short_sleep(self):
        time.sleep(np.random.randint(2, 5))

    def link_search(self,driver,link,dict):
        print(link)
        driver.get(link)
        print(link)
        self.short_sleep()
        driver.refresh()
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser" )
        elements = soup.find_all("div", {"class": "col-lg-4"})
        for element in elements:
            SKU = element.find('img', {"class": "img-responsive"}).get('alt')
            product_link = element.find('a').get('href')
            try:
                price = element.find("div", {"class": "price"}).text
            except:
                price = None
            try:
                product_rating = element.find("meta", {"itemprop": "ratingValue"}).get('content')
            except:
                product_rating = None
            try:
                review_count = element.find("meta", {"itemprop": "reviewCount"}).get('content')
            except:
                review_count = None
            dict.append(
                {"Root": link,  "SKU": SKU,"Product Link":product_link,"Price": price,"Produt Rating":product_rating,"Review Count":review_count})
        try:
            pagination_link = driver.find_element(By.XPATH, "//li[@class='forward']/a").get_attribute("href")
            self.link_search(driver,pagination_link,dict)
        except:
            pass
        return dict

def main(input_file_path, proxy_username, proxy_password, output_file_path):
    scraper = costco_scraper(input_file_path, proxy_username,proxy_password, output_file_path)
    scraper
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--proxy_username', type=str, help='Username')
    parser.add_argument('--proxy_password', type=str, help='Password')
    parser.add_argument('--input_file_path', type=str, help='Input File')
    parser.add_argument('--output_file_path', type=str, help='Output File')

    args = parser.parse_args()
    main(args.input_file_path, args.proxy_username,args.proxy_password,args.output_file_path)

