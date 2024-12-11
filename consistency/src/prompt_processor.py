from typing import Union

summary_alpaca_prompt = """
### Instruction:
다음은 지원자와 기업 간 전반적 Culture-fit, RightPeopleFit, 기타 종합 지표(summaryResult)를 바탕으로 최종적으로 지원자를 평가하는 코멘트를 생성하는 과정이다.
분석 기준은 다음과 같다:
1) Vision 및 Workstyle 결과에서 도출한 장점과 개선점, 그리고 summaryResult 내 제공된 추가정보(조기퇴사 가능성, 적응기간, 유지/이탈 요소, fitGrade 등)를 종합 반영한다.
2) VisionScore, WorkStyleScore, CulturefitScore, RightPeopleFitScore, fitGrade 등을 활용해 전체 적합도 수준을 명확히 결론짓고, 해당 결론은 데이터가 동일할 경우 재분석에도 유사한 형태를 유지한다.
3) 장점을 중심으로 지원자가 기업에 긍정적으로 기여할 수 있는 부분을 강조하고, 개선 필요 영역(예: 특정 문화나 가치에서의 차이)은 조직 차원에서 어떻게 대응할지 시사점을 제시한다.
4) 표현은 일관되고 체계화되어, 다양한 재실행에도 동일한 평가 결과를 일관성 있게 제시할 수 있도록 한다.

### Input Example:
```json
{
   "processed_data": {
      "이직 스트레스 요인": "경영진 변화",
      "위험성향": ["오만형"],
      "적응기간": "3개월",
      "조기퇴사가능성": "낮음",
      "검사항목별결과": [
         "업무 이해도 높음",
         "팀워크 협업 가능성 보통",
         "리더십 잠재력 있음"
      ],
      "이직요인": "인정 부족",
      "장기재직요인": "명확한 보상체계"
   }
}

### Response:
종합 평가 결과를 근거로 지원자의 기업 적합성을 결론짓고 향후 관리 포인트를 제안하는 코멘트.
"""


vision_alpaca_prompt = """
### Instruction:
다음은 기업 비전 관련 키워드와 해당 지원자의 스코어(visionResult)를 입력으로 받았을 때, 지원자가 기업 비전(가치관)과 어느 정도 정렬되는지 체계적으로 분석하는 코멘트를 생성하는 과정이다.
분석 기준은 다음과 같다:
1) 제공된 키워드별 스코어를 기반으로, 기업이 강조하는 핵심 비전 키워드(예: 혁신, 사회공헌, 성장, 전문성 등)와 지원자의 해당 스코어를 비교하여 '높은 정렬', '평균 수준', '개선 필요' 등의 평가를 일관된 기준으로 분류한다.
2) 높은 점수를 받은 핵심 키워드는 장점으로, 평균 수준 키워드는 보통 수준, 낮은 점수 키워드는 개선 또는 주의가 필요하다는 형태로 구체적으로 언급한다.
3) 전체 비전 점수(visionScore)나 핵심 키워드의 정렬도를 종합해 전반적 비전 적합성을 결론 짓는다.
4) 여러 번 동일한 데이터를 분석해도 유사한 결론에 도달할 수 있도록, 표현과 구조를 체계적이고 일관성 있게 유지한다.

### Input Example:
{
  "기업비전키워드": [
    {"키워드": "혁신", "점수": 4.5},
    {"키워드": "지속가능성", "점수": 4.3},
    {"키워드": "사회공헌", "점수": 4.2}
  ],
  "피검사자비전키워드": [
    {"키워드": "혁신", "점수": 4.0},
    {"키워드": "지속가능성", "점수": 4.8},
    {"키워드": "사회공헌", "점수": 0.4}
  ]
}

### Response:
기업 비전과 지원자의 정렬도를 체계적으로 해석하고 요약한 코멘트.
"""

