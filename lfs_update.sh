#!/bin/bash

apt -y update && apt install -y git-lfs jq

GITHUB_TOKEN=$(curl -X POST -H  "Content-Type: application/json" -H "Authorization: Bearer $(gcloud auth print-access-token)" https://cloudbuild.googleapis.com/v2/projects/amd-sev-356012/locations/europe-west1/connections/blindllama-v2/repositories/mithril-security-blindllama-v2:accessReadToken | jq .token)
USERNAME=mithril-security

echo $USERNAME > creds
echo $GITHUB_TOKEN >> creds

git config --global credential.helper "./creds"

GIT_LFS_SKIP_SMUDGE=1 git lfs pull
