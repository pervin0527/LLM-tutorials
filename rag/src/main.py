import os
import time

from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from utils.config_utils import read_config
from utils.browser_options import load_options
from utils.crawler_utils import region_scroll_down, page_scroll_down


def list_items_crawling(browser, list_items:List[WebElement]):
    page_scroll_down(browser)

    total_data = []
    for list_item in list_items:
        try:
            data = {}
            box_item = list_item.find_element(By.TAG_NAME, "div")

            company_nm = box_item.find_element(By.CLASS_NAME, "company_nm")
            company_name = company_nm.find_element(By.TAG_NAME, "a").text
            company_url = company_nm.find_element(By.TAG_NAME, "a").get_attribute("href")
            data.update({"company_name" : company_name, "company_url" : company_url})


            notification_info = list_item.find_element(By.CLASS_NAME, "notification_info")
            anchor = notification_info.find_element(By.TAG_NAME, "a")
            recruit_title = anchor.get_attribute("title")
            recruit_url = anchor.get_attribute("href")

            job_sector_spans = notification_info.find_element(By.CLASS_NAME, "job_sector").find_elements(By.TAG_NAME, "span")
            recruit_metadata = [span.text for span in job_sector_spans]

            data.update({"recruit_title" : recruit_title, "recruit_url" : recruit_url, "recruit_meta_data" : recruit_metadata})
            total_data.append(data)

        except:
            continue

    return total_data


def main(cfg):
    options = load_options()
    os.makedirs(cfg['screenshot_path'], exist_ok=True)
    
    browser = webdriver.Chrome(options=options)
    browser.get(cfg['saramin_url'])
    browser.save_screenshot(f"{cfg['screenshot_path']}/sc_00.png")
    
    sp_main_wrapper = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "sp_main_wrapper")))
    wrap_depth_category = browser.find_element(By.CLASS_NAME, "wrap_depth_category ")
    overview = wrap_depth_category.find_element(By.CLASS_NAME, "overview")

    region_ids = ["depth1_btn_101000", "depth1_btn_102000", "depth1_btn_108000", "depth1_btn_106000", "depth1_btn_104000",
                  "depth1_btn_103000", "depth1_btn_105000", "depth1_btn_107000", "depth1_btn_118000", "depth1_btn_109000",
                  "depth1_btn_110000", "depth1_btn_111000", "depth1_btn_112000", "depth1_btn_113000", "depth1_btn_115000",
                  "depth1_btn_114000", "depth1_btn_116000", "depth1_btn_117000"]
    
    total_recruits = []
    for id in region_ids:
        if id == "depth1_btn_115000":
            region_scroll_down(overview, browser)

        item = overview.find_element(By.ID, id)
        item.click()

        search_btn = sp_main_wrapper.find_element(By.ID, "search_btn")
        search_btn.click()

        list_tab = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "list_tab")))
        common_company_tab = list_tab.find_elements(By.TAG_NAME, "li")[1]
        common_company_tab.click()

        recruit_list_renew = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "recruit_list_renew")))
        default_list_wrap = recruit_list_renew.find_element(By.ID, "default_list_wrap")
        page_box = default_list_wrap.find_element(By.CLASS_NAME, "PageBox")

        btns = page_box.find_elements(By.CLASS_NAME, "BtnType")

        recruit_list_renew = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "recruit_list_renew")))
        default_list_wrap = recruit_list_renew.find_element(By.ID, "default_list_wrap")

        page_box = default_list_wrap.find_element(By.CLASS_NAME, "PageBox")

        list_body = default_list_wrap.find_element(By.CLASS_NAME, "list_body")
        list_items = list_body.find_elements(By.CLASS_NAME, "list_item")
        print(len(list_items))

        time.sleep(3)
        recruits = list_items_crawling(browser, list_items)

        for recruit in recruits:
            print(recruit, "\n")
        
        total_recruits.extend(recruits)
        
        break
        

    input("브라우저를 닫으려면 Enter를 누르세요.")
    browser.quit()


if __name__ == "__main__":
    cfg = read_config("./configs/config.yaml")
    main(cfg)