# LLM-tutorials

## Docker

```
docker build -t llm .

docker run --gpus all -it --name llm-workspace \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /home/pervinco/:/home/pervinco/ \
    -e DISPLAY=$DISPLAY \
    -p 8888:8888 \
    llm

docker start llm-workspace
docker exec -it llm-workspace bash

pip install --upgrade ipywidgets notebook jupyterlab
```

## MoRA

'''
cd /path/to/LLM-tutorials  # 개인 레포지토리로 이동
git submodule add https://github.com/kongds/MoRA.git
git submodule update --init --recursive
'''


## Step1 - 싱글턴 데이터셋

 - Train Dataset : [https://huggingface.co/datasets/nlpai-lab/kullm-v2](https://huggingface.co/datasets/nlpai-lab/kullm-v2)