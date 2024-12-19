import re
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib import font_manager

from utils.font import get_font_path
from utils.culture_fit_visualize import vision_radar, workstyle_radar
from utils.file import load_json, save_to_json_file, save_feedback, load_feedback

FEEDBACK_FILE = "../data/feedback_results.json"

# 페이지 렌더링 함수
def render_page(idx, dataset, vision_comments, workstyle_comments, summary_comments, feedback_data):
    st.title(f"Data Review: Index {idx + 1}")

    # 데이터 준비
    data = dataset[idx]
    vc = vision_comments[idx]
    wc = workstyle_comments[idx]
    sc = summary_comments[idx]

    page_left, page_right = st.columns(2)

    # 왼쪽 페이지 구성
    with page_left:
        st.subheader("검사 결과")
        col1, col2 = st.columns([0.8, 0.8])

        with col1:
            st.subheader("Vision")
            fig_vision = vision_radar(data)
            st.plotly_chart(fig_vision, use_container_width=True)

        with col2:
            st.subheader("Workstyle")
            fig_workstyle = workstyle_radar(data)
            st.plotly_chart(fig_workstyle, use_container_width=True)

        st.subheader("컬처핏 적합수준")
        st.markdown(f"```{data['summaryResult']['fitGrade']}```")

        st.subheader("검사 항목별 결과")
        recruitment_questions = data["summaryResult"]["recruitentQuestions"]
        sorted_questions = sorted(
            recruitment_questions.items(),
            key=lambda item: int(re.search(r"^\d+", item[0]).group())  # 질문 번호로 정렬
        )
        sorted_questions_text = "\n".join(f"{k}: {v}" for k, v in sorted_questions)
        st.markdown(f"```\n{sorted_questions_text}\n```")

        st.subheader("갈등 유발 요인")
        fued_factors = data["summaryResult"]["fued"]
        st.markdown(f"```{', '.join(fued_factors) if fued_factors else 'None'}```")

        st.subheader("이직 스트레스 요인")
        turnover_factors = data["summaryResult"]["turnOverFactors"]
        turnover_text = "\n".join(turnover_factors) if turnover_factors else "None"
        st.markdown(f"```\n{turnover_text}\n```")

    # 오른쪽 페이지 구성
    with page_right:
        st.subheader("Comment 비교")

        # 텍스트 데이터 준비
        vc_origin = vc["original"][0]["response"].replace('.', '\n')
        wc_origin = wc["original"][0]["response"].replace('.', '\n')
        sc_origin = sc["original"][0]["response"].replace('.', '\n')
        origin_total = f"[Vision]\n{vc_origin}\n[Workstyle]\n{wc_origin}\n[Summary]\n{sc_origin}"

        vc_advance = vc["advanced"][0]["response"].replace('.', '\n')
        wc_advance = wc["advanced"][0]["response"].replace('.', '\n')
        sc_advance = sc["advanced"][0]["response"].replace('.', '\n')
        advance_total = f"[Vision]\n{vc_advance}\n[Workstyle]\n{wc_advance}\n[Summary]\n{sc_advance}"

        # 텍스트 비교 영역
        st.text_area("Original Text", origin_total, height=400, disabled=True)
        st.text_area("Advanced Text", advance_total, height=400, disabled=True)

        # 선택 옵션
        selected_option = st.radio(
            "두 텍스트 중 하나를 선택하세요:",
            options=["Original", "Advanced"],
            index=0,
        )

        # 피드백 입력란 (session_state를 사용해 초기화 가능)
        feedback_key = f"feedback_{idx}"
        if feedback_key not in st.session_state:
            st.session_state[feedback_key] = ""  # 초기값 설정

        feedback = st.text_area("피드백을 입력하세요:", st.session_state[feedback_key], height=100)

        # 선택 완료 버튼
        if st.button("선택 완료"):
            if selected_option and feedback.strip():  # 선택 및 피드백 확인
                feedback_data.append({
                    "index": idx,
                    "selected_option": selected_option,
                    "feedback": feedback,
                })
                save_feedback(FEEDBACK_FILE, feedback_data)
                st.success("피드백이 저장되었습니다!")
                st.session_state[feedback_key] = ""  # 피드백 초기화
                st.session_state.idx += 1  # 다음 인덱스로 이동
            else:
                st.error("선택과 피드백을 모두 입력해야 합니다!")

def main():
    # 데이터 로드
    dataset = load_json("../data/dev-survey-result.json")
    vision_comments = load_json("../data/vision_output.json")
    workstyle_comments = load_json("../data/workstyle_output.json")
    summary_comments = load_json("../data/summary_output.json")

    assert len(dataset) == len(vision_comments) == len(workstyle_comments) == len(summary_comments)

    # Streamlit 설정
    st.set_page_config(page_title="EDA Dashboard", layout="wide")

    # 초기 상태 설정
    if "idx" not in st.session_state:
        st.session_state.idx = 0  # 현재 데이터 인덱스

    # 기존 피드백 로드
    feedback_data = load_feedback(FEEDBACK_FILE)

    # 현재 인덱스
    idx = st.session_state.idx

    # 데이터가 끝나면 메시지 출력
    if idx >= len(dataset):
        st.title("모든 데이터가 처리되었습니다.")
        st.stop()

    # 페이지 렌더링
    render_page(idx, dataset, vision_comments, workstyle_comments, summary_comments, feedback_data)

if __name__ == "__main__":
    main()