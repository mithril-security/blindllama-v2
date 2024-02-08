#!/bin/sh

set -eux

# Need to install
# TODO build an image with the required dependency
apk add --no-cache bash

/usr/bin/earthly-entrypoint.sh || true

mkdir -p output/osdisk
earthly -P +mithril-os-ci --OS_CONFIG='config.yaml'

directory="output/osdisk"

# Find all files in the directory and compute their SHA256 checksum
( cd $directory && find "." -type f -exec sha256sum {} \; ) > output/DIGEST
