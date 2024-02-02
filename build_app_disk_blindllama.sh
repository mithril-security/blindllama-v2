#!/bin/bash 

set -euxo pipefail


tmpdir=".tmp/blindllama-disk-bis"
outputdir="output/blindllama"

# Cleaning up old work
rm -rf $tmpdir 
rm -rf $outputdir

# Prepare directories
mkdir -p $tmpdir
mkdir -p $outputdir

# Copy the blindllama app disk content base
cp -r .tmp/blindllama-disk/. $tmpdir


echo "Copying model to application disk..."
mkdir -p output/inputs
( cd "prepared_model" && find "." -type f -exec sha256sum {} \; ) > output/inputs/PREPARED_MODEL.SHA256SUMS

cp -al prepared_model/model $tmpdir/disk/
cp -al prepared_model/engines $tmpdir/disk/

echo "Finished copying model"


echo "Adding container images to application disk..."
mkdir $tmpdir/disk/container-images/

# Hard links to avoid a copy 
# images name:
# Define the source directory for the images
source_dir="images/blindllama"

# Define the target directory where hard links will be created
target_dir="$tmpdir/disk/container-images"

# List of docker image names to be included in the disk
image_names=(
    "attestation-generator.tar.gz"
    "attestation-server-latest.tar.gz"
    "ingress-controller-latest.tar.gz"
    "k8s-tpm-device-plugin-image.tar.gz"
    # "nvcr-io-nvidia-tritonserver-23-10-trtllm-python-py3.tar.gz"
    "nvidia-device-plugin-latest.tar.gz"
)

# Loop over each image name and create a hard link
for image_name in "${image_names[@]}"; do
    source_file="$source_dir/$image_name"
    target_file="$target_dir/$image_name"
    
    # Check if the source file exists
    if [ -e "$source_file" ]; then
        # Create a hard link
        ln "$source_file" "$target_file"
        echo "Created hard link for $image_name"
    else
        echo "Source file $source_file does not exist"
        exit 1
    fi
done

echo "Finished adding images to disk"

echo "Starting building disk..."

echo "..Obtaining debian-systemd image from earthly..."
earthly +debian-systemd
echo "..debian-systemd loaded"

docker run --rm  -v "$(realpath $outputdir)":/output -v "$(realpath $tmpdir)":/workdir/:ro \
  -w /workdir debian-systemd /bin/sh -c "\
touch /output/disk.raw; \
export SOURCE_DATE_EPOCH=0; \
systemd-repart \
    --empty=allow \
    --size=auto \
    --dry-run=no \
    --json=pretty \
    --no-pager \
    --offline=yes \
    --seed 71601f80-beac-47c3-80f8-97f8c2ff4fcf \
    --definitions=. \
    /output/disk.raw > /output/application_disk_info.json \
"
echo "Finished building disk : $outputdir/disk.raw"
