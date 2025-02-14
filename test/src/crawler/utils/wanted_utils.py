import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver

from src.crawler.utils.selenium_utils import set_webdriver, wait_for_element

from app.utils.logging import logger


def wanted_login(driver:WebDriver):
    try:
        driver.get("https://id.wanted.jobs/login?service=wanted&step=PASSWORD_ENTRY")
        time.sleep(1)

        section = driver.find_element(By.CLASS_NAME, "css-cvaybd").find_element(By.CLASS_NAME, "css-9bdxp9")
        form = section.find_element(By.CLASS_NAME, "css-e130a2")

        email_input = form.find_element(By.ID, "email")
        email_input.send_keys("admin@gravylab.co.kr")

        password_div = form.find_element(By.CLASS_NAME, "css-1dxhdfz")
        password_input = password_div.find_element(By.CLASS_NAME, "css-1sbrczv")
        password_input.send_keys("glab0110!!")

        login_button = form.find_element(By.CLASS_NAME, "css-14q7s2s")
        login_button.click()

        logger.info(f"[원티드] 로그인 완료 {driver.current_url}")
        time.sleep(1)

        driver.get("https://www.wanted.co.kr")
        logger.info(f"[원티드] 메인 페이지 이동 {driver.current_url}")
        time.sleep(1)

    except Exception as e:
        logger.error(f"[원티드] 로그인 실패: {e}")


def wanted_search_company(driver:WebDriver, company_name:str, company_url:str, company_bizno:str):
    try:
        sub_driver = set_webdriver()
        
        main_container = driver.find_element(By.ID, "__next")
        nav_bar_container = main_container.find_element(By.CLASS_NAME, "NavBar_className__H6bPC")
        nav_bar = nav_bar_container.find_element(By.CLASS_NAME, "MainBar_MainBarNav__eLU8g")

        aside_container = nav_bar.find_element(By.CLASS_NAME, "Aside_aside__vBaBA")
        aside = aside_container.find_element(By.CLASS_NAME, "Aside_asideList__QHkRQ")

        search_icon = aside.find_elements(By.TAG_NAME, "li")[0]
        search_btn = search_icon.find_element(By.CLASS_NAME, 'Aside_searchButton__rajGo')
        search_btn.click()
        time.sleep(0.5)

        nav_search_bar = nav_bar_container.find_element(By.ID, "nav_searchbar").find_element(By.CLASS_NAME, "SearchBar_SearchBar__ZAr_1")
        search_input_container = nav_search_bar.find_element(By.CLASS_NAME, "SearchBar_SearchInputLine__BbDX9")
        search_input = search_input_container.find_element(By.CLASS_NAME, "SearchInput_SearchInput__ssVOa")
        search_input.send_keys(company_name)
        search_input.send_keys(Keys.ENTER)

        logger.info(f"[원티드] 회사 검색 완료 {driver.current_url}")
        time.sleep(1)

        search_container = main_container.find_element(By.ID, "search_tabpanel_overview")
        company_list = search_container.find_elements(By.CLASS_NAME, "SearchCompanyCard_container__HIPPs")
        logger.info(f"[원티드] 회사 검색 결과 수 : {len(company_list)}")

        wanted_ids = []
        for idx, card in enumerate(company_list):
            anchor = card.find_element(By.CLASS_NAME, "SearchCompanyCard_inner__kZD3m")
            searched_url = anchor.get_attribute("href")
            searched_name = anchor.get_attribute("data-company-name")
            searched_id = anchor.get_attribute("data-company-id")

            logger.info(f"[원티드] [{idx+1}/{len(company_list)}] : {searched_name} {searched_url} {searched_id}")

            sub_driver.get(searched_url)
            time.sleep(1)

            sub_main_container = sub_driver.find_element(By.ID, "__next")
            company_info_container = sub_main_container.find_element(By.CLASS_NAME, "wds-1q5hgpy")
            fold_btn = company_info_container.find_element(By.CLASS_NAME, "wds-evw7fo")
            fold_btn.click()

            text_container = company_info_container.find_element(By.CLASS_NAME, "wds-1gealz5")
            anchor = text_container.find_element(By.TAG_NAME, "a")
            wanted_comp_url = anchor.get_attribute("href")

            logger.info(f"원티드 url : {wanted_comp_url}, 입력 url : {company_url}")
            logger.info(f"원티드 이름 : {searched_name}, 입력 이름 : {company_name}")
            if company_name in searched_name and company_url in wanted_comp_url:
                wanted_ids.append(searched_id)
                logger.info("ADDED\n")
            else:
                logger.info("NOT ADDED\n")

        return wanted_ids

    except Exception as e:
        logger.error(f"[원티드] 회사 검색 실패: {e}")
        return []
    
    finally:
        sub_driver.quit()


