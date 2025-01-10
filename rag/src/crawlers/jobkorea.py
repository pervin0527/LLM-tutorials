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

class JobkoreaCrawler:
    def __init__(self, cfg, client):
        self.cfg = cfg
        self.client = client

        options = load_options(self.cfg)
        self.browser = webdriver.Chrome(options=options)