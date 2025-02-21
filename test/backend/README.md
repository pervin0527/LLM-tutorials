# culture_backend

## Local
```bash
## app
docker build -t culture_backend .
docker run -it \
  --name culture_backend \
  -p 9997:9997 \
  -v /home/jake:/home/jake \
  culture_backend /bin/bash


## mongo db
docker pull mongo:4.4.29
docker run -d --name local-mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=ai \
  -e MONGO_INITDB_ROOT_PASSWORD=glab0110!! \
  -v ~/mongodb-data:/data/db \
  mongo:4.4.29 --auth

```