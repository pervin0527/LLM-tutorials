```bash
docker pull selenium/standalone-chrome

docker run -d -p 4444:4444 --name selenium-chrome selenium/standalone-chrome
```

```bash
cd /home/pervinco/LLM-tutorials/rag

docker build -t rag_image:latest .

docker run --name rag -it -v /home/user:/home/user rag_image:latest
```
