import os
import uuid
import psycopg2
import requests
import json

from dotenv import load_dotenv
load_dotenv('./keys.env')
USER = os.getenv('USER')
HOST = os.getenv('HOST')
DB = os.getenv('DB')
PW = os.getenv('PW')
JWT = os.getenv("JWT")

# 데이터베이스 설정
db_config = {
    'host': HOST,
    'database': DB,
    'user': USER,
    'password': PW,
    'port': 5432
}
print(db_config)

# UUID 유효성 검사 함수
def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))  # UUID로 변환 시도
        return True
    except ValueError:
        return False

# 데이터베이스에서 ID 가져오기
def fetch_ids(query):
    try:
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute(query)  # SQL 쿼리 실행
        ids = cursor.fetchall()  # 결과 가져오기
        return [row[0] for row in ids if is_valid_uuid(row[0])]  # UUID만 반환
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []
    finally:
        if 'connection' in locals() and connection:
            cursor.close()
            connection.close()

# REST API 호출 및 결과 저장
def send_request_to_api(id_list, output_file):
    base_url = "https://dev-api.grabberhr.com/api/v2/public/tests/{testId}/ai-request"
    headers = {
        'accept': '*/*',
        'Authorization': f'Bearer {JWT}'
    }

    all_responses = []  # 응답 데이터를 저장할 리스트

    for id_value in id_list:
        print(id_value)
        url = base_url.format(testId=id_value)  # ID를 URL에 삽입
        try:
            response = requests.get(url, headers=headers)  # GET 요청
            if response.status_code == 200:
                try:
                    data = response.json()  # JSON 파싱
                    all_responses.append(data)  # 응답 데이터 저장
                    print(f"Success: ID {id_value} processed.")
                except ValueError:
                    print(f"Success: ID {id_value} processed, but response is not valid JSON.")
            else:
                print(f"Failed for ID {id_value}: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"Error sending request for ID {id_value}: {e}")

    # 모든 응답 데이터를 파일에 저장
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_responses, f, ensure_ascii=False, indent=4)
        print(f"All responses saved to {output_file}.")
    except Exception as e:
        print(f"Error saving responses to file: {e}")


def main():
    # 첫 번째 쿼리 실행
    query1 = """
    SELECT id
    FROM hr_culture_test
    WHERE auth_code IS NOT NULL;
    """
    # ids_with_auth_code = fetch_ids(query1)
    # print(f"Fetched valid UUIDs with auth_code: {len(ids_with_auth_code)}")
    # test = ids_with_auth_code[0]
    # send_request_to_api([test])
    # send_request_to_api(ids_with_auth_code)

    # 두 번째 쿼리 실행
    query2 = """
    SELECT id
    FROM hr_culture_test
    WHERE auth_code IS NOT NULL
      AND enabled = FALSE;
    """
    ids_with_auth_code_disabled = fetch_ids(query2)
    print(f"Fetched valid UUIDs with auth_code and disabled: {len(ids_with_auth_code_disabled)}")

    # API 호출 및 결과 저장
    send_request_to_api(ids_with_auth_code_disabled, "../data/dev-survey-result.json")


if __name__ == "__main__":
    main()
