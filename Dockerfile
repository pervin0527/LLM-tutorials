FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
        git \
        python3-pip \
        python3-dev \
        python3-opencv \
        libglib2.0-0 \
        libpq-dev gcc

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
RUN pip3 install --no-cache-dir \
    torch==2.4.0 \
    torchvision==0.19.0 \
    torchtext==0.18.0 \
    torchmetrics==1.5.1 \
    opencv-python \
    matplotlib \
    jupyter

ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,display