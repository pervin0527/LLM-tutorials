import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

from utils.config_utils import read_config
from utils.browser_options import load_options

def main(cfg):
    options = load_options()
    os.makedirs(cfg['screenshot_path'], exist_ok=True)
    
    browser = webdriver.Chrome(options=options)
    browser.get(cfg['saramin_url'])
    browser.save_screenshot(f"{cfg['screenshot_path']}/sc_00.png")
    
    sp_main_wrapper = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "sp_main_wrapper")))
    # sp_area = WebDriverWait(sp_main_wrapper, 10).until(EC.presence_of_element_located((By.ID, "sp_area_lastDepth_101000")))
    # sp_area = sp_area.find_elements(By.TAG_NAME, "li")[0]

    wrap_depth_category = browser.find_element(By.CLASS_NAME, "wrap_depth_category ")
    overview = wrap_depth_category.find_element(By.CLASS_NAME, "overview")
    region_ids = ["depth1_btn_101000", "depth1_btn_102000", "depth1_btn_108000", "depth1_btn_106000", "depth1_btn_104000", "depth1_btn_103000", "depth1_btn_105000", "depth1_btn_107000", "depth1_btn_118000",
                  "depth1_btn_109000", "depth1_btn_110000", "depth1_btn_111000", "depth1_btn_112000", "depth1_btn_113000", "depth1_btn_115000", "depth1_btn_114000", "depth1_btn_116000", "depth1_btn_117000"]
    for id in region_ids:
        item = overview.find_element(By.ID, id)
        name = item.find_element(By.CLASS_NAME, "txt").text
        count = item.find_element(By.CLASS_NAME, "count").text

        print(name, count)


    time.sleep(30)


if __name__ == "__main__":
    cfg = read_config("./configs/config.yaml")
    main(cfg)