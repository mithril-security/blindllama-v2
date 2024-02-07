#!/bin/bash

apt update && apt install git-lfs jq

GITHUB_TOKEN=$(curl -X POST -H  "Content-Type: application/json" -H "Authorization: Bearer $(gcloud auth print-access-token)" https://cloudbuild.googleapis.com/v2/projects/amd-sev-356012/locations/europe-west1/connections/blindllama-v2/repositories/mithril-security-blindllama-v2:accessReadToken | jq .token)

git-lfs install

GIT_LFS_SKIP_SMUDGE=1 git -c credential.helper= -c "credential.https://github.com/.helper=!f() { echo password=$GITHUB_TOKEN; }" lfs pull
