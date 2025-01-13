import re
import os
import cv2
import time
import requests
import unicodedata

from PIL import Image
from tqdm import tqdm
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

from transformers import TrOCRProcessor, AutoTokenizer, AutoModelForImageTextToText

from ocr.text_detector.detection import detect
from ocr.text_detector.file_utils import saveResult
from ocr.text_detector.model_utils import load_model
from ocr.text_detector.image_processor import load_image

from llm.chatgpt import generate
from llm.prerpocess import img_preprocessing
from llm.prompts import recruit_txt_prompt, recruit_img_prompt

from db.save import save_crawl_data

from utils.browser_options import load_options
from utils.crawler_utils import page_scroll_down


class WantedCrawler:
    def __init__(self, cfg, client):
        self.cfg = cfg
        self.client = client
        self.url = "https://www.wanted.co.kr/wdlist?country=kr&job_sort=job.latest_order&years=-1&locations=all"

        options = load_options(self.cfg)
        self.browser = webdriver.Chrome(options=options)
        self.browser.get(self.url)


    def find_elements_with_retry(self, by, value, max_retries=1):
        retries = 0
        while retries < max_retries:
            elements = self.browser.find_elements(by, value)
            if elements:
                return elements
            retries += 1
            time.sleep(0.5)
        return []
    

    def fetch_job_data(self, api_url, url=None):
        try:
            # GET 요청 보내기
            response = requests.get(api_url)
            
            # 요청이 성공적으로 완료되었는지 확인 
            response.raise_for_status()
            
            # JSON 형식으로 응답 데이터를 파싱
            job_data = response.json()

            # share_link가 없거나 null인 경우 url 파라미터 값을 할당
            if 'share_link' not in job_data or job_data['share_link'] is None:
                job_data['share_link'] = url
                
            return job_data

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"An error occurred: {err}")


    def scroll_and_collect_incremental_urls(self):
        base_url = "https://www.wanted.co.kr/wd/"
        
        last_height = self.browser.execute_script("return document.body.scrollHeight")
        total_divs = 0
        index = 1

        dataset = []
        while True:
            # 페이지의 끝까지 스크롤
            body_element = self.browser.find_element(By.TAG_NAME, 'body')
            body_element.send_keys(Keys.END)
            
            try:
                # 새로운 요소가 로드될 때까지 기다림
                WebDriverWait(self.browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'footer')))
            except:
                pass            
            time.sleep(3)
            
            # 새로운 페이지 높이 계산
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            
            # 필요한 요소의 셀렉터 정의
            selector = ("#__next > div.JobList_JobList__Qj_5c > div.JobList_JobList__contentWrapper__3wwft > ul > li")
            
            # 현재 페이지에서 새로 추가된 <div> 요소 찾기
            elements = self.find_elements_with_retry(By.CSS_SELECTOR, selector)
            new_divs = elements[total_divs:]  # total_divs 이후의 요소들만 처리
            for element in new_divs:
                try:
                    link = element.find_element(By.TAG_NAME, 'a')
                    url = link.get_attribute('href')
                    if url:
                        if url.startswith(base_url):
                            company_code = url[len(base_url):]
                            print("=" * 100)
                            print(f"Data {index} processed for company_code: {company_code}")
                            
                            api_url = f"https://www.wanted.co.kr/api/v4/jobs/{company_code}"
                            print(api_url)

                            data = self.fetch_job_data(api_url, url)
                            print(data, "\n")
                            time.sleep(0.1)
                            
                            dataset.append(data)
                            # save_crawl_data(data)
                            index += 1

                            if index > self.cfg['max_job_items']:
                                print(f"Index limit reached: {index}. Stopping scroll.")
                                return dataset

                except StaleElementReferenceException:
                    continue
            
            total_divs += len(new_divs)
            
            # 새로운 높이가 이전 높이와 같으면 스크롤 종료
            if new_height == last_height:
                print(f"Scrolling stopped. Final page height: {new_height}")
                break
            
            last_height = new_height