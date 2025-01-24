import os

def get_db_info():
    return {
        'host': os.getenv("DB_HOST"),
        'user': os.getenv("DB_USER"),
        'password': os.getenv("DB_PASSWORD"),
        'database': os.getenv("DB_NAME"),
        'port': int(os.getenv("DB_PORT", 3306))  # 기본 포트를 3306으로 설정
    } 