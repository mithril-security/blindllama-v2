# Quick tour for BlindLlama-v2 OpenAI


> :warning: **This is a prototype**

## Introduction

BlindLlama-v2 is a framework for serving Kubernetes-based applications on verifiable and isolated environments called enclaves and deploying them on Cloud VMs equipped with GPUs and vTPMs.

By deploying models like Llama 2 with BlindLlama-v2, end-users can consume AI models with guarantees the admins of the AI infrastructure cannot see users' data as they can verify data is only processed in verifiable environments isolated (leveraging hypervisor isolation) and data will not leave (network isolation).

For developers wishing to deploy their applications with BlindLlama-v2, the process is done in 4 steps:
- Prepare the image
    - Model
    - OS
    - Network configuration
- Generate measurements
- Deploy on Azure
- Integrate the secure client-side SDK

Then, users can consume the Confidential AI service while having guarantees that their data is end-to-end protected and not visible to the AI service's admins.

More information about the security properties, the architecture, and the workflow can be found in our Whitepaper.

In this quick tour, we will show how one can package a Kubernetes application to serve either Llama 2 7b or GPT 2 using TensorRT, prepare measurements to prove the model is served in an enclave, deploy it on Azure VMs with A100 and vTPMs, and finally consume the AI model with confidentiality.

## Core concepts

Trust in our enclaves is derived from 3 core principles:
Transparency source: the code is open-source 
Transparency build: the build is done using SLSA
Transparency run time: the client verifies the server software identity through the measurements of the previously built source code in a transparent manner

## Prerequisites
To run this example, you will need to use a VM with a GPU such as Standard_NC24ads_A100_v4. To run a larger model than the Llama 7B, you may need to use larger machines with more memory and more GPUs, such as the Standard_NC48ads_A100_v4 or the Standard_NC96ads_A100_v4.

The code requires python 3.11 or later.
You will also need to install git lfs, which can be done with:
```console
apt-get update && apt-get install git-lfs -y --no-install-recommends
git lfs install

git submodule update --init --recursive
```

## 1 - Preparing the image
BlindLlama-v2 serves Kubernetes-based images inside enclaves and, therefore, requires developers to package their applications in the appropriate manner.

For this example, several components have to be packaged:
The model weights have to be prepared to be used by TensorRT
The Mithril OS, which is a minimal OS designed to be easily verifiable and provide measurements, has to be integrated into the final image
The application disk is a data disk containing the required container images, such as the attestation generator, the triton server, and the attestation server. The application disk can be measured and a root hash generated, attesting to every file in the disk.
Any changes to the disk will alter the root hash and, therefore, be detected.

### A - Model weights

Triton with TensorRT requires the creation of a model engine that has the weights embedded in it. The following script will generate a model engine for Llama 2 7b.
```console
./launch_container_create_model_engine.sh "Llama-2-7b-hf"
```
To create a model engine for GPT2-medium, use:
```console
./launch_container_create_model_engine.sh "gpt2-medium"
```
Note: The model engines are specific to the GPU they are generated on. If you use an A100 GPU to create the model engine, you must run the BlindLlama-v2 VM on a machine with an A100 GPU.

**By default, the engine generated uses 1 engine. To create the model engine according to your specifications, you may change the create_engine.sh script present at tritonRT/create_engine.sh before creating the model engine.**

```console
python /tensorrtllm_backend/tensorrt_llm/examples/llama/build.py --model_dir /$1/ \
                --dtype bfloat16 \
                --use_gpt_attention_plugin bfloat16 \
                --use_inflight_batching \
                --paged_kv_cache \
                --remove_input_padding \
                --use_gemm_plugin bfloat16 \
                --output_dir /engines/1-gpu/ \
                --world_size 1
```

### B - Production mode:
This will create an OS image in production mode with no means of access to the image. The only point of access is the ingress controller and the endpoints it serves. There is no shell access, SSH, etc.

```console
earthly -i -P +mithril-os --OS_CONFIG='config.yaml'
```

### C - Application disk
This command will create an application disk with the Llama 2 7B model engine (generated earlier) included in it.

```console
earthly -i -P +blindllamav2-appdisk --MODEL="Llama-2-7b-hf"
```
To create an application disk with GPT2-medium use:
```console
earthly -i -P +blindllamav2-appdisk --MODEL="gpt2-medium"
```

### D - Network policy

While the network policy will be part of the disk, it is interesting to explore it further, as it is important for security and privacy. 

The network policy that will be used will be included in the final measurement of the application disk. For instance, we will use the following one to allow data to be loaded inside the enclave, but nothing will leave it except the output of the AI model that will be sent back to the requester.

The network policy file can be found in the annex.

