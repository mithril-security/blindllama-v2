# Fluorite Server

Some of the code required to build a Fluorite server are present as submodules.

## Update the submodules:
This may take some time and will require sufficient storage as it will download the model weights from huggingface and clone the tensortllm_backend repo. 

You will need to install git-lfs before updating the submodules.
```
apt-get update && apt-get install git-lfs -y --no-install-recommends
git lfs install
git submodule update --init --recursive
```

## Build the custom OS 
Mithril OS can be built in debug or production mode. The debug mode is unsafe for production, it allows root access to the OS and is designed for debugging.

The OS disk cannot toggle between debugging and production mode. To be able to debug your application you will need to build the OS disk in debug mode and vice-versa for production mode.
```
earthly -i -P +mithril-os --OS_CONFIG='config.yaml'
OR
earthly -i -P +mithril-os --OS_CONFIG='config.debug.yaml'
```
A successful build will output the following artifacts:
```
Artifact github.com/mithril-security/fluorite-server:main+mkosi/image output as local/initrd_image.cpio.zst
Artifact github.com/mithril-security/fluorite-server:main+mkosi/image.manifest output as local/initrd.manifest
Artifact github.com/mithril-security/fluorite-server:main+mkosi/image.manifest output as local/os_disk.manifest
Artifact github.com/mithril-security/fluorite-server:main+mkosi/image.raw output as local/os_disk.raw
```

## Build the application disk

You can either create a hello-world appdisk to test with or create an appdisk containing model weights.

### Hello World HTTP server (for testing) :
```
earthly -i -P +helloworld-appdisk
```

### Model appdisk:

**You may skip initalizing the submodules if you have already initialized and updated the submodules earlier.** 

Download and install git lfs, then initialize the submodules (this will download the weights for llama 7B and requires over 25 GB)
```
git lfs install
git submodule init
git submodule update
``` 

Build the model engine:
TensortRT requires the model to be converted to an appropriate format before it can be executed on the backend. To convert the Llama 2 model into the right format we use the launch_container_create_model_engine.sh. The script expects the name of the model directory as an argument.
```
./launch_container_create_model_engine.sh "Llama-2-7b-hf"
```
This will create a folder called “**engines**” with the model engine in it.


Set the model you want to run as the MODEL flag. The default model is llama2-7B and it is the only model included by default in this repo.
```
earthly -i -P +fluorite-appdisk --MODEL="config-llama2-7B-hf.yaml"
```

## Generating expected measurements from OS and application disks:

### OS Disk:

Create an OS disk as mentioned above using either the production or debug modes (**You do not need to rerun this command if you’ve already created the OS disk**):

```
earthly -i -P +mithril-os --OS_CONFIG='config.yaml'

OR

earthly -i -P +mithril-os --OS_CONFIG='config.debug.yaml'
```

Then generate the expected measurements using the following script:
```
./scripts/generate_expected_measurements_files.py
```
This outputs the following measurement files for QEMU and Azure:
measurements_qemu.json
measurements_azure.json

You can find them in the client directory at:

*client/client/fluorite/security_config/*

The files contain the expected PCR register values for the registers 0, 1, 2, 3, 4, 12, and 13
These measurements will be used by the client to compare against the attestation report/quote it receives from the server.

### Application Disk:

Create an application disk as mentioned above (**You do not need to rerun this command if you’ve already created the application disk**):

```
earthly -i -P +fluorite-appdisk --MODEL="config-llama2-7B-hf.yaml"
```

Now we generate the disk roothash which the client will use to verify that the correct application disk is mounted on the VM.
```
./scripts/generate_security_config.py
```

## Test it by booting locally with QEMU

Important: You need to remove swtpm BEFORE installing swtpm-tools. 
These changes were made to make the TPM simulation closer to Azure. Now the TPM even contains a fake AK and can generate fake quote.

Requirements : 
```
sudo apt install swtpm-tools
sudo apt install qemu-kvm virt-manager virtinst libvirt-clients bridge-utils libvirt-daemon-system -y
```

```
./boot.sh
```

You can also run:

```
./run_test_qemu_helloworld.sh
```

It will start the server and check that the server behaves as expected.


## Upload images on Azure and create a VM:


Requirements : 
```
sudo apt-get install qemu-utils
# Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
# Install azcopy 
https://aka.ms/downloadazcopy-v10-linux
``` 

Edit upload.sh with your Azure resource group and region where you want the disk to be created.
```
### Replace with your values
AZ_RESOURCE_GROUP="my-resource-group"
AZ_REGION="myregion"
### End
```

```
./upload.sh
``` 
This script uploads the disks, creates a VM, and creates a network rule to allow HTTPS requests into the VM.

## Test request to server:
```
curl -k --resolve api.cloud.localhost:443:serverIP -X POST https://api.cloud.localhost/v2/models/ensemble/generate -d '{"text_input": "What is machine learning?", "max_tokens": 20, "bad_words": "", "stop_words": ""}'
```

## Auth for GCP CLI
```
gcloud auth login
```
## Auth for Azure CLI

```
az login
az account set --subscription "Microsoft Azure Sponsorship"
```
