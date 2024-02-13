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
    python3 ./scripts/build_wheel.py --trt_root=/usr/local/tensorrt --skip_building_wheel)
    