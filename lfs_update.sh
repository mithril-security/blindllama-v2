#!/bin/bash

set -euxo pipefail

apt -y update && apt install -y git-lfs


git remote add origin https://$1@github.com/mithril-security/blindllama-v2.git
git config --global url."https://amd-sev-test:$1@github.com/".insteadOf "https://github.com/"
GIT_LFS_SKIP_SMUDGE=1 git lfs pull 

ls -al ./mithril-os/mkosi/rootfs/mkosi.skeleton/usr/local/bin
