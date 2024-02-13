#!/bin/bash

docker run --net host --shm-size=2g \
            --ulimit memlock=-1 --ulimit stack=67108864 \
            -v $(pwd)/tensorrtllm_backend:/tensorrtllm_backend \
            -v $(pwd)/tritonRT/create_tensorrt_py_package.sh:/opt/tritonserver/create_tensorrt_py_package.sh \
            nvcr.io/nvidia/tritonserver:23.10-trtllm-python-py3 ./create_tensorrt_py_package.sh

