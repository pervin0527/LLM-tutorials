import os
import time

from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from utils.config_utils import read_config
from utils.browser_options import load_options
from utils.crawler_utils import page_scroll_down, save_to_json


def list_items_crawling(list_items:List[WebElement], region: str):
    total_data = []
    for list_item in list_items:
        try:
            data = {"region" : region}
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
    browser = webdriver.Chrome(options=options)
    region_ids = ["depth1_btn_101000", "depth1_btn_102000", "depth1_btn_108000", "depth1_btn_106000", "depth1_btn_104000",
                  "depth1_btn_103000", "depth1_btn_105000", "depth1_btn_107000", "depth1_btn_118000", "depth1_btn_109000",
                  "depth1_btn_110000", "depth1_btn_111000", "depth1_btn_112000", "depth1_btn_113000", "depth1_btn_115000",
                  "depth1_btn_114000", "depth1_btn_116000", "depth1_btn_117000"]
    
    total_recruits = []
    for id in region_ids[:3]:
        curr_page = 1
        id = id.split("_")[-1]

        if cfg['last_page'] == 0 or cfg['last_page'] == None:
            browser.get(f"https://www.saramin.co.kr/zf_user/jobs/list/domestic?page=10000&loc_mcd={id}&tab_type=default&search_optional_item=n&search_done=y&panel_count=y&isAjaxRequest=0&page_count=50&sort=RL&type=domestic&is_param=1&isSearchResultEmpty=1&isSectionHome=0&searchParamCount=1#searchTitle")
            recruit_list_renew = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "recruit_list_renew")))
            default_list_wrap = recruit_list_renew.find_element(By.ID, "default_list_wrap")
            page_box = default_list_wrap.find_element(By.CLASS_NAME, "PageBox")
            btns = page_box.find_elements(By.CLASS_NAME, "BtnType")

            last_page = int(btns[-1].text)
             
        else:
            last_page = cfg['last_page']

        while curr_page <= last_page:
            print(curr_page, last_page)
            browser.get(f"https://www.saramin.co.kr/zf_user/jobs/list/domestic?page={curr_page}&loc_mcd={id}&tab_type=default&search_optional_item=n&search_done=y&panel_count=y&isAjaxRequest=0&page_count=50&sort=RL&type=domestic&is_param=1&isSearchResultEmpty=1&isSectionHome=0&searchParamCount=1#searchTitle")
            time.sleep(1.5)

            wrap_title_recruit = browser.find_element(By.CLASS_NAME, "wrap_title_recruit")
            region = wrap_title_recruit.find_element(By.TAG_NAME, "span").text

            recruit_list_renew = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "recruit_list_renew")))
            default_list_wrap = recruit_list_renew.find_element(By.ID, "default_list_wrap")
            page_scroll_down(browser, scroll_step=1500)

            list_body = default_list_wrap.find_element(By.CLASS_NAME, "list_body")
            list_items = list_body.find_elements(By.CLASS_NAME, "list_item")
            recruits = list_items_crawling(list_items, region)

            for recruit in recruits:
                print(recruit, "\n")
            
            total_recruits.extend(recruits)
            curr_page += 1

    os.makedirs("../data", exist_ok=True)
    save_to_json(total_recruits, "../data/saramin_raw.json")
        

    input("브라우저를 닫으려면 Enter를 누르세요.")
    browser.quit()


if __name__ == "__main__":
    cfg = read_config("./configs/config.yaml")
    main(cfg)