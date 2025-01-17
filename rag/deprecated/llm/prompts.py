def recruit_txt_prompt():
    prompt = f"""
    ## 지시사항
    주어진 데이터는 특정 회사에서 게재한 채용 공고입니다. 아래 정의된 내용과 단계들을 순차적으로 수행하면서 마지막 결과값을 반환하세요.
    
    ### 1단계
    입력된 데이터는 OCR 모델의 출력 결과이기 때문에 잘못 인식된 텍스트가 존재할 수 있습니다.
    - 인사 및 채용 담당자의 이메일 주소가 포함된 경우 이와 관련된 텍스트는 절대 제거하면 안됩니다.
    - 한글이나 영어가 아닌 특수문자나 기호는 제거합니다.('!', '?' 와 같은 문법적 기호는 제외함.)
    - 한글 또는 영어임에도 적절하게 단어를 완성하고 있지 않은 경우에는 제거합니다.

    ### 2단계
    일반적으로 기업이 사용하는 채용공고 템플릿으로 내용을 깔끔하게 재구성해서 반환해주세요. 다음과 같은 조건들을 충족시켜야 합니다.
    - 기본적으로 마크다운 형식을 사용해주세요. 각 부문의 제목은 '##'으로 표기하고 부문별 항목은 '-'으로 표기합니다.
        [예시]
            ## 모집 부문 및 상세내용
            - 모집 부문 : OOO
            - 모집 인원 : OOO
            - 학력 : OOO

    - 경력 항목을 보면 "경력": "경력 3년 ↑"과 같이 화살표 기호를 사용 중인데 이를 "경력": "경력 3년 이상" 으로 수정하세요.
    - '모집인원'은 몇 명을 채용할 것인지 나타냅니다. 여기에 직급이나 직책을 작성하지 않도록 주의하세요. '0명'이라고 기재되어 있는 경우는 인원제한이 없음을 뜻합니다.

    ## 요구사항
    - 당신이 최종적으로 반환해야하는 값은 2단계의 결과값입니다.
    - 중간 단계나 사고 과정을 결과값에 포함시키거나 반환하지 않도록 주의하세요.
    """

    return prompt


def recruit_img_prompt():
    prompt = f"""
    ## 지시사항
    주어진 이미지로부터 텍스트를 추출해서 반환해주세요.
    """

    return prompt