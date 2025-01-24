import fitz
import pdfplumber

import time
import concurrent.futures

def timeit(func):
    """함수 실행 시간을 측정하는 데코레이터"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 실행 시간: {end_time - start_time:.4f}초")
        return result
    return wrapper

@timeit
def extract_text_with_pdfplumber(pdf_file):
    # PDF 파일 열기
    all_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        # 각 페이지의 텍스트 추출
        for page in pdf.pages:
            all_text += page.extract_text() + "\n"
    return all_text


@timeit
def extract_text_with_pymupdf(pdf_file):
    # PDF 파일 열기
    doc = fitz.open(pdf_file)
    all_text = ""

    # 각 페이지의 텍스트 추출
    for page_num in range(len(doc)):
        page = doc[page_num]
        all_text += page.get_text() + "\n"

    doc.close()
    return all_text


@timeit
def pdf_text_alignment(client, extracted_text):
    # 공통 시스템 프롬프트
    init_system_prompt = """
        당신은 자기소개서, 이력서 첨삭 전문가 입니다.
        사용자가 입력한 데이터는 PDF 파일에서 추출한 텍스트이기 때문에 적절한 문서형식을 갖추지 못한 텍스트 데이터입니다. 
    """

    # 각 항목별 프롬프트
    prompts = [
        "프로필 : 제목, 신상정보, 학력/경력사항, 희망연봉, 희망근무지/근무형태",
        "학력 : 재학기간, 구분(졸업여부), 학교명, 전공, 학점",
        "경력 : 회사명, 근무기간, 부서/직급/직책, 지역, 연봉, 담당업무",
        "자격증/어학/수상내역 : 구분(자격증/어학시험/면허증), 자격/어학/수상명, 발행처/기관/언어, 취득일/수상일, 합격/점수",
        "보유기술 : 보유기술명/수준/상세내용",
        "취업우대사항 : 우대사항명/내용",
        "경력기술서 : 기업명, 재직기간, 부서/직급/직책, 제목, 상세내용",
        "자기소개서 : 제목, 상세내용"
    ]

    # 각 항목별 결과를 저장할 리스트
    results = []

    # 각 항목별로 대화 수행
    for prompt in prompts:
        # 시스템 프롬프트와 사용자 프롬프트 구성
        system_prompt = init_system_prompt + f"\n주어진 항목에 해당하는 정보를 입력된 텍스트로부터 추출하고 Markdown 문법을 사용해 문서형식으로 정리하고 문자열로 출력해주세요.\n{prompt}"
        user_prompt = f"{extracted_text}"

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        # 각 항목별 결과 저장
        results.append(response.choices[0].message.content)

    # 최종 결과를 하나의 텍스트로 종합
    final_text = "\n\n".join(results)

    return final_text


@timeit
def pdf_text_alignment_v2(client, extracted_text):
    # 공통 시스템 프롬프트
    init_system_prompt = """
        당신은 자기소개서, 이력서 첨삭 전문가 입니다. 다음 지시사항과 주의사항에 따라 작업을 수행하세요.

        [지시사항]
        - 사용자가 입력한 데이터는 PDF 파일에서 추출한 텍스트이기 때문에 적절한 문서형식을 갖추지 못한 텍스트 데이터입니다. 
        - 사용자가 입력 텍스트로부터 추출하길 희망하는 데이터를 추출하고, markdown 문법으로 재구성합니다. 그 후 값을 반환할 때는 문자열(str)로 반환해주세요.

        [주의사항]
        - ```markdown``` 과 같은 형태는 포함하면 안됩니다.
        - 추출하고 재구성한 데이터 외에 다른 말은 하지마세요. 예를 들어 '학력 정보를 다음과 같이 정리하였습니다.' 와 같은 말은 하지마세요.

    """

    # 각 항목별 프롬프트
    prompts = [
        "지원자 정보 - 이력서(또는 자기소개서)제목, 신상정보, 학력/경력사항, 희망연봉, 희망근무지/근무형태",
        "학력 - 재학기간, 구분(졸업여부), 학교명, 전공, 학점",
        "경력 -  회사명, 근무기간, 부서/직급/직책, 지역, 연봉, 담당업무",
        "자격증/어학/수상내역 - 구분(자격증/어학시험/면허증), 자격/어학/수상명, 발행처/기관/언어, 취득일/수상일, 합격/점수",
        "보유기술 -  보유기술명/수준/상세내용",
        "취업우대사항 - 우대사항명/내용",
        "경력기술서 - 기업명, 재직기간, 부서/직급/직책, 제목, 상세내용",
        "자기소개서 - 제목, 상세내용"
    ]

    def process_prompt(prompt):
        system_prompt = init_system_prompt + f"\n주어진 항목에 해당하는 정보를 입력된 텍스트로부터 추출하고 Markdown 문법을 사용해 문서형식으로 정리하고 문자열로 출력해주세요.\n{prompt}"
        user_prompt = f"{extracted_text}"

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content

    # 병렬로 각 항목 처리
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(process_prompt, prompts))

    # 최종 결과를 하나의 텍스트로 종합
    final_text = "\n\n".join(results)

    return final_text