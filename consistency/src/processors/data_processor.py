from utils.mapping_dict import key_translation

def translate_and_convert_to_string(summary_result: dict) -> str:
    # 매핑 작업을 수행하는 함수
    def translate_key(key: str) -> str:
        return key_translation.get(key, key)
    
    # 각 요소들을 문자열로 변환하고 결과를 저장할 리스트
    ## result 리스트에 {key : value}형태로 저장함
    result = []
    
    # additionalInformation 처리
    result.append("\n채용 권장 수준, 입사 후 적응 기간, 조기 퇴사 가능성 : ")
    additional_info = summary_result.get("additionalInformation", {})
    for key, value in additional_info.items():
        result.append(f"{key}: {value}")

    # recruitentQuestions 처리
    result.append("\n검사 항목별 결과 : ")
    recruitent_questions = summary_result.get("recruitentQuestions", {})
    for key, value in recruitent_questions.items():
        result.append(f"{key}: {value}")
    
    # turnOverFactors 처리 및 key 매핑
    result.append("\n이직 스트레스 요인 : ")
    turn_over_factors = summary_result.get("turnOverFactors", [])
    if not turn_over_factors:
        result.append("없음")
    else:
        translated_turn_over_factors = [translate_key(factor) for factor in turn_over_factors]
        result.append(f"{', '.join(translated_turn_over_factors)}")

    # fued 처리 (None이 아닐 때만 추가)
    fued = summary_result.get("fued")
    if fued:
        result.append(f"\n위험 성향 : {', '.join(fued)}")

    return "\n".join(result)


def get_top_and_remaining_keywords(keywords: dict, top_n: int = 3) -> tuple:
    # 점수를 기준으로 키워드를 내림차순 정렬
    sorted_keywords = sorted(keywords.items(), key=lambda item: item[1], reverse=True)
    
    # 상위 n개 키워드 추출
    top_keywords = sorted_keywords[:top_n]
    
    # 나머지 키워드 추출
    remaining_keywords = sorted_keywords[top_n:]
    
    return top_keywords, remaining_keywords


def convert_keywords_to_string(keywords: list) -> str:
    # 리스트형 튜플을 "키워드:점수, 키워드:점수" 형식의 문자열로 변환하는 함수
    return ", ".join([f"{keyword}:{score}" for keyword, score in keywords])


def process_vision_result(vision_result: dict, summary_result: dict) -> dict:
    # company와 compute 각각에 대해 상위 3개 키워드와 나머지 키워드를 분리
    company_top, company_remaining = get_top_and_remaining_keywords(vision_result['company']['keyWord'])
    compute_top, compute_remaining = get_top_and_remaining_keywords(vision_result['compute']['keyWord'])

    # 키워드를 문자열로 변환
    company_top_str = convert_keywords_to_string(company_top)
    company_remaining_str = convert_keywords_to_string(company_remaining)
    compute_top_str = convert_keywords_to_string(compute_top)
    compute_remaining_str = convert_keywords_to_string(compute_remaining)
    
    compute_vision_eval_score = summary_result.get('visionScore')
    compute_high_eval_rate = summary_result['calCulturefit'].get('highCultureScore')
    compute_middle_eval_rate = summary_result['calCulturefit'].get('middleCultureScore')
    scroe_ceiling = summary_result['calCulturefit'].get('visionPercent')
    
    # 동적 임계값 계산
    high_threshold = scroe_ceiling * compute_high_eval_rate / 100
    middle_threshold = scroe_ceiling * compute_middle_eval_rate / 100

    # 평가 결과 분류
    if compute_vision_eval_score >= high_threshold:
        compute_vision_total_evalation = "우수"
        
    elif middle_threshold <= compute_vision_eval_score < high_threshold:
        compute_vision_total_evalation = "보통"
        
    else:
        compute_vision_total_evalation = "검토 필요"

    return {
        "company_top_keywords": company_top_str,
        "company_remaining_keywords": company_remaining_str,
        "compute_top_keywords": compute_top_str,
        "compute_remaining_keywords": compute_remaining_str,
        "compute_vision_total_evalation": compute_vision_total_evalation,
    }


def extract_workstyle_info(workstyle_result: dict, summary_result: dict) -> dict:
    # 기업과 피검사자의 워크스타일 키워드와 점수를 가져옵니다.
    company_keywords = list(workstyle_result['company']['keyWord'].items())
    compute_keywords = list(workstyle_result['compute']['keyWord'].items())

    # 기업과 피검사자의 총합 점수를 가져옵니다.
    workstyle_company_total_score = workstyle_result['company']['totalScore']
    workstyle_compute_total_score = workstyle_result['compute']['totalScore']

    # 기업과 피검사자의 동일 키워드의 일치율을 가져옵니다.
    workstyle_match_percentage = workstyle_result['rate']

    # 피검사자의 총합 점수 비교 비율을 계산합니다.
    comparison_ratio = (workstyle_compute_total_score / workstyle_company_total_score) * 100

    # 키워드를 문자열로 변환
    company_keywords_str = convert_keywords_to_string(company_keywords)
    compute_keywords_str = convert_keywords_to_string(compute_keywords)

    compute_workstyle_eval_score = summary_result['workStyleScore']

    compute_high_eval_rate = summary_result['calCulturefit'].get('highCultureScore')
    compute_middle_eval_rate = summary_result['calCulturefit'].get('middleCultureScore')
    scroe_ceiling = summary_result['calCulturefit'].get('workStylePercent')

    # 동적 임계값 계산
    high_threshold = scroe_ceiling * compute_high_eval_rate / 100
    middle_threshold = scroe_ceiling * compute_middle_eval_rate / 100

    # 평가 결과 분류
    if compute_workstyle_eval_score >= high_threshold:
        compute_workstyle_total_evalation = "우수"
        
    elif middle_threshold <= compute_workstyle_eval_score < high_threshold:
        compute_workstyle_total_evalation = "보통"
        
    else:
        compute_workstyle_total_evalation = "검토 필요"

    # 결과를 포맷팅하여 반환합니다.
    result = {
        "company_keywords": company_keywords_str,
        "compute_keywords": compute_keywords_str,
        "workstyle_match_percentage": workstyle_match_percentage,
        "workstyle_company_total_score": workstyle_company_total_score,
        "workstyle_compute_total_score": workstyle_compute_total_score,
        "comparison_ratio": comparison_ratio,
        "compute_workstyle_total_evalation": compute_workstyle_total_evalation,
    }

    return result