#!/bin/bash 

# Install CMake
bash /tensorrtllm_backend/tensorrt_llm/docker/common/install_cmake.sh
export PATH="/usr/local/cmake/bin:${PATH}"

# PyTorch needs to be built from source for aarch64
ARCH="$(uname -i)"
if [ "${ARCH}" = "aarch64" ]; then TORCH_INSTALL_TYPE="src_non_cxx11_abi"; \
else TORCH_INSTALL_TYPE="pypi"; fi && \
(cd /tensorrtllm_backend/tensorrt_llm &&
    bash docker/common/install_pytorch.sh $TORCH_INSTALL_TYPE &&
    python3 ./scripts/build_wheel.py --trt_root=/usr/local/tensorrt &&
    pip3 install ./build/tensorrt_llm*.whl)

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda-12.2/compat/lib.real/libcuda.so.1

python /tensorrtllm_backend/tensorrt_llm/examples/llama/build.py --model_dir /$1/ \
                --dtype bfloat16 \
                --use_gpt_attention_plugin bfloat16 \
                --use_inflight_batching \
                --paged_kv_cache \
                --remove_input_padding \
                --use_gemm_plugin bfloat16 \
                --output_dir /engines/1-gpu/ \
                --world_size 1