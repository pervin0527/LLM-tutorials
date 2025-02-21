import re
import json


async def process_string_to_json(text: str) -> dict:
    try:
        # 첫 번째 '{' 와 마지막 '}' 찾기
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError("JSON 형식의 데이터를 찾을 수 없습니다.")
            
        # JSON 부분 추출 및 전처리
        json_str = text[start_idx:end_idx + 1]
        json_str = json_str.strip()
        
        # JSON 파싱 시도
        try:
            parsed_data = json.loads(json_str)
        except json.JSONDecodeError:
            # 공백, 줄바꿈 정리 후 재시도
            json_str = re.sub(r'\s+', ' ', json_str)
            parsed_data = json.loads(json_str)
            
        return parsed_data
        
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 파싱 실패: {str(e)}")
    except Exception as e:
        raise ValueError(f"데이터 처리 중 오류 발생: {str(e)}")