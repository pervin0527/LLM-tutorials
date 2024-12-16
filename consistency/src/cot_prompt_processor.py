from tqdm import tqdm

vision_prompt = """
[목표]

기업이 중요하게 생각하는 핵심 비전( company_top_visions )과 부가적 가치( company_remain_visions )를 기준으로, 피검사자( compute_top_visions, compute_remain_visions )의 비전 적합도를 평가하는 문장을 작성한다.
최종 출력문은 내부적인 계산 과정이나 점수를 드러내지 않고, 기업과 피검사자 간 비전 적합성을 간결하고 겸손하게 표현한다.
문장 마지막에 compute_vision_total_evaluation 값을 반영하여 전반적인 비전 fit을 "높은 편", "보통", "낮은 편" 중 하나로 마무리한다.

[입력 예시]
company_top_visions: 혁신:5.0, 도전:5.0, 창조:5.0
compnay_remain_visions : 전문성:3.7, 즐거움:3.5, 사회공헌:3.2
compute_top_visions: 창조:5.0, 도전:3.85, 혁신:3.64
compute_remain_visions : 인재:3.25, 최고지향:3.13, 성장:3.08, 성과:3.08, 상생:2.5, 열정:2.5, 소통:2.31, 즐거움:2.22, 고객:2.0, 신속성:1.92, 사회공헌:1.67, 전문성:1.36, 문제해결:0.0
compute_vision_total_evaluation : 검토 필요

[작성 지침]
모델은 내부적으로 다음 단계(Chain of Thought)를 거쳐 결론에 도달하나 최종 출력에는 노출하지 않는다.

compnay_top_visions와 compute_top_visions 비교:
   - 차이가 0.5 이하인 키워드는 기업과 높은 수준으로 정렬되었음을 긍정적으로 표현하며 특정 키워드에 대해 피검사자의 점수가 더 높은 경우, 기업에 추가적 가치를 제공할 가능성을 긍정적으로 표현한다.
   - 1.8 이상 차이난다면 해당 키워드에 대해 우려가 됨을 표현한다.(다만 부정적인 어체는 사용하지 않는다.)

company_remain_visions 상위 4개와 compute_remain_visions 상위 4개를 비교:
   - 차이가 0.5 이하인 경우 추가적으로 기업과 fit이 있음을 긍정적으로 표현한다.
   - 1.8 이상 차이 나는 키워드는 기업 비전과 차이가 있음을 간결하게 표현(우려, 간극 등을 짧게 언급)

최종 문장 작성 시 조건
   - 한글 300자 이내, 존댓말, 겸손한 어조
   - 최종 문장에 점수나 계산 과정, 단계별 분석 내용 포함 금지한다.
   - 키워드는 따옴표로 명시하되 점수 언급 금지한다.
   - 마지막 문장에 compute_vision_total_evaluation값("검토 필요")을 반영
      - "우수"일 경우: "전반적으로 피검사자와 기업간 비전 fit은 높은 편입니다."
      - "보통"일 경우: "전반적으로 피검사자와 기업간 비전 fit은 보통입니다."
      - "검토 필요"일 경우: "전반적으로 피검사자와 기업간 비전 fit은 낮은 편입니다."

최종 출력:
위 모든 과정을 종합한 하나의 문장만을 결과로 제시한다.
예: "피검사자는 (차이가 0.5이하인 키워드들) 부문에서 기업 비전과 높은 수준으로 정렬된 모습을 보이며, (차이가 0.5초과 1.8미만 키워드들)에서도 보통 수준의 정렬되는 것으로 보입니다. 하지만 (1.8이상인 키워드들)에서 차이를 드러내고 있습니다. 전반적으로 피검사자와 기업간 비전 fit은 낮은 편입니다."
"""

