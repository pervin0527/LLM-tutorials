FROM python:3.11-slim-bullseye@sha256:34fb194372f3390c5986dd0a94f21de5f1615d0e1684c977e083fab06b2018be

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=on \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# 작업 디렉토리 설정
WORKDIR /culture_backoffice_backend

# 전체 프로젝트 복사
COPY . /culture_backoffice_backend/

# 필요한 패키지만 설치
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install -U \
    'fastapi[standard]' \
    uvicorn

# 컨테이너 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
