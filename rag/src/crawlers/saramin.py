import json
import time

from tqdm import tqdm
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from utils.browser_options import load_options
from utils.crawler_utils import page_scroll_down


class SaraminCrawler:
    def __init__(self, cfg):
        self.cfg = cfg

        options = load_options()
        self.browser = webdriver.Chrome(options=options)
        self.region_ids = [
            "depth1_btn_101000", "depth1_btn_102000", "depth1_btn_108000", "depth1_btn_106000", "depth1_btn_104000",
            "depth1_btn_103000", "depth1_btn_105000", "depth1_btn_107000", "depth1_btn_118000", "depth1_btn_109000",
            "depth1_btn_110000", "depth1_btn_111000", "depth1_btn_112000", "depth1_btn_113000", "depth1_btn_115000",
            "depth1_btn_114000", "depth1_btn_116000", "depth1_btn_117000"
        ]


    def list_items_crawling(self, list_items:List[WebElement], region: str):
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


    def recruit_list_crawling(self):
        total_recruits = []

        for id in self.region_ids:
            curr_page = 1
            id = id.split("_")[-1]

            # 지역 이름 가져오기
            self.browser.get(f"https://www.saramin.co.kr/zf_user/jobs/list/domestic?page=1&loc_mcd={id}&tab_type=default&search_optional_item=n&search_done=y&panel_count=y&isAjaxRequest=0&page_count=50&sort=RL&type=domestic&is_param=1&isSearchResultEmpty=1&isSectionHome=0&searchParamCount=1#searchTitle")
            wrap_title_recruit = self.browser.find_element(By.CLASS_NAME, "wrap_title_recruit")
            region = wrap_title_recruit.find_element(By.TAG_NAME, "span").text
            print(f"현재 지역: {region}")

            # 마지막 페이지 수 확인
            if self.cfg['last_page'] == 0 or self.cfg['last_page'] is None:
                recruit_list_renew = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "recruit_list_renew")))
                default_list_wrap = recruit_list_renew.find_element(By.ID, "default_list_wrap")
                page_box = default_list_wrap.find_element(By.CLASS_NAME, "PageBox")
                btns = page_box.find_elements(By.CLASS_NAME, "BtnType")
                last_page = int(btns[-1].text)
            else:
                last_page = self.cfg['last_page']

            with tqdm(total=last_page, desc=f"Recruit List Crawling") as page_pbar:
                while curr_page <= last_page:
                    self.browser.get(f"https://www.saramin.co.kr/zf_user/jobs/list/domestic?page={curr_page}&loc_mcd={id}&tab_type=default&search_optional_item=n&search_done=y&panel_count=y&isAjaxRequest=0&page_count=50&sort=RL&type=domestic&is_param=1&isSearchResultEmpty=1&isSectionHome=0&searchParamCount=1#searchTitle")
                    time.sleep(1.5)

                    recruit_list_renew = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "recruit_list_renew")))
                    default_list_wrap = recruit_list_renew.find_element(By.ID, "default_list_wrap")
                    page_scroll_down(self.browser, scroll_step=1500)

                    list_body = default_list_wrap.find_element(By.CLASS_NAME, "list_body")
                    list_items = list_body.find_elements(By.CLASS_NAME, "list_item")
                    recruits = self.list_items_crawling(list_items, region)

                    total_recruits.extend(recruits)
                    curr_page += 1
                    page_pbar.update(1)
            print()

        return total_recruits
    

    def recruit_post_crawling(self, recruits: List[dict]):
        total_data = []
        for recruit in tqdm(recruits, desc="Recruit Post Crawling"):
            try:
                url = recruit.get("recruit_url")
                if not url:
                    continue

                self.browser.get(url)
                time.sleep(1.5)
                
            except Exception as e:
                print(f"Error processing {recruit.get('recruit_url')}: {e}")
                continue

        return total_data