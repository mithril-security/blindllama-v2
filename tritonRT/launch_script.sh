#!/bin/bash

# Because of this issue: https://github.com/NVIDIA/TensorRT-LLM/issues/656
cp /tensorrtllm_backend/tensorrt_llm/cpp/build/tensorrt_llm/plugins/lib* backends/tensorrtllm/

python3 /launch_triton_server.py --world_size=1 --model_repo=/inflight_batcher_llm

tail -f /dev/null