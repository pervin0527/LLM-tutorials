FROM python:3.9-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    --fix-broken && \
    rm -rf /var/lib/apt/lists/*

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


# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt


# Copy application files
COPY src/ /app/
WORKDIR /app

# Default command
CMD ["python", "main.py"]
