import time

from typing import Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from src.crawler.utils.selenium_utils import set_webdriver, wait_for_element
from src.crawler.utils.data_utils import extract_company_id

from app.utils.logging import logger


def jobplanet_login(driver:WebDriver):
    logger.info("잡플래닛 로그인 시작")
    while True:
        driver.get("https://www.jobplanet.co.kr/users/sign_in?_nav=gb")
        try:
            contents_wrap = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="contents_wrap"]'))
            )
            break  # 성공적으로 찾으면 반복문 탈출

        except:
            logger.warning("contents_wrap을 찾지 못했습니다. 다시 시도합니다.")
            time.sleep(1)  # 잠시 대기 후 다시 시도

    contents = contents_wrap.find_element(By.ID, "contents")
    new_user = contents.find_element(By.ID, "new_user")

    sign_in = new_user.find_element(By.ID, "signInSignInCon")
    login_container = sign_in.find_element(By.CLASS_NAME, 'signInsignIn_wrap')
    sign_wrap = login_container.find_element(By.CLASS_NAME, "sign_wrap")
    email_section = sign_wrap.find_element(By.CLASS_NAME, "section_email")

    user_email = email_section.find_element(By.ID, "user_email")
    user_email.send_keys("admin@gravylab.co.kr")

    user_password = email_section.find_element(By.ID, "user_password")
    user_password.send_keys("glab0110!!")

    sign_in_button = sign_wrap.find_element(By.CLASS_NAME, "btn_sign_up")
    sign_in_button.click()

    logger.info("로그인 완료")
    

def google_search_jobplanet_ids(driver:WebDriver, target_urls:List[str], company_name:str, company_url:Optional[str] = None, company_bizno:Optional[str] = None):
    logger.info(f"구글 검색 시작: {company_name} {company_bizno} {company_url}")
    sub_driver = set_webdriver()

    try:    
        driver.get(f"https://www.google.com/search?q=잡플래닛+{company_name}+기업+복지")
        time.sleep(0.5)

        container = driver.find_element(By.XPATH, '//*[@id="rso"]')
        items = []
        for class_name in ["hlcw0c", "MjjYud"]:
            items.extend(container.find_elements(By.CLASS_NAME, class_name))

        jobplanet_ids = set()
        for idx, item in enumerate(items):
            try:
                searched_url = item.find_element(By.TAG_NAME, 'a').get_attribute("href")
                sub_driver.get(searched_url)

                header = sub_driver.find_element(By.ID, "CompaniesHeader")
                companies_info = header.find_element(By.ID, "CompaniesInfo")
                jobplanet_company_name = companies_info.find_element(By.ID, "companyName").text
                jobplanet_company_url = companies_info.find_element(By.XPATH, '//*[@id="CompaniesInfo"]/div[2]/div/div[2]/div/a').get_attribute("href")

                logger.info(f"idx : {idx}, searched_url : {searched_url}")
                jobplanet_company_id = extract_company_id(searched_url)
                logger.info(f"잡플래닛 데이터 -  회사명 : {jobplanet_company_name}, 회사 id : {jobplanet_company_id}, 회사 링크 : {jobplanet_company_url}")

                if jobplanet_company_id is None:
                    logger.info(f"잡플래닛 id가 없습니다.")
                    continue

                if any(url in searched_url for url in target_urls):
                    logger.info(f"company_name : {company_name}, jobplanet_company_name : {jobplanet_company_name}")
                    logger.info(f"company_url : {company_url}, jobplanet_company_url : {jobplanet_company_url}")

                    if company_url in jobplanet_company_url:
                        logger.info(f"ADDED\n")
                        jobplanet_ids.add(jobplanet_company_id)
                    else:
                        logger.info(f"NOT ADDED\n")
                
            except:
                continue

        return list(jobplanet_ids)

    except Exception as e:
        logger.warning(f"구글 검색 실패: {e}")
        return []
    
    finally:
        sub_driver.quit()
    

def get_jobplanet_welfare(driver:WebDriver, company_name:str, company_url:str, company_bizno:str, target_urls:List[str]):
    try:
        jobplanet_ids = google_search_jobplanet_ids(driver, 
                                                    target_urls=target_urls,
                                                    company_name=company_name, 
                                                    company_url=company_url,
                                                    company_bizno=company_bizno)
        
        logger.info(f"후보 수 : {len(jobplanet_ids)}")
        for idx, jobplanet_id in enumerate(jobplanet_ids):
            curr_url = f"https://www.jobplanet.co.kr/companies/{jobplanet_id}/benefits"
            logger.info(f"[{idx+1}/{len(jobplanet_ids)}] curr_url : {curr_url}")


        jobplanet_login(driver)
        time.sleep(1)
        
        logger.info(f"[잡플래닛] {curr_url} 로드 중...")
        driver.get(curr_url)

        WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')        
        body_wrap = driver.find_element(By.CLASS_NAME, "body_wrap")
        cmp_hd = wait_for_element(driver, By.XPATH, '/html/body/div[1]/div[3]')    
        logger.info(f"[잡플래닛] {curr_url} 로드 완료")

        new_top_bnr = cmp_hd.find_element(By.CLASS_NAME, "new_top_bnr")
        top_bnr_container = new_top_bnr.find_element(By.CLASS_NAME, "top_bnr_container")
        top_bhr_box = top_bnr_container.find_element(By.CLASS_NAME, "top_bhr_box")

        company_info_box = top_bhr_box.find_element(By.CLASS_NAME, "company_info_box")
        about_company = company_info_box.find_element(By.CLASS_NAME, "about_company")
        target_url = about_company.find_element(By.CLASS_NAME, "info").find_element(By.TAG_NAME, "a").get_attribute("href")

        if company_url in target_url:
            contents_wrap = body_wrap.find_element(By.ID, "contents_wrap")
            contents = contents_wrap.find_element(By.ID, "contents")
            main_contents = contents.find_element(By.ID, "mainContents")

            welfare_container = main_contents.find_element(By.ID, "welfareReviewsContainer")
            welfare_tab = welfare_container.find_element(By.ID, "welfareReviewTab")

            try:
                welfare_item_list = welfare_tab.find_element(By.ID, "welfare-item-list")
                welfare_provision = welfare_item_list.find_element(By.CLASS_NAME, "welfare-provision")
                section = welfare_provision.find_element(By.CLASS_NAME, "welfare-provision__section")

                welfare_provision_list = section.find_element(By.CLASS_NAME, "welfare-provision__list")
                items = welfare_provision_list.find_elements(By.CLASS_NAME, "welfare-provision__item")

                logger.info(f"[잡플래닛] {len(items)}개의 복지 정보 찾음")
                total_data = {}
                for item in items:
                    title = item.find_element(By.CLASS_NAME, "welfare-bullet__tit").text
                    welfare_items = item.find_elements(By.CLASS_NAME, "welfare-bullet__item")

                    curr_data = []
                    for welfare_item in welfare_items:
                        curr_data.append(welfare_item.text)
                    
                    total_data[title] = curr_data

                logger.info(f"[잡플래닛] 복지 정보 수집 완료")
                return total_data

            except Exception as e:
                logger.error(f"[잡플래닛] 복지 정보를 찾지 못함 : {e}")

    except Exception as e:
        logger.error(f"[잡플래닛] 복지 수집 중 오류 발생: {e}")
        return []