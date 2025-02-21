FROM python:3.11-slim-bullseye@sha256:34fb194372f3390c5986dd0a94f21de5f1615d0e1684c977e083fab06b2018be

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=on \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONPATH=/culture_backoffice_data

# 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update -q && \
    apt-get install -y -q \
      wget \
      unzip \
      curl \
      gnupg2 \
      ca-certificates \
      libglib2.0-0 \
      libnss3 \
      libgconf-2-4 \
      libfontconfig1 \
      libxi6 \
      libxcursor1 \
      libxss1 \
      libxcomposite1 \
      libasound2 \
      libxdamage1 \
      libxtst6 \
      libatk1.0-0 \
      libgtk-3-0 \
      libdrm2 \
      libgbm1 \
      fonts-liberation \
      libu2f-udev \
      libvulkan1 \
      xdg-utils \
      tini \
      fonts-nanum \
      libmagic1 \
      --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN fc-cache -fv

# Google Chrome 설치
RUN wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_127.0.6533.88-1_amd64.deb && \
    apt-get install -y ./google-chrome-stable_127.0.6533.88-1_amd64.deb && \
    rm google-chrome-stable_127.0.6533.88-1_amd64.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ChromeDriver 설치
RUN wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/127.0.6533.88/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver-linux64/chromedriver && \
    rm /tmp/chromedriver.zip

# 작업 디렉토리 설정
WORKDIR /culture_backoffice_data

# 전체 프로젝트 복사
COPY . /culture_backoffice_data/

RUN pip install --no-cache-dir -r requirements.txt

# entrypoint.sh 스크립트 복사 및 실행 권한 부여
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 컨테이너 실행 시 entrypoint.sh 실행
ENTRYPOINT ["/entrypoint.sh"]