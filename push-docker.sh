#!/usr/bin/env bash

dockerpath="shttksm/app"

echo "Docker ID and Image: $dockerpath"

# Authenticate & Tag
docker login &&\
    docker image tag app $dockerpath

# Push Image
docker image push $dockerpath

# reference, when I pull the image
# docker pull shttkms/app
