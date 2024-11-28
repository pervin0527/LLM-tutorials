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
```


## Step1 - 싱글턴 데이터셋

 - Train Dataset : [https://huggingface.co/datasets/nlpai-lab/kullm-v2](https://huggingface.co/datasets/nlpai-lab/kullm-v2)