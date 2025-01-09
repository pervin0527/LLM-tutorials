import os
import openai

from dotenv import load_dotenv
from recruit_detail_prompt import make_prompt

load_dotenv('../../../keys.env')
openai_api_key = os.getenv('GRAVY_LAB_OPENAI')

client = openai.OpenAI(api_key=openai_api_key)

def run_openai_api(prompt, input, temperature):
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


if __name__ == "__main__":
    sample = "D - 25 씨앤에스 ( 주 ) 관심기업 채용중 2 임사지원 35 공간디자이너 ( 전시디자인 인테리어 디자인 구함 ( 오후5시퇴근 ) T미주과 되느 모집부문 상세내용 및 공통 자격요건 프학력 대졸 이상 ( 2, 3년 ) 디자이너 설계실 0명 주요업무 = 고객요구 분석 = 프로젝트 관리 및조율  디자인 컨셉 개발 시각적 제작 자료 = 팀 협업 및소통 지원자격 = = 경력 경력 3년 이상 우대사항 트컬러리스트기사, 실내건축기사, 건축기사 = = 30툴능숙자, 해당직무 근무경험 CAD / CAM 능숙자 근무조건 특근무형태 정규직 ( 수습기간 ) - 2개월 특근무일시 09 : 00 ~ 17 : 00 틉근무지역 ( 05836 ) 서울 송파구 법원로9길 26 에이치비지니스파크 서울 8호선 문정 에서 800m 이내 전형절차 Setp Setp2 Setp3 최종합격 서류전형 1차면접 접수기간및 방법 특접수기간 2024년 12월 5일 ( 목 ) 10시 2025년 2월 3일 ( 월 ) 24시 = 즙접수방법 사람인 입사지원 이력서양식 사람인 온라인 이력서 유의사항 D - 25 씨앤에스 ( 주 ) 관심기업 채용중 2 임사지원 35 공간디자이너 ( 전시디자인 인테리어 디자인 구함 ( 오후5시퇴근 ) 복리후생 교육 / 생활 급여제도 점심식사 음료제공 ( 차, 인센티브제, 퇴직금, 4대 보험 제공, 커피 ) 조직문화 리프레시 자유복장 연차 내용 닫기 근무지위치 ( 05836 ) 서울 송파구 법원로9길 에이치비지니스파크 26 서울 8호선 문정역에서 800m 이내 지도보기 접수기간및방법 지원방법 사람인 입사지원 남은 기간 25일 07 : 18 : 08 접수양식 사람인 이력서 양식 인터뷰 미리보기 @ 사전인터뷰 입사지원 후 사전인터뷰 작성이 필요합니다. 질문 2024. 12. 05 10 : 00 시작일 마감일 2025. 02. 03 23 : 59 일사지원 마감일은 기업의 사정 조기마감 등으로 변경될 있습니다. 수 지원자 통계 지원지수 경력별 연봉별 현황 현황 23명 궁금하다면? 이 공고에 지원한 회원들이 로그인 하시고 지원자들의 다지일서 승 학력 등의 현황을 경력, 성별, 확인하세요"
    prompt = make_prompt()

    result = run_openai_api(prompt, sample, temperature=0)
    print(result)