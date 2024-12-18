# LLM-tutorials

## Docker

```bash
docker build -t llm_image:latest .
docker run --gpus all -it --name llm \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /home/pervinco/:/home/pervinco/ \
    -e DISPLAY=$DISPLAY \
    -p 7007:22 \
    llm_image:latest

docker start llm
docker exec -it llm bash

pip install --upgrade ipywidgets notebook jupyterlab
```

## MoRA

```bash
cd /path/to/LLM-tutorials  # 개인 레포지토리로 이동

git submodule add https://github.com/kongds/MoRA.git
git submodule update --init --recursive

git submodule add https://github.com/DopeorNope-Lee/Easy_DPO
git submodule update --init --recursive
```


## Step1 - 싱글턴 데이터셋

 - Train Dataset : [https://huggingface.co/datasets/nlpai-lab/kullm-v2](https://huggingface.co/datasets/nlpai-lab/kullm-v2)