workstyle_alpaca_prompt = """
### Instruction:
다음은 기업이 추구하는 일하는 방식(Workstyle) 관련 키워드와 해당 지원자의 스코어(workstyleResult)를 입력으로 받았을 때, 지원자가 기업의 작업 스타일 기대치와 어느 정도 일치하는지 체계적으로 분석하는 코멘트를 생성하는 과정이다.
분석 기준은 다음과 같다:
1) 제공된 키워드별 스코어를 분석하여, 기업이 중점적으로 여기는 작업 스타일(예: 혁신형, 스피드형, 목표지향형 등)에서 지원자가 얼마나 높은 점수를 보이는지 판단한다.
2) 점수 범위를 기준으로 '높은 정렬'(상위점수), '평균 정렬'(중간점수), '부족한 정렬'(낮은점수)로 명확히 구분하고, 각 그룹에 속하는 키워드를 예시로 들어 설명한다.
3) 가능하다면 총합 점수(workStyleScore)나 비율(rate)을 활용해 전체적인 적합도를 결론지으며, 이 결론은 반복 수행에도 변하지 않는 일관된 방식으로 표현한다.
4) 강점과 개선 필요점을 균형 있게 서술한다.

### Input Example:
{
  "기업업무성향키워드": [
    {"키워드": "협업", "점수": 4.5},
    {"키워드": "도전정신", "점수": 4.0},
    {"키워드": "자율성", "점수": 3.8}
  ],
  "피검사자업무성향키워드": [
    {"키워드": "협업", "점수": 4.7},
    {"키워드": "도전정신", "점수": 3.9},
    {"키워드": "자율성", "점수": 3.8}
  ]
}

### Response:
기업의 일하는 방식과 지원자 간 정렬도를 분석하고, 강점 및 개선점, 종합 판단을 제시하는 코멘트.
"""


def generate_vision_prompt(processed_data: dict) -> list:
    company_top_keywords = processed_data['company_top_keywords']
    company_remaining_keywords = processed_data['company_remaining_keywords']
    compute_top_keywords = processed_data['compute_top_keywords']
    compute_remaining_keywords = processed_data['compute_remaining_keywords']
    
    # 종합 평가
    compute_vision_total_evalation = processed_data['compute_vision_total_evalation']
    
    # print('company_top_keywords', company_top_keywords)
    # print('company_remaining_keywords', company_remaining_keywords)
    # print('compute_top_keywords', compute_top_keywords)
    # print('compute_remaining_keywords', compute_remaining_keywords)

    default_prompt = vision_alpaca_prompt
    content = (
        f"기업의 상위 3개 비전 키워드와 점수: {company_top_keywords}\n"
        f"기업의 상위 3개 외 비전 키워드와 점수: {company_remaining_keywords}\n"
        f"피검사자의 비전 키워드와 점수: {compute_top_keywords}, {compute_remaining_keywords}\n"
        # f"기업의 비전 키워드와 점수: {company_top_keywords}, {company_remaining_keywords}\n"
        f"피검사자와 기업의 비전 적합성 평가 결과 : {compute_vision_total_evalation}\n"
    )

    messages = [
        {
            "role": "system",
            "content": f"※필수지침사항:\n{default_prompt}"
        },
        {
            "role": "user",
            "content": content
        },
    ]

    return messages


def generate_workstyle_prompt(processed_data: dict) -> list:
    company_keywords = processed_data['company_keywords']
    compute_keywords = processed_data['compute_keywords']
    workstyle_match_percentage = processed_data['workstyle_match_percentage']
    # workstyle_company_total_score = processed_data['workstyle_company_total_score']
    # workstyle_compute_total_score = processed_data['workstyle_compute_total_score']
    # comparison_ratio = processed_data['comparison_ratio']
    
    # 종합 평가
    compute_workstyle_total_evalation = processed_data['compute_workstyle_total_evalation']
    default_prompt = workstyle_alpaca_prompt

    content = (
        f"기업의 업무 성향 키워드 및 점수: {company_keywords}\n"
        f"피검사자의 업무 성향 키워드와 점수: {compute_keywords}\n"
        f"피검사자와 기업의 업무 성향 적합성 평가 결과 : {compute_workstyle_total_evalation}\n"
    )

    messages = [
        {
            "role": "system",
            "content": f"※필수지침사항:\n{default_prompt}"
        },
        {
            "role": "user",
            "content": content
        },
    ]
    
    return messages


def generate_summary_prompt(processed_data: dict) -> list:
    default_prompt = summary_alpaca_prompt
    content = processed_data

    messages = [
        {
            "role": "system",
            "content": f"※필수지침사항:\n{default_prompt}"
        },
        {
            "role": "user",
            "content": content
        },
    ]

    return messages