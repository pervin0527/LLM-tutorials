from typing import Union
from src.prompts_v1 import summary_default_prompt, workstyle_default_prompt, vision_default_prompt


def generate_vision_prompt(processed_data: dict) -> list:
    company_top_keywords = processed_data['company_top_keywords']
    company_remaining_keywords = processed_data['company_remaining_keywords']
    compute_top_keywords = processed_data['compute_top_keywords']
    compute_remaining_keywords = processed_data['compute_remaining_keywords']
    
    # 종합 평가
    compute_vision_total_evalation = processed_data['compute_vision_total_evalation']
    
    print('company_top_keywords', company_top_keywords)
    print('company_remaining_keywords', company_remaining_keywords)
    print('compute_top_keywords', compute_top_keywords)
    print('compute_remaining_keywords', compute_remaining_keywords)

    default_prompt = vision_default_prompt
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
    print(messages)
    print()
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
    default_prompt = workstyle_default_prompt

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
    default_prompt = summary_default_prompt
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