## 2 - Generating measurements
Once the disks are created, we can generate the measurements of the disks. These measurements will be used by the client to verify the server.

Here is how to generate the measurements of the OS disk.
```console
./scripts/generate_expected_measurements_files.py
```
The measurement file contains the PCR values of the OS. A sample measurement file is as follows:
```json
{
    "measurements": {
        "0": "f3a7e99a5f819a034386bce753a48a73cfdaa0bea0ecfc124bedbf5a8c4799be",
        "1": "3d458cfe55cc03ea1f443f1562beec8df51c75e14a9fcf9a7234a13f198e7969",
        "2": "3d458cfe55cc03ea1f443f1562beec8df51c75e14a9fcf9a7234a13f198e7969",
        "3": "3d458cfe55cc03ea1f443f1562beec8df51c75e14a9fcf9a7234a13f198e7969",
        "4": "dd2ccfebe24db4c43ed6913d3cbd7f700395a88679d3bb3519ab6bace1d064c0",
        "12": "0000000000000000000000000000000000000000000000000000000000000000",
        "13": "0000000000000000000000000000000000000000000000000000000000000000"
    }
}
```

To understand better what it means, each PCR measures different parts of the stack:
PCRs  0, 1, 2, and 3 are firmware related measurements.
PCR 4 measures the UKI (initrd, kernel image, and boot stub)
PCR 12 and 13 measure the kernel command line and system extensions. We do not want any of those to be enabled, so we ensure they are 0s.

Here is how to generate the root hash of the application disk.
```console
./scripts/generate_security_config.py
```
The application disk is simply a data disk. Therefore, the only measurement we need is a measurement of everything stored on the disk. The root hash is calculated using dm-verity. It is independent of the OS disk and the OS disk measurement.

A sample root hash is as follows:
```json
{
    "application_disk_roothash": "89ca5b62df40df834b8f7a17ce2cce72247cebbb87b80d220845ec583470605f"
}
```

This root hash represents the full stack we expect to measure, from the Mithril OS to the Triton app, through the weights loaded.
## 3 - Deploying it on Azure
We can now deploy the image on the appropriate Azure VM.

Here are some deployment requirements: 
```console
# qemu-utils to resize disk to conform to azure disk specifications
sudo apt-get install qemu-utils
# Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
# azcopy to copy disk to azure 
https://aka.ms/downloadazcopy-v10-linux
```

Edit `upload_config.sh` with your Azure resource group and region where you want the disk to be created.
```sh
### Replace with your values
AZ_RESOURCE_GROUP="my-resource-group"
AZ_REGION="myregion"
### End
```
Run the following script to upload the disks and create a VM.
```console
./upload.sh
```
This script uploads the disks, creates a VM, adds DNS entries in the local machine's /etc/hosts file, and creates a network rule in the Azure firewall to allow HTTPS requests into the VM. Note that these network rules are regular network rules. The network isolation policies to ensure data does not leave the enclaves are of the OS and k3s.

The model is now up and running and can be queried while having guarantees it is deployed in a VM with no admin access and benefits from network isolation.

## 4 - Confidential consumption with attested TLS
To consume the model securely, we provide a Python client SDK. This SDK will perform attestation by verifying the measurements of the enclave, ensuring they come from genuine vTPMs and that the measurements match the expected secure version of our code.

These measurements are created in the client when the [generate_security_config.py](./scripts/generate_security_config.py) and [generate_expected_measurements_files.py](./scripts/generate_expected_measurements_files.py) scripts are run. You can find the measurements in the client directory at `client/client/blindllamav2/security_config`

Once the attestation passes, we establish a TLS channel that ends up inside our enclave.

This whole process is also known as attested TLS.

### A - Installation
The client may be installed with pip.
```console
apt install tpm2-tools
cd client/client
pip install .
```
### B - Querying the model