workstyle_prompt = """
[목표]

기업이 중요하게 생각하는 업무 스타일( company_keywords )과 피검사자( compute_keywords )의 업무 스타일 적합성을 비교한 후, 이를 한 문장으로 요약한 최종 평가문을 출력한다.
문장 내에는 점수나 내부 계산 과정, 단계별 결과를 포함하지 않는다.
Chain of Thought(추론 과정)는 모델 내부적으로만 수행하고, 최종 출력에는 오직 완성된 평가문만 제시한다.
[입력 예시]

company_keywords : 촉진자형:5.0, 분석형:5.0, 조력자형:5.0, 논리형:5.0, 협력형:5.0, 겸손형:5.0
compute_keywords : 촉진자형:2.14, 분석형:2.6, 조력자형:1.88, 논리형:2.22, 협력형:3.08, 겸손형:2.14
workstyle_company_total_score : 30.0
workstyle_compute_total_score : 14.06
comparison_ratio: 46.86666666666667
compute_workstyle_total_evaluation : 검토필요

[작성 지침]
모델은 내부적으로 다음 과정을 거쳐 결론에 이를 것(Chain of Thought), 하지만 최종 출력에서는 이 과정을 표시하지 않는다.

company_keywords와 compute_keywords 간 점수 차이를 계산한다.
점수 차이를 기준으로 키워드들을 세 그룹(0.5 이하, 0.5 초과 1.8 미만, 1.8 이상)으로 분류한다.
   - 0.5 이하인 경우 기업의 업무 방식과 적합함을 긍정적으로 서술.
   - 0.5 초과, 1.8미만인 경우 약한 긍정으로 서술.
   - 1.8 이상인 경우 기업의 업무 방식과 차이가 있어 우려됨을 서술하되, 부정적이지 않은 내용으로 서술.

각 그룹에 해당하는 키워드들에 대해 문장을 구성한다. 긍정문과 부정문이 모두 포함되는 경우 긍정문을 '보입니다.'처럼 문장을 완료한 후 '그러나'로 이어서 부정문을 연결할 것.
"피검사자는 (0.5 이하인 키워드들) 부문에서 기업의 비전과 보통 수준으로 정렬되어 있습니다. (0.5 초과, 1.8 미만인 항목들이 있다면 추가로 서술.) 그러나, (1.8 이상인 키워드들) 부문에서는 기업의 기대치와 차이를 보여 우려되며, 전반적으로 피검사자와 기업 간 업무 성향 fit은 낮은 수준으로 평가됩니다."
compute_workstyle_total_evaluation 값("우수", "보통", "검토필요")에 따라 마지막 문장을 결정한다.

최종 결과문 조건

- 한글 300자 이내, 존댓말, 겸손한 어투 사용.
- '어느정도'처럼 중의적인 표현이 아니라 '낮다', '보통' 또는 '비슷한', '높음'과 같은 수준이 구분 가능한 단어들을 사용할 것.
- 긍정문과 부정문이 모두 포함되는 경우 긍정문을 '보입니다.'처럼 문장을 완료한 후 '그러나'로 이어서 부정문을 연결할 것.
- 키워드명은 그대로 활용하되 점수나 내부 계산과정, 단계별 결과 언급 금지
- 최종 출력은 한 문장의 평가문만 제시

문장 예:
"피검사자는 '혁신성', '친화성', '유니크성', '스피드형' 부문에서 기업의 비전과 높은 수준으로 정렬된 모습을 보이며, '성과', '도전', '관계성'에서는 평균 수준에 해당하는 비전을 보이고, '논리성', '신뢰형', '이문화성' 부문에서는 기업의 기대치와 차이를 보이는 것으로 판단되며, 전반적으로 피검사자와 기업간 업무 성향 fit은 평균적인 수준으로 평가됩니다."
최종 출력은 내부 판단 결과를 모두 종합한 하나의 문장만 반환한다.
"""

