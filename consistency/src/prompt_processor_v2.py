from typing import Union
from src.prompts_v2 import summary_default_prompt, vision_default_prompt, workstyle_default_prompt

def generate_vision_prompt(processed_data: dict) -> list:
    company_top_keywords = processed_data['company_top_keywords']
    company_remaining_keywords = processed_data['company_remaining_keywords']
    compute_top_keywords = processed_data['compute_top_keywords']
    compute_remaining_keywords = processed_data['compute_remaining_keywords']
    compute_vision_total_evalation = processed_data['compute_vision_total_evalation']

    content = (
        f"기업 상위 3개 비전 키워드: {company_top_keywords}\n"
        f"기업 기타 비전 키워드: {company_remaining_keywords}\n"
        f"피검사자 비전 키워드: {compute_top_keywords}, {compute_remaining_keywords}\n"
        f"비전 적합성 평가 결과: {compute_vision_total_evalation}\n"
    )

    messages = [
        {
            "role": "system",
            "content": vision_default_prompt
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
    compute_workstyle_total_evalation = processed_data['compute_workstyle_total_evalation']

    content = (
        f"기업 업무성향 키워드: {company_keywords}\n"
        f"피검사자 업무성향 키워드: {compute_keywords}\n"
        f"업무 성향 적합성 평가 결과: {compute_workstyle_total_evalation}\n"
    )

    messages = [
        {
            "role": "system",
            "content": workstyle_default_prompt
        },
        {
            "role": "user",
            "content": content
        },
    ]

    return messages


def generate_summary_prompt(processed_data: dict) -> list:
    # Chain of Thought 지침은 summary_default_prompt에 이미 반영되어 있음.
    # 내부적으로 사고를 거친 뒤 최종 답변만 출력하도록 합니다.
    messages = [
        {
            "role": "system",
            "content": summary_default_prompt
        },
        {
            "role": "user",
            "content": str(processed_data)
        },
    ]
    return messages
