import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from app.utils.logging import logger
from src.crawler.web_tree import set_webdriver

def login_jobplanet(driver):
    driver.find_element(By.XPATH, '//*[@id="user_email"]').send_keys("admin@gravylab.co.kr")
    driver.find_element(By.XPATH, '//*[@id="user_password"]').send_keys("glab0110!!")
    driver.find_element(By.XPATH, '//*[@id="signInSignInCon"]/div[2]/div/section[2]/fieldset/button').click()
    time.sleep(0.5)


def set_company_name(driver, company_name):
    driver.find_element(By.XPATH, '//*[@id="search_bar_search_query"]').send_keys(company_name)
    driver.find_element(By.XPATH, '//*[@id="search_bar_search_query"]').send_keys(Keys.ENTER)
    container = driver.find_element(By.XPATH, '/html/body/div[1]/main/div[1]/div/div/div[1]/div[2]/ul')
    items = container.find_elements(By.TAG_NAME, "a")
    
    target_item = items[0]
    target_item.click()

    
def crawl_jobplanet(company_name):
    driver = set_webdriver("https://www.jobplanet.co.kr/users/sign_in?_nav=gb")
    login_jobplanet(driver)
    set_company_name(driver, company_name)

    time.sleep(30)
    driver.quit()