summary_prompt = """
목표: 채용 피검사자의 결과를 바탕으로, 피검사자가 해당 기업에 얼마나 적합한지 종합적으로 평가하고, 채용 여부를 결정하는 데 필요한 코멘트를 작성하는 것입니다.

작업 설명: 피검사자의 평가 데이터를 분석하고, 단계별로 정보를 종합하여 최종적으로 200자 이내의 코멘트를 작성합니다. 모든 문장은 한글로 작성하고, 존댓말과 겸손한 어체를 사용하며, 띄어쓰기를 포함하여 200자 이내로 제한해야 합니다.

주의 사항: 단계별로 결과를 도출하지만, 반환하는 값은 5단계에서 생성한 최종 코멘트만 반환해야합니다. 5단계를 제외한 다른 단계의 결과를 반환하지 않도록 주의하세요.

---

**1단계:**  
- "recruitentQuestions" 값에서 ["그렇다", "매우 그렇다"]에 해당하는 항목들을 기반으로 피검사자가 가진 긍정적인 점을 서술하세요.
- 만약 긍정적인 항목들이 없다면 아무것도 하지 않고 다음 단계로 넘어갑니다.
- 예제1: "피검사자는 팀 내 협력과 소통에서 긍정적인 평가를 받았습니다."
- 예제2: "피검사자는 기업의 비전과 가치관에 매우 부합하며, 일하는 방식도 기업이 추구하는 방향과 일치합니다. 타 팀 및 구성원과의 협업과 상급자와의 소통에서도 긍정적인 평가를 받았습니다."

**2단계:**  
- "fued" 값이 피검사자의 갈등 유발 요인을 나타냅니다.  
- "fued" 값이 명시되어 있을 경우
   - 갈등 유발 요인이 1개인 경우 :조직 내에서 발생할 수 있는 문제와 갈등을 강하게 경고하는 문장을 구체적으로 서술하세요.
   - 갈등 유발 요인이 2개 이상인 경우 : 갈등 유발 요인을 확인할 필요가 있음을 명시하세요.
- "fued" 값이 "없음"일 경우, 해당 단계는 생략하고 다음 단계로 넘어갑니다.  
- 예제1: "투쟁형 성향으로 인해 과도한 경쟁과 갈등이 우려되며, 팀 분위기에 부정적인 영향을 미칠 수 있습니다."
- 예제2: "피검사자는 과몰입형 성향이 있어 조직 내 융통성이 부족하고, 다른 팀원들과의 협력이 어려울 수 있습니다. 이는 조직 내 갈등을 유발하고, 장기적으로 업무 효율성을 저하시킬 수 있습니다. 타 팀 및 구성원과의 협업이 원활하지 않으며, 기업의 일하는 방식과 부합하지 않는 점이 우려됩니다."
- 예제3: "모사형, 오만형, 과몰입형 성향이 높아 조직 내 파벌 형성, 신뢰 저하, 융통성 부족 등의 문제가 발생할 수 있습니다. 갈등 유발 요인을 확인하는 것이 중요합니다."

**3단계:**  
- "turnOverFactors" 값이 "없음"이 아닐 경우, "OO에 대한 스트레스 요인이 있으므로,"로 시작하여 기업이 대응할 수 있는 방법을 제시하세요.  
- 확정적인 어체를 피하고, "필요할 수 있습니다"와 같은 제시형 어체를 사용하세요.  
- "turnOverFactors" 값이 "없음"일 경우, 해당 단계는 생략하고 다음 단계로 넘어갑니다.  
- 예: "공정인사에 대한 스트레스 요인이 있으므로, 인사정책에 대한 명확한 안내가 필요할 수 있습니다."

**4단계:**  
- "additionalInformation" 값 중 "입사 후 적응 기간"과 "조기 퇴사 가능성"을 활용해 간략히 서술하세요.  
- 예: "입사 후 적응 기간은 보통이며, 조기 퇴사 가능성은 낮습니다."

**5단계:**  
- 1, 2, 3, 4단계에서 도출한 결과를 종합하여, 200자 이내로 최종 코멘트를 작성하세요.  
- 존댓말과 겸손한 어체를 사용하며, "채용을 권장합니다" 또는 "채용을 권장하지 않습니다"와 같은 끝맺음 문장은 사용하지 않습니다.  
- 예제1: "피검사자는 기업의 비전과 가치관에 잘 부합하며, 타 팀 및 구성원과의 협업과 소통에서도 긍정적인 평가를 받았습니다. 그러나 오만형 성향이 감지되어 팀원 간 신뢰를 저해하고 적대적인 분위기를 형성할 수 있습니다. 이는 조직 내 갈등을 유발할 수 있으므로 주의가 필요합니다. 공정인사에 대한 스트레스 요인이 있으므로, 인사 정책에 대한 명확한 안내가 필요할 수 있습니다. 입사 후 적응 기간은 보통이며, 조기 퇴사 가능성은 낮습니다."
- 예제2: "피검사자는 과몰입형 성향이 있어 조직 내 융통성이 부족하고, 다른 팀원들과의 협력이 어려울 수 있습니다. 이는 조직 내 갈등을 유발하고, 장기적으로 업무 효율성을 저하시킬 수 있습니다. 타 팀 및 구성원과의 협업이 원활하지 않으며, 기업의 일하는 방식과 부합하지 않는 점이 우려됩니다. 입사 후 적응 기간은 보통이나, 조기 퇴사 가능성이 높아 장기 재직에 대한 신중한 검토가 필요합니다. 갈등 유발 요인을 확인하시기 바랍니다."
- 예제3: "피검사자는 기업의 비전과 가치관에 매우 부합하며, 타 팀 및 구성원과의 원만한 협업과 상급자와의 원활한 소통이 기대됩니다. 그러나 모사형, 오만형, 과몰입형 성향이 높아 조직 내 파벌 형성, 신뢰 저하, 융통성 부족 등의 문제가 발생할 수 있습니다. 갈등 유발 요인을 확인하는 것이 중요합니다. 입사 후 적응 기간은 보통이며, 조기 퇴사 가능성은 낮습니다."
"""

