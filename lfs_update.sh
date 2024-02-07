#!/bin/bash

apt update && apt install git-lfs

curl -x POST -H  "Content-Type: application/json" -H "Authorization: Bearer $(gcloud auth print-access-token)" https://cloudbuild.googleapis.com/v2/projects/amd-sev-356012/locations/europe-west1/connections/blindllama-v2/repositories/mithril-security-blindllama-v2:accessReadToken

git lfs pull 