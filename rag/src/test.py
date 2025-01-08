import os
import cv2
import time
import pytesseract
from selenium import webdriver
from selenium.webdriver.common.by import By

def scroll_and_capture(browser, element, output_dir="screenshots"):
    """스크롤하면서 스크린샷 촬영"""
    # 출력 디렉토리 생성
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

    while scroll_y < total_height:
        # 현재 스크롤 위치 설정
        browser.execute_script(f"window.scrollTo(0, {location['y'] + scroll_y});")
        time.sleep(1)  # 스크롤 후 렌더링 대기

        # 스크린샷 저장
        screenshot_path = os.path.join(output_dir, f"screenshot_{screenshot_index}.png")
        browser.save_screenshot(screenshot_path)
        print(f"스크린샷 저장: {screenshot_path}")

        scroll_y += viewport_height
        screenshot_index += 1

def extract_text_from_images(image_dir):
    """이미지 디렉토리 내 모든 이미지에서 텍스트 추출"""
    extracted_texts = {}

    for file_name in sorted(os.listdir(image_dir)):
        if file_name.endswith(".png"):
            image_path = os.path.join(image_dir, file_name)
            print(f"텍스트 추출 중: {image_path}")

            # OpenCV로 이미지 열기
            image = cv2.imread(image_path)

            # Tesseract를 이용해 텍스트 추출
            text = pytesseract.image_to_string(image, lang="kor+eng")  # 한국어와 영어 동시 지원
            extracted_texts[file_name] = text

    return extracted_texts

if __name__ == "__main__":
    browser = webdriver.Chrome()
    browser.get("https://www.saramin.co.kr/zf_user/jobs/relay/view?view_type=list&rec_idx=49725038")
    time.sleep(2)

    wrap_jv_cont = browser.find_element(By.CLASS_NAME, "wrap_jv_cont")
    element = wrap_jv_cont.find_element(By.CLASS_NAME, "jv_detail")

    os.makedirs("./imgs", exist_ok=True)
    scroll_and_capture(browser, element, output_dir="./imgs")

    # 브라우저 종료
    browser.quit()

    # 스크린샷에서 텍스트 추출
    extracted_texts = extract_text_from_images("./imgs")

    # 추출된 텍스트 출력
    for file_name, text in extracted_texts.items():
        print(f"파일: {file_name}\n텍스트:\n{text}\n")
