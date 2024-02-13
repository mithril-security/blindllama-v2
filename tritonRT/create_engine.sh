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

if [ $1 == 'Llama-2-7b-hf' ]
then
    python /tensorrtllm_backend/tensorrt_llm/examples/llama/build.py --model_dir /$1/ \
                    --dtype bfloat16 \
                    --use_gpt_attention_plugin bfloat16 \
                    --use_inflight_batching \
                    --paged_kv_cache \
                    --remove_input_padding \
                    --use_gemm_plugin bfloat16 \
                    --output_dir /engines/$1/1-gpu/ \
                    --world_size 1
elif [ $1 == 'gpt2-medium' ]
then
    python /tensorrtllm_backend/tensorrt_llm/examples/gpt/hf_gpt_convert.py -p 8 -i /$1 -o ./c-model/gpt2 --tensor-parallelism 1 --storage-type float16
    python /tensorrtllm_backend/tensorrt_llm/examples/gpt/build.py --model_dir=./c-model/gpt2/1-gpu/ \
                 --world_size=1 \
                 --dtype float16 \
                 --use_inflight_batching \
                 --use_gpt_attention_plugin float16 \
                 --paged_kv_cache \
                 --use_gemm_plugin float16 \
                 --remove_input_padding \
                 --hidden_act gelu \
                 --parallel_build \
                 --output_dir=/engines/$1/1-gpu/
else
    echo "Unsupported model"
fi
