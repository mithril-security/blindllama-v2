#!/bin/bash

set -euo pipefail


# Check if an image name is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <docker-image-name> <destination_folder>"
    echo "Example: ./export_docker_image_as_tar.sh strm/helloworld-http:latest images/helloworld"
    exit 1
fi

# Assign the first argument as the Docker image name
image_name=$1
destination_folder=$2

mkdir -p "$destination_folder"

# Get the hash of the latest image
new_hash=$(docker images --no-trunc --quiet "$image_name")


# Generate a filename-friendly version of the image name for use in file paths
filename=$(echo $image_name | sed 's/[^a-zA-Z0-9]/-/g')

# Read the hash from the cache file, if it exists
hash_file="$destination_folder/$filename.hash"
if [ -f "$hash_file" ]; then
    previous_hash=$(<"$hash_file")
else
    previous_hash=""
fi

# Compare the new hash with the previous hash
if [ "$new_hash" != "$previous_hash" ]; then
    echo "New image, exporting to $destination_folder/$filename.tar"
    # Save the Docker image
    docker save $image_name > $destination_folder/$filename.tar
    # Update the hash in the cache file
    echo "$new_hash" > "$hash_file"
else
    echo "No update needed. '$destination_folder/$filename.tar' is up-to-date."
fi