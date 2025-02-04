FROM python:3.11-slim-bullseye@sha256:34fb194372f3390c5986dd0a94f21de5f1615d0e1684c977e083fab06b2018be

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=on \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# 패키지 업데이트 및 필요한 패키지 설치
ENV ACCEPT_EULA=Y

RUN apt-get update -q && \
    apt-get upgrade -y -q && \
    apt-get install -y -q \
    build-essential \
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
    libmagic1 \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Google Chrome 설치 (127.0.6533.88 버전)
RUN wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_127.0.6533.88-1_amd64.deb && \
    apt-get install -y ./google-chrome-stable_127.0.6533.88-1_amd64.deb && \
    rm google-chrome-stable_127.0.6533.88-1_amd64.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 설치된 Chrome 버전 확인
RUN google-chrome --version

# ChromeDriver 설치 (크롬 버전과 일치)
RUN wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/127.0.6533.88/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver-linux64/chromedriver && \
    rm /tmp/chromedriver.zip

# 설치된 ChromeDriver 버전 확인
RUN /usr/local/bin/chromedriver-linux64/chromedriver --version

# Python 패키지 설치
RUN pip install -U \
    langchain \
    langchain-core \
    langchain-openai \
    langchain-upstage \
    langchain-community \
    langchain-huggingface \
    'fastapi[standard]'
