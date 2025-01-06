FROM nvidia/cuda:11.7.1-cudnn8-devel-ubuntu22.04

# 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# 기본 패키지 설치
RUN apt-get update && apt-get install -y \
    git python3-pip python3-dev libglib2.0-0 libpq-dev gcc

# PyTorch 설치 (CUDA 11.7 호환)
RUN pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2

# 기본 쉘 실행
CMD ["bash"]