def prompt_input_processing(hr_data_dict, vision_data, workstyle_data):
    vision_input = f"""
    company_top_visions: {vision_data['company_top_keywords']}
    compnay_remain_visions : {vision_data['company_remaining_keywords']}
    compute_top_visions: {vision_data['compute_top_keywords']}
    compute_remain_visions : {vision_data['compute_remaining_keywords']}
    compute_vision_total_evaluation : {vision_data['compute_vision_total_evalation']}
    """

    workstyle_input = f"""
    company_keywords : {workstyle_data['company_keywords']}
    compute_keywords : {workstyle_data['compute_keywords']}
    workstyle_company_total_score : {workstyle_data['workstyle_company_total_score']}
    workstyle_compute_total_score : {workstyle_data['workstyle_compute_total_score']}
    workstyle_compute_total_score : {workstyle_data['workstyle_match_percentage']}
    comparison_ratio: {workstyle_data['comparison_ratio']}
    compute_workstyle_total_evaluation : {workstyle_data['compute_workstyle_total_evalation']}
    """

    summary_input = f"""
    additionalInformation : {hr_data_dict['summaryResult']['additionalInformation']}
    recruitentQuestions : {hr_data_dict['summaryResult']['recruitentQuestions']}
    turnOVerFactors : {hr_data_dict['summaryResult']['turnOverFactors']}
    fued :{hr_data_dict['summaryResult']['fued']}
    """

    return vision_input, workstyle_input, summary_input


def run_openai_api(client, n_iter, prompt, input, temperature):
    results = []
    # for i in range(n_iter):
    for i in tqdm(range(n_iter)):
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": input}
            ],
            temperature=temperature
        )
        response_content = completion.choices[0].message.content
        results.append({
            "iteration": i + 1,
            "response": response_content
        })
    return results