Now, we can start consuming the previously deployed model.
We provide an OpenAI-like interface to consume the model, but instead of using regular TLS, our framework performs attested TLS:
```python
import blindllamav2

response = blindllamav2.completion.create(
    fetch_attestation_insecure=True,
    model="meta-llama/Llama-2-7b-hf",
    text_input="What is machine Learning?",
    bad_words="",
    stop_words="",
    max_tokens=20,
)

print(response)

## What happens under the hood

from blindllamav2._config import CONFIG
from blindllamav2.attestation.attested_session import AttestedSession
from blindllamav2.attestation_validator import AttestationValidator
from blindllamav2.security_config import (
    APPLICATION_DISK_ROOTHASH,
    EXPECTED_OS_MEASUREMENTS,
)
from blindllamav2.attestation.verifier import PlatformKind
from blindllamav2.completion import PromptRequest

print(f"\n Expected OS measurements: {EXPECTED_OS_MEASUREMENTS[CONFIG.target]} \n")
print(f"Expected application disk roothash: {APPLICATION_DISK_ROOTHASH} \n")

# A validator class that verifies that the attestation report matches expected measurements 
attestation_validator = AttestationValidator(
    platform_kind=PlatformKind.AZURE_TRUSTED_LAUNCH,
    expected_application_disk_roothash=APPLICATION_DISK_ROOTHASH,
    expected_os_measurements=EXPECTED_OS_MEASUREMENTS[CONFIG.target],
)

# Creates a session with the obtained TLS certificate from the server after validating server state
session = AttestedSession(
    api_url=CONFIG.api_url,
    attestation_endpoint_base_url=CONFIG.attestation_endpoint_base_url,
    attestation_validator=attestation_validator,
    fetch_attestation_document_over_insecure_connection=True,  # CONFIG.feature_flags.fetch_attestation_document_over_insecure_connection
)

prompt = PromptRequest(text_input="What is machine Learning?", max_tokens=20, bad_words="", stop_words="")

req = session.post(f"{CONFIG.api_url}/v2/models/ensemble/generate", json=prompt.dict())
req.raise_for_status()
print(req.text)
```
## Annex - Information on network Policy and Isolation
The network policy is implemented individually for the k3s pods as well as for the host.
The host network is controlled by iptables rules. The exact rules are:
```
*filter
# Allow localhost connections to permit communication between k3s components
-A INPUT -p tcp -s localhost -d localhost -j ACCEPT
-A OUTPUT -p tcp -s localhost -d localhost -j ACCEPT
# Allow connection to Azure IMDS to get the VM Instance userdata
-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A OUTPUT -p tcp -d 169.254.169.254 --dport 80 -j ACCEPT
# DNS over UDP
-A INPUT -p udp --sport 53 -j ACCEPT
-A INPUT -p udp --dport 53 -j ACCEPT
-A OUTPUT -p udp --sport 53 -j ACCEPT
-A OUTPUT -p udp --dport 53 -j ACCEPT
# DNS over TCP
-A INPUT -p tcp --sport 53 -j ACCEPT
-A INPUT -p tcp --dport 53 -j ACCEPT
-A OUTPUT -p tcp --sport 53 -j ACCEPT
-A OUTPUT -p tcp --dport 53 -j ACCEPT
# Drop all other traffic
-A OUTPUT -j DROP
-A INPUT -j DROP
COMMIT
```
In the repository they can be found in [rules.v4](mithril-os/mkosi/rootfs/mkosi.extra/etc/iptables/rules.v4) and [rules.v6](mithril-os/mkosi/rootfs/mkosi.extra/etc/iptables/rules.v6)

These rules block all incoming and outgoing traffic except for DNS queries and localhost connections. The rules are applied on boot by the iptables-persistent package. You can verify that the package is installed if you take a look at the [mkosi.conf](mithril-os/mkosi/rootfs/mkosi.conf.j2) file.

Similarly for k3s we set rules to allow incoming traffic only to the ingress controller which acts as reverse proxy. Outgoing traffic is also restricted to the reverse proxy. All other traffic not destined for or leaving from the reverse proxy is blocked.
Rules are also in place to allow traffic from the reverse proxy to the appropriate container (either blindllamav2 or the attestation server).

These rules are as follows:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-caddy-ns
  namespace: caddy-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: caddy-ingress
  namespace: caddy-system
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: caddy-ingress-controller
  ingress:
  - from:
    - ipBlock:
        cidr: 0.0.0.0/0
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: caddy-egress
  namespace: caddy-system
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: caddy-ingress-controller
  policyTypes:
  - Egress
  egress:
  - {}
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ingress-to-attestation-server
  namespace: caddy-system
spec:
  podSelector:
    matchLabels:
      app: attestation-server
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: "caddy-system"
      podSelector:
        matchLabels:
          app.kubernetes.io/name: caddy-ingress-controller
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ingress-to-blindllamav2
spec:
  podSelector:
    matchLabels:
      app: blindllamav2
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: "caddy-system"
      podSelector:
        matchLabels:
          app.kubernetes.io/name: caddy-ingress-controller
```
When the client tries to connect to the server it first retrieves the attestation report which is a quote from the TPM. The client uses the measurements stored in the `security_config` to validate the quote received from the TPM. 

If there are any changes in the host networking rules, it will reflect in the PCR values (PCR 4) of the OS measurement and the connection will be terminated. If there are any changes in the k3s network policy, it will reflect in the application disk root hash measurement (PCR 15) and the connection will be terminated.
