FROM nvidia/cuda:12.4.1-devel-ubuntu22.04
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -q && \
    apt-get install -y -q \
      python3 \
      python3-pip \
      python3-venv \
      python3-dev \
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
      libopenmpi-dev \
      --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


COPY requirements.txt ./requirements.txt
RUN python3 -m pip install -U --no-cache-dir -r ./requirements.txt        

RUN pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu124

RUN pip install --no-cache-dir -U \
    faiss-gpu \
    langchain \
    langgraph \
    langchain-core \
    langchain-openai \
    langchain-anthropic \
    langchain-upstage \
    langchain-community \
    langchain-huggingface \
    langchain-elasticsearch \
    packaging \
    flash-attn \
    accelerate \
    bitsandbytes \
    deepspeed \
    mpi4py

ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility