from selenium.webdriver.chrome.options import Options

def load_options():
    options = Options()
    # options.add_argument("--headless")
    options.add_argument('--incognito')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument('--disable-infobars')
    options.add_argument("--disable-extensions")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument("--disable-popup-blocking")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-insecure-localhost')
    options.add_argument("--blink-settings=imagesEnabled=false")  # 이미지 비활성화
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    return options