import os
import re
import requests

from openai import OpenAI
from bs4 import BeautifulSoup

from dotenv import load_dotenv
load_dotenv('./keys.env')
openai_api_key = os.getenv('GRAVY_LAB_OPENAI')

prompt = """
주어진 웹 페이지 전체 내용에서 본문에 해당하는 핵심내용을 추출해주세요.
"""

def generate(client, prompt, input, temperature):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": input}
        ],
        temperature=temperature
    )
    response_content = completion.choices[0].message.content
    return response_content

def main():
    client = OpenAI(api_key=openai_api_key)
    url = "https://company.namyangi.com/recruit/overview.asp" ## "https://company.namyangi.com/enterprise/vision.asp"
    response = requests.get(url)

    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        all_text = soup.get_text()
        cleaned_text = re.sub(r'\s+', ' ', all_text).strip()
        
        result = generate(client, prompt, cleaned_text, 0)
        print(result)

    else:
        print(f"Failed to fetch the page. Status code: {response.status_code}")


if __name__ == "__main__":
    main()