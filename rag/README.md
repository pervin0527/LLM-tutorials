```bash
docker pull selenium/standalone-chrome

docker run -d -p 4444:4444 --name selenium-chrome selenium/standalone-chrome
```

```bash
cd /home/pervinco/LLM-tutorials/rag

docker build -t selenium-python-app .

docker run --rm selenium-python-app
```
