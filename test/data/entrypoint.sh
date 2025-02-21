#!/bin/sh
set -e

# # 가상 환경 생성 및 활성화
# python3 -m venv /culture_backoffice_data/venv
# . /culture_backoffice_data/venv/bin/activate

# pip 업데이트
pip install --upgrade pip

# 직접 설치할 파이썬 라이브러리 설치
pip install -U \
    langchain \
    langchain-core \
    langchain-openai \
    langchain-upstage \
    langchain-community \
    langchain-huggingface \
    langchain-elasticsearch \
    'fastapi[standard]'

# # 시스템 패키지 업데이트 및 필수 빌드 도구 설치
# apt-get update
# apt-get install -y build-essential gcc g++ curl git default-jdk

# # mecab 설치
# wget https://bitbucket.org/eunjeon/mecab-ko/downloads/mecab-0.996-ko-0.9.2.tar.gz
# tar xvfz mecab-0.996-ko-0.9.2.tar.gz
# cd mecab-0.996-ko-0.9.2
# ./configure
# make
# make check
# make install
# ldconfig
# mecab --version

# wget https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz
# tar xvfz mecab-ko-dic-2.1.1-20180720.tar.gz
# cd mecab-ko-dic-2.1.1-20180720
# ./configure
# make
# make install

# curl -s https://raw.githubusercontent.com/konlpy/konlpy/master/scripts/mecab.sh > mecab_script.sh
# bash mecab_script.sh

# pip install mecab-python
# rm mecab-0.996-ko-0.9.2.tar.gz

# Python 패키지 디렉토리에 __init__.py 파일 생성
mkdir -p /culture_backoffice_data/src/rag/data
touch /culture_backoffice_data/src/__init__.py
touch /culture_backoffice_data/src/rag/__init__.py
touch /culture_backoffice_data/src/rag/data/__init__.py
touch /culture_backoffice_data/src/rag/retriever/__init__.py

apt-get update
apt-get install -y git

# docker-compose에서 전달된 커맨드를 실행
cd /culture_backoffice_data
exec "$@"
