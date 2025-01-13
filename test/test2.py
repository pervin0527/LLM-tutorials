import os
import re
import requests
from openai import OpenAI
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv('./keys.env')
openai_api_key = os.getenv('GRAVY_LAB_OPENAI')

# GPT 프롬프트
prompt = """
주어진 기업 홈페이지에서 다음 정보들을 알 수 있을 것 같은 텍스트 및 링크들을 선별하고 정리해주세요.
- 기업의 이념 및 비전(가치관)
- 기업의 작업 스타일(작업 방식)
- 기업의 인재 채용
"""

def generate(client, prompt, input_text, temperature=0.5):
    """GPT를 사용해 정보 추출"""
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": input_text}
        ],
        temperature=temperature
    )
    response_content = completion.choices[0].message.content
    return response_content

def extract_links_and_text(soup):
    """HTML에서 모든 링크와 텍스트 추출"""
    links = []
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        text = a_tag.get_text(strip=True)
        if link.startswith("http") or link.startswith("/"):
            links.append({"text": text, "url": link})
    return links

def main():
    client = OpenAI(api_key=openai_api_key)
    url = "https://company.namyangi.com/recruit/overview.asp"

    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        # 텍스트 및 링크 추출
        cleaned_text = re.sub(r'\s+', ' ', soup.get_text()).strip()
        links = extract_links_and_text(soup)

        # ChatGPT에 요청
        input_data = f"텍스트: {cleaned_text}\n\n링크: {links}"
        result = generate(client, prompt, input_data, temperature=0.7)

        # 결과 출력
        print("GPT가 선별한 링크와 정보:")
        print(result)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")

if __name__ == "__main__":
    main()
