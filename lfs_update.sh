#!/bin/bash

set -euo pipefail

apt-get -y update && apt-get install -y git-lfs

git config --global url."https://$1@github.com/".insteadOf "https://github.com/"
GIT_LFS_SKIP_SMUDGE=1 git lfs pull 
