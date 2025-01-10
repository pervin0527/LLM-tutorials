```bash
ubuntu-drivers devices
lshw -numeric -C display
lspci | grep -i nvidia

## 자동설치
sudo ubuntu-drivers autoinstall

## 수동으로 원하는 버전 설치
sudo apt install nvidia-driver-560
sudo reboot
```

```bash
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update

sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```


```bash
cd /home/pervinco/LLM-tutorials/rag

docker build -t rag_image:latest .

docker run --gpus all --name rag -it -v /home/jake:/home/jake rag_image:latest
```

```bash
apt install -y tesseract-ocr libtesseract-dev tesseract-ocr-kor
pip install pytesseract easyocr
```