def extract_salary_data(section, container_class_name, label_class_name, salary_type, company_name):
    """
    연봉 정보를 추출하는 공통 함수
    """
    try:
        logger.info(f"[원티드] '{salary_type}' 정보 수집 시작")
        salary_data = {}

        # 연봉 정보가 포함된 컨테이너 찾기
        salary_container = section.find_element(By.CLASS_NAME, container_class_name)

        # 연봉 상단 정보 (백분위수 등) 가져오기
        salary_header = salary_container.find_element(By.CLASS_NAME, "ChartSummary_wrapper__TkKe3")
        salary_percentile = salary_header.find_element(By.CLASS_NAME, "ChartSummary_wrapper__percentile__nWzXY")
        logger.info(f"{salary_type} 백분위수: {salary_percentile.text}")

        # 차트에서 X축 값 (연도 또는 기타 정보) 가져오기
        chart_container = salary_container.find_element(By.CLASS_NAME, "recharts-responsive-container")
        xaxis = chart_container.find_element(By.CLASS_NAME, "recharts-xAxis")
        xaxis_ticks = xaxis.find_elements(By.CLASS_NAME, "recharts-cartesian-axis-tick")
        logger.info(f"{salary_type} xaxis_ticks 개수: {len(xaxis_ticks)}")

        xaxis_tick_texts = []
        for tick in xaxis_ticks:
            tick_text = tick.text
            if "." in tick_text:
                tick_text = company_name
            xaxis_tick_texts.append(tick_text)

        # 차트에서 연봉 값 가져오기
        chart_bar = chart_container.find_element(By.CLASS_NAME, "recharts-bar")
        chart_bar_labels = chart_bar.find_element(By.CLASS_NAME, "recharts-label-list")
        labels = chart_bar_labels.find_elements(By.CLASS_NAME, label_class_name)
        logger.info(f"{salary_type} labels 개수: {len(labels)}")

        if len(labels) != len(xaxis_tick_texts):
            logger.warning(f"[원티드] '{salary_type}'에서 X축 개수와 라벨 개수가 일치하지 않음! (xaxis: {len(xaxis_tick_texts)}, labels: {len(labels)})")

        for idx, label in enumerate(labels):
            if idx < len(xaxis_tick_texts):
                salary_data[xaxis_tick_texts[idx]] = label.text
            else:
                logger.warning(f"[원티드] '{salary_type}' 라벨 인덱스 초과: {label.text}")

        salary_data["백분위수"] = salary_percentile.text
        logger.info(f"{salary_type} 수집 완료: {salary_data}")
        return salary_data

    except Exception as e:
        logger.error(f"[원티드] '{salary_type}' 정보를 찾지 못했습니다.: {e}")
        return None


def get_wanted_welfare(driver: WebDriver, company_name: str, company_url: str, company_bizno: str):
    """
    기업의 연봉 정보를 수집하는 함수
    """
    try:
        wanted_login(driver)
        wanted_ids = wanted_search_company(driver, company_name, company_url, company_bizno)
        logger.info(f"원티드 회사 검색 결과 수 : {len(wanted_ids)}")

        total_data = {}
        for id in wanted_ids:
            curr_url = f"https://www.wanted.co.kr/company/{id}?inflow=insight"
            logger.info(f"curr_url : {curr_url}")
            driver.get(curr_url)
            time.sleep(2)

            logger.info(f"[원티드] 기업 연봉 정보 수집 시작")
            main_container = driver.find_element(By.ID, "__next")
            company_detail_container = main_container.find_element(By.CLASS_NAME, "CompanyDetail_CompanyDetail__Content__s7uXb")

            sections = company_detail_container.find_elements(By.CLASS_NAME, "CompanyCard_CompanyCard__LBbfm")
            logger.info(f"[원티드] 기업 연봉 정보 섹션 수: {len(sections)}")

            for section in sections:
                title = section.find_element(By.CLASS_NAME, "wds-apdtzg")
                logger.info(f"[원티드] 섹션명: {title.text}")

                if "연봉" in title.text:
                    # 평균 연봉 수집
                    avg_salary_data = extract_salary_data(
                        section,
                        "AverageSalaryChart_wrapper__chartContents__g2ono",  # 컨테이너 클래스
                        "AverageSalaryChart_wrapper__text__8R55J",  # 라벨 클래스
                        "평균 연봉",
                        company_name
                    )
                    if avg_salary_data:
                        total_data["평균 연봉"] = avg_salary_data

                    # 올해 입사자 평균 연봉 수집
                    new_salary_data = extract_salary_data(
                        section,
                        "HiredAverageSalaryChart_wrapper__chartContents__J3GRA",  # 컨테이너 클래스
                        "HiredAverageSalaryChart_wrapper__text__F1ZDM",  # 라벨 클래스
                        "올해 입사자 평균 연봉",
                        company_name
                    )
                    if new_salary_data:
                        total_data["올해 입사자 평균 연봉"] = new_salary_data

            if total_data:
                return total_data
            else:
                return []

    except Exception as e:
        logger.error(f"[원티드] 연봉 정보 수집 중 오류 발생: {e}")
        return []
