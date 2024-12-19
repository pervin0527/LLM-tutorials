import json
import streamlit as st

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def save_to_json_file(data, file_name):
    try:
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Data successfully saved to {file_name}")
        
    except Exception as e:
        print(f"Error saving data to {file_name}: {e}")


def save_feedback(file_path, feedback_data):
    try:
        with open(file_path, "w") as f:
            json.dump(feedback_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error saving feedback: {e}")


def load_feedback(file_path):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data  # JSON 배열 반환
            else:
                return []  # 올바른 구조가 아니면 빈 배열 반환
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # 파일이 없거나 구조가 잘못된 경우 빈 배열 반환