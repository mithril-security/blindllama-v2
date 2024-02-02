# preprocessing
sed -i 's#${tokenizer_dir}#/{{ model }}/#' ./disk/inflight_batcher_llm/preprocessing/config.pbtxt
sed -i 's#${tokenizer_type}#auto#' ./disk/inflight_batcher_llm/preprocessing/config.pbtxt
sed -i 's#${tokenizer_dir}#/{{ model }}/#' ./disk/inflight_batcher_llm/postprocessing/config.pbtxt
sed -i 's#${tokenizer_type}#auto#' ./disk/inflight_batcher_llm/postprocessing/config.pbtxt

sed -i 's#${decoupled_mode}#false#' ./disk/inflight_batcher_llm/tensorrt_llm/config.pbtxt
sed -i 's#${engine_dir}#/engines/1-gpu/#' ./disk/inflight_batcher_llm/tensorrt_llm/config.pbtxt
