```bash

pip install selenium webdriver-manager pandas fastapi "uvicorn[standard]"

## 구글 크롬
wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_127.0.6533.88-1_amd64.deb
apt-get update && apt-get install -y ./google-chrome-stable_127.0.6533.88-1_amd64.deb
rm google-chrome-stable_127.0.6533.88-1_amd64.deb
apt-get clean
rm -rf /var/lib/apt/lists/

## 크롬 드라이버
wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/127.0.6533.88/linux64/chromedriver-linux64.zip
unzip /tmp/chromedriver.zip -d /usr/local/bin/
chmod +x /usr/local/bin/chromedriver-linux64/chromedriver
rm /tmp/chromedriver.zip
```