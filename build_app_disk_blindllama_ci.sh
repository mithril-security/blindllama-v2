#!/bin/sh

set -eux

# Need to install
# TODO build an image with the required dependency
apk add --no-cache bash

/usr/bin/earthly-entrypoint.sh || true

earthly +attestation-generator-image
./export_docker_image_as_tar.sh attestation-generator images/blindllama

docker pull halverneus/static-file-server:latest
docker tag halverneus/static-file-server:latest attestation-server:latest
./export_docker_image_as_tar.sh attestation-server:latest images/blindllama

earthly +k8s-tpm-device-plugin-image
./export_docker_image_as_tar.sh k8s-tpm-device-plugin-image images/blindllama

docker pull nvcr.io/nvidia/k8s-device-plugin:v0.14.3
docker tag nvcr.io/nvidia/k8s-device-plugin:v0.14.3 nvidia-device-plugin:latest
./export_docker_image_as_tar.sh nvidia-device-plugin:latest images/blindllama


docker pull caddy/ingress:latest 
docker tag caddy/ingress:latest ingress-controller:latest
./export_docker_image_as_tar.sh ingress-controller:latest images/blindllama

# TODO: add triton image
docker pull nvcr.io/nvidia/tritonserver:23.10-trtllm-python-py3
./export_docker_image_as_tar.sh nvcr.io/nvidia/tritonserver:23.10-trtllm-python-py3 images/blindllama


earthly -a +blindllamav2-appdisk-without-images/ .tmp/blindllama-disk

bash build_app_disk_blindllama.sh
rm -rf images .tmp/
mkdir -p output/blindllama

directory="output/blindllama"

# Find all files in the directory and compute their SHA256 checksum
( cd $directory && find "." -type f -exec sha256sum {} \; ) > output/SHA256SUMS
