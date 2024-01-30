#!/bin/bash

## Update the submodules
cd tensorrtllm_backend

## Install git-lfs if needed
apt-get update && apt-get install git-lfs -y --no-install-recommends
git lfs install
git submodule update --init --recursive

# cd tensorrt_llm/cpp/tensorrt_llm/batch_manager/x86_64-linux-gnu/ && git lfs pull
cd ..

# Create a directory to store the model engine that will be created in the next step
mkdir -p engines

# Using the docker container to avoid installing all the dependencies required to compile a model engine on the local machine
# The create engine script installs the tensort_llm python package which compiles the engine. This takes a while, may be well worth it
# to create a container image with the python package pre-installed to save on time as long as we can transparently prove the contants and purpose of 
# said image. SLSA can build this image to address this issue.
sudo docker run --net host --shm-size=2g --gpus all \
            --ulimit memlock=-1 --ulimit stack=67108864 \
            -v $(pwd)/tensorrtllm_backend:/tensorrtllm_backend \
            -v $(pwd)/application_disk/model/$1:/$1 \
            -v $(pwd)/engines:/engines \
            -v $(pwd)/tritonRT/create_engine.sh:/opt/tritonserver/create_engine.sh \
            nvcr.io/nvidia/tritonserver:23.10-trtllm-python-py3 ./create_engine.sh $1