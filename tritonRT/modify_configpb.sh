#!/bin/bash 

set -euxo pipefail

# Check if exactly one argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <model-name>"
    echo "model-name can be either 'Llama-2-7b-hf' or 'gpt2-medium'"
    exit 1
fi

# The model name is the first argument
model_name="$1"

# rm ./disk/model/$MODEL_NAME/*.safetensors
# rm ./disk/model/$MODEL_NAME/*.bin

if [ "$model_name" == 'Llama-2-7b-hf' ]
then
    tokenizer_dir="$model_name" \
    tokenizer_type="auto" \
    envsubst < ./disk/inflight_batcher_llm/preprocessing/config.pbtxt | sponge ./disk/inflight_batcher_llm/preprocessing/config.pbtxt

    tokenizer_dir="$model_name" \
    tokenizer_type="auto" \
    envsubst < ./disk/inflight_batcher_llm/postprocessing/config.pbtxt| sponge ./disk/inflight_batcher_llm/postprocessing/config.pbtxt

    decoupled_mode="false" \
    engine_dir="/engines/1-gpu/" \
    batch_scheduler_policy="max_utilization" \
    envsubst <  ./disk/inflight_batcher_llm/tensorrt_llm/config.pbtxt | sponge  ./disk/inflight_batcher_llm/tensorrt_llm/config.pbtxt

elif [ "$model_name" == 'gpt2-medium' ]
then
    tokenizer_dir="$model_name" \
    tokenizer_type="auto" \
    envsubst < ./disk/inflight_batcher_llm/preprocessing/config.pbtxt | sponge ./disk/inflight_batcher_llm/preprocessing/config.pbtxt

    tokenizer_dir="$model_name" \
    tokenizer_type="auto" \
    envsubst < ./disk/inflight_batcher_llm/postprocessing/config.pbtxt| sponge ./disk/inflight_batcher_llm/postprocessing/config.pbtxt

    decoupled_mode="false" \
    engine_dir="/engines/1-gpu/" \
    envsubst <  ./disk/inflight_batcher_llm/tensorrt_llm/config.pbtxt | sponge  ./disk/inflight_batcher_llm/tensorrt_llm/config.pbtxt

else
    echo "Unsupported model"
    exit 1
fi