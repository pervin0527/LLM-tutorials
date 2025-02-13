import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

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
    