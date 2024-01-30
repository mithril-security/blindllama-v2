#!/bin/bash
# We start with a boot.sh
set -e

# Cleanup function to kill all background jobs
cleanup() {
    for pid in $(jobs -p); do
        if kill -0 $pid 2>/dev/null; then  # check if the process is still running
            kill $pid 2>/dev/null
        fi
    done
}

# Set the trap to run the cleanup function upon exiting the script
trap cleanup EXIT

./setup-tpm.sh

swtpm socket --tpm2 -t --tpmstate dir=/tmp/tpm --ctrl type=unixio,path=/tmp/swtpm-sock &

if [ "$(whoami)" == "vscode" ]; then
    sudo chown vscode /dev/kvm
fi

echo "127.0.0.1 attestation-endpoint.api.helloworld-app.example.com " | sudo tee -a /etc/hosts
echo "127.0.0.1 api.helloworld-app.example.com " | sudo tee -a /etc/hosts

qemu-system-x86_64 \
    -enable-kvm \
    -cpu host \
    -smp 6 \
    -m 2048 \
    -bios /usr/share/qemu/OVMF.fd \
    -drive format=raw,file=local/os_disk.raw \
    -drive format=raw,file=local/application_disk.raw \
    -nographic \
    -nic user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:443-:443  \
    -chardev socket,id=chrtpm,path=/tmp/swtpm-sock \
    -tpmdev emulator,id=tpm0,chardev=chrtpm -device tpm-crb,tpmdev=tpm0 > /dev/null &

retry_command() {
    local command="$@"
    local MAX_RETRIES=60
    local RETRY_INTERVAL=2  # seconds
    local retry_count=0

    while true; do
        eval $command && echo "Test successful" && return 0  # If command succeeds, exit the function

        retry_count=$((retry_count + 1))
        if [[ $retry_count -ge $MAX_RETRIES ]]; then
            echo "Max retries reached. Exiting."
            return 1
        fi

        echo "Command failed. Retrying in $RETRY_INTERVAL seconds..."
        sleep $RETRY_INTERVAL
    done
}

# Wait until the server is ready to run the Python test
retry_command 'curl --max-time 1  --fail-with-body -k https://attestation-endpoint.api.helloworld-app.example.com/attestation.json && echo "" && curl -k https://api.helloworld-app.example.com'

cd client/client
poetry install --quiet
poetry run pytest tests/integration/test_e2e_helloworld.py -k "qemu"