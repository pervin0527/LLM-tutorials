import time
import json

def region_scroll_down(element, browser, scroll_pause_time=1):
    current_top = int(browser.execute_script("return parseInt(arguments[0].style.top.replace('px', '')) || 0;", element))
    
    while True:
        browser.execute_script("arguments[0].style.top = arguments[0].offsetTop - 100 + 'px';", element)
        time.sleep(scroll_pause_time)
        
        new_top = int(browser.execute_script("return parseInt(arguments[0].style.top.replace('px', '')) || 0;", element))
        if new_top <= -120:
            break

        if new_top == current_top:
            break

        current_top = new_top


def page_scroll_down(browser, scroll_step=500, delay=1.0):
    last_height = browser.execute_script("return document.body.scrollHeight")
    current_position = 0

    while current_position < last_height:
        # 현재 위치에서 scroll_step 만큼 아래로 스크롤
        current_position += scroll_step
        browser.execute_script(f"window.scrollTo(0, {current_position});")
        
        # 지정된 시간만큼 대기
        time.sleep(delay)
        
        # 새 페이지 높이를 가져옴
        new_height = browser.execute_script("return document.body.scrollHeight")
        
        # 만약 페이지 끝에 도달했으면 종료
        if current_position >= new_height:
            break
        
        last_height = new_height


def save_to_json(data, filename="recruit_data.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"Data saved to {filename}")