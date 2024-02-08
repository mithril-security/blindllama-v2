#!/bin/bash

apt -y update && apt install -y git-lfs jq

GITHUB_TOKEN=$(curl -X POST -H  "Content-Type: application/json" -H "Authorization: Bearer $(gcloud auth print-access-token)" https://cloudbuild.googleapis.com/v2/projects/amd-sev-356012/locations/europe-west1/connections/blindllama-v2/repositories/mithril-security-blindllama-v2:accessReadToken | jq .token)
gcloud auth print-access-token
# gcloud builds connections describe blindllama-v2 --region=europe-west1
git remote remove origin
git remote add origin https://$GITHUB_TOKEN@github.com/mithril-security/blindllama-v2.git
GIT_LFS_SKIP_SMUDGE=1 git lfs pull
