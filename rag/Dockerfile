FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu20.04
ARG DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
        git \
        python3-pip \
        python3-dev \
        python3-opencv \
        libglib2.0-0 \
        libpq-dev gcc

# Google Chrome 설치 (127.0.6533.88 버전)
RUN wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_127.0.6533.88-1_amd64.deb && \
    apt-get update && \
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

    
COPY requirements.txt ./requirements.txt
RUN python3 -m pip install --no-cache-dir -r ./requirements.txt
RUN pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118

ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility