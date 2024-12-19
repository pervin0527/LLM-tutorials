import streamlit as st
from pathlib import Path

def get_font_path():
    """
    프로젝트 내의 fonts 디렉토리에서 나눔고딕 폰트를 찾는 함수
    """
    # 현재 실행 파일의 절대 경로를 기준으로 fonts 디렉토리를 찾습니다
    current_file = Path(__file__).resolve()
    project_root = current_file.parent
    font_path = project_root / 'fonts' / 'NanumGothic.ttf'
    
    # fonts 디렉토리가 없다면 생성
    if not font_path.parent.exists():
        font_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 폰트 파일이 없다면 다운로드 (선택사항)
    if not font_path.exists():
        st.warning("폰트 파일이 없습니다. fonts 디렉토리에 NanumGothic.ttf를 넣어주세요.")
        # 기본 폰트 사용
        return None
    
    return str(font_path)