import re
import os
import cv2
import time
import unicodedata

from PIL import Image
from tqdm import tqdm
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from transformers import TrOCRProcessor, AutoTokenizer, AutoModelForImageTextToText


from utils.browser_options import load_options
from utils.crawler_utils import page_scroll_down

from ocr.text_detector.detection import detect
from ocr.text_detector.file_utils import saveResult
from ocr.text_detector.model_utils import load_model
from ocr.text_detector.image_processor import load_image

from llm.chatgpt import generate
from llm.prerpocess import img_preprocessing
from llm.prompts import recruit_txt_prompt, recruit_img_prompt


class SaraminCrawler:
    def __init__(self, cfg, client):
        self.cfg = cfg
        self.client = client

        options = load_options(self.cfg)
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
                    page_scroll_down(self.browser, scroll_step=self.cfg['scroll_step'])

                    list_body = default_list_wrap.find_element(By.CLASS_NAME, "list_body")
                    list_items = list_body.find_elements(By.CLASS_NAME, "list_item")
                    recruits = self.list_items_crawling(list_items, region)

                    total_recruits.extend(recruits)
                    curr_page += 1
                    page_pbar.update(1)
            print()

        return total_recruits
    

    def column_process(self, cols:List[WebElement]):
        data = {}
        for col in cols:
            dls = col.find_elements(By.TAG_NAME, "dl")
            for dl in dls:
                dt = dl.find_element(By.TAG_NAME, "dt").text

                if dt != "필수사항":
                    dd = dl.find_element(By.TAG_NAME, "dd").text
                    if dt == "급여":
                        dd = dd.split("\n")[0]
                    elif dt == "근무지역":
                        dd = " ".join(dd.split(" ")[:-1])

                else:
                    dd = dl.find_element(By.TAG_NAME, "dd")
                    tool_tip_wrap = dd.find_element(By.CLASS_NAME, "toolTipWrap")
                    tool_tip_wrap.click()

                    tool_tip = tool_tip_wrap.find_element(By.CLASS_NAME, "toolTip")
                    tool_tip_cont = tool_tip.find_element(By.CLASS_NAME, "toolTipCont")
                    tool_tip_txt = tool_tip_cont.find_element(By.CLASS_NAME, "toolTipTxt")
                    lis = tool_tip_txt.find_elements(By.TAG_NAME, "li")

                    details = {}
                    for li in lis:
                        key = li.find_element(By.TAG_NAME, "span").text.strip()
                        value = li.text.replace(key, "").strip().split(", ")
                        details[key] = value
                    
                    dd = details
                data.update({dt: dd})
        return data
    

    def scroll_and_capture(self, rec_id, browser, element):
        output_dir = f"{self.cfg['save_path']}/images"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 요소 위치와 크기 가져오기
        location = element.location
        size = element.size
        total_width, total_height = size['width'], size['height']
        viewport_height = browser.execute_script("return window.innerHeight")

        # 스크롤 위치 초기화
        scroll_y = 0
        screenshot_index = 0
        img_files = []
        while scroll_y < total_height:
            # 현재 스크롤 위치 설정
            browser.execute_script(f"window.scrollTo(0, {location['y'] + scroll_y});")
            time.sleep(1)  # 스크롤 후 렌더링 대기

            # 스크린샷 저장
            screenshot_path = os.path.join(output_dir, f"{rec_id}_{screenshot_index:>04}.png")
            browser.save_screenshot(screenshot_path)
            img_files.append(screenshot_path)

            scroll_y += viewport_height
            screenshot_index += 1

        return img_files


    def extract_text_from_images(self, img_files, detector, processor, tokenizer, recognizer):
        result_folder = f"{self.cfg['save_path']}/results"
        os.makedirs(result_folder, exist_ok=True)
        
        all_texts = []  # 모든 텍스트를 저장할 리스트
        for img_file in img_files:
            # 이미지 불러오기
            image = load_image(img_file)
            
            # 텍스트 영역 감지
            bboxes, polys, score_text = detect(detector, 
                                               image, 
                                               text_thres=self.cfg['text_thres'], 
                                               link_thres=self.cfg['link_thres'], 
                                               low_text=self.cfg['low_text'], 
                                               cuda=self.cfg['cuda'],
                                               poly=self.cfg['poly'],
                                               refine_net=self.cfg['refine_net'])
            
            # 감지된 각 영역에서 텍스트 추출
            for poly in polys:
                x_min = int(min(poly[:, 0]))
                y_min = int(min(poly[:, 1]))
                x_max = int(max(poly[:, 0]))
                y_max = int(max(poly[:, 1]))
                
                # 영역 잘라내기
                cropped_image = image[y_min:y_max, x_min:x_max]
                cropped_pil_image = Image.fromarray(cropped_image)
                
                # TrOCR 모델을 사용해 텍스트 추출
                pixel_values = processor(cropped_pil_image, return_tensors="pt").pixel_values
                generated_ids = recognizer.generate(pixel_values, max_length=64)
                generated_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
                generated_text = unicodedata.normalize("NFC", generated_text)
                
                all_texts.append(generated_text)
            
            # 결과 마스크 저장
            filename, file_ext = os.path.splitext(os.path.basename(img_file))
            mask_file = result_folder + "/res_" + filename + '_mask.jpg'
            cv2.imwrite(mask_file, score_text)
            saveResult(img_file, image[:, :, ::-1], polys, dirname=result_folder)

        return " ".join(all_texts)


    def two_stage_ocr(self, img_files, detector, processor, tokenizer, recognizer):
        texts = self.extract_text_from_images(img_files, detector, processor, tokenizer, recognizer)

        return texts
    

    def multi_modal_ocr(self, img_files, img_prompt, temperature):
        texts = []
        for img_file in img_files:
            binary_img = img_preprocessing(img_file)
            text = generate(client=self.client, prompt=img_prompt, input=binary_img, temperature=temperature)
            texts.append(text)
        
        return texts


    def recruit_post_crawling(self, recruits: List[dict]):
        if self.cfg['ocr_method'] == "two_stage":
            print(f"Method : Two Stage OCR")
            detector = load_model(self.cfg)
            processor = TrOCRProcessor.from_pretrained("ddobokki/ko-trocr") 
            tokenizer = AutoTokenizer.from_pretrained("ddobokki/ko-trocr")
            recognizer = AutoModelForImageTextToText.from_pretrained("ddobokki/ko-trocr")
        
        elif self.cfg['ocr_method'] == "llm":
            print(f"Method : Large Multi Modal")
            img_prompt = recruit_img_prompt()

        crawling_data = []
        failed_data = []
        for idx, recruit in enumerate(recruits):
            print("=" * 100)
            print(f"{idx:>07}")
            url = recruit.get("recruit_url")
            
            if not url:
                continue
            
            curr_data = {}
            match = re.search(r'rec_idx=(\d+)', url)
            rec_id = match.group(1) if match else None
            curr_data.update({
                'id' : rec_id, 
                "url" : url, 
                "region" : recruit.get("region"), 
                "company_name" : recruit.get("company_name"),
                "title" : recruit.get("recruit_title"), 
                "metadata" : recruit.get("recruit_meta_data"),

            })

            start_time = time.time()
            self.browser.get(url)
            time.sleep(1.5)

            wrap_jv_cont = self.browser.find_elements(By.CLASS_NAME, "wrap_jv_cont")[0]
            
            jv_summary = wrap_jv_cont.find_element(By.CLASS_NAME, "jv_summary")
            cont = jv_summary.find_element(By.CLASS_NAME, "cont")
            cols = cont.find_elements(By.CLASS_NAME, "col")
            summary_data = self.column_process(cols)

            jv_detail = wrap_jv_cont.find_element(By.CLASS_NAME, "jv_detail")
            try:
                # jv_benefit 클래스명을 가진 원소 찾기
                jv_benefit = wrap_jv_cont.find_element(By.CLASS_NAME, "jv_benefit")
                cont = jv_benefit.find_element(By.CLASS_NAME, "cont")
                btn_more_cont = cont.find_element(By.CLASS_NAME, "btn_more_cont")
                btn_more_cont.click()

            except NoSuchElementException:
                # jv_benefit을 찾지 못한 경우 아무 작업도 수행하지 않음
                pass

            img_files = self.scroll_and_capture(rec_id, self.browser, jv_detail)
            if self.cfg['ocr_method'] == "two_stage":
                detail_data = self.two_stage_ocr(img_files, detector, processor, tokenizer, recognizer)
            else:
                detail_data = self.multi_modal_ocr(img_files, img_prompt, self.cfg['temperature'])

            prompt = recruit_txt_prompt()
            raw_data = ", ".join(f"{key}: {value}" for key, value in summary_data.items()) + detail_data
            processed_data = generate(self.client, prompt, raw_data, self.cfg['temperature'])

            curr_data.update({"recruit_main" : processed_data})
            crawling_data.append(curr_data)

            if self.cfg['debug']:
                print(f">>URL\n{url}\n")
                print(f">>Summary\n{summary_data}\n")
                print(f">>Detail\n{detail_data}\n")
                print(f">>Regenerated\n{processed_data}\n")
            else:
                print(f">>Saved Data\n{curr_data}\n")

            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Processed in {elapsed_time:.2f} seconds\n\n")

        return crawling_data, failed_data