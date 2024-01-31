<a name="readme-top"></a>

<!-- [![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Apache License][license-shield]][license-url] -->


<!-- PROJECT LOGO -->
<br />
<div align="center">
    <img src="https://github.com/mithril-security/blindai/raw/main/docs/assets/logo.png" alt="Logo" width="80" height="80">

<h1 align="center">BlindLlama-v2</h1>
</div>

 <p align="center">
    <b>Making AI Confidential & Transparent</b><br /><br />

## Prerequisite:
You need to deploy a server running the Llama 2 model for the client to communicate with. 
Instructions to do this are available in the “Deploying blindllamav2 server” document. 

If you’ve already done this, you may proceed to the next step.

## Installation:

First, you'll need to install:
- the `blindllamav2` Python client
- `tpm2-tools`, this library is used by the client to verify the server

```
apt install tpm2-tools
cd client/client
pip install .
```

## Querying the model
Now you're ready to start playing with our privacy-friendly Llama 2 model!

First of all, you'll need to import the `blindllamav2` package.

blindllamav2's client SDK is based on that of `openai` to facilitate uptake as end users are already familiar with their SDK.

Our querying method `completion.create()` accepts six options `model`, `text_input`, `bad_words`, `stop_words`, `max_tokens` and `fetch_attestation_insecure` of which only `text_input` and `max_tokens` are compulsory. :

- The `text_input` option is a string input containing your query input text. Feel free to modify the `text_input` option below to test the API with new prompts!
- The `model` option allows you to select the model you wish to use and is set to Llama-2-7b by default. We currently only support this model, but will add more models in the near future.
- The `bad_words` option is a list of words that should be avoided in the output from the model.
- The `stop_words` option is a list of words that should terminate the output when it occurs.
- The `max_tokens` option is the maximum number of tokens in the output.
- The `fetch_attestation_insecure` option sets whether the attestation report may be fetched over an insecure connection. The attestation report is used to set up the attested TLS connection. By default it is set to True.
This option exists to permit development tests where DNS records are not set.

The `completion.create()` method returns the response of the model as a string.

```
import blindllamav2

# query model and save output in response string
response = blindllamav2.completion.create(
    fetch_attestation_insecure=True,
    text_input="What is machine Learning?",
    bad_words="",
    stop_words="",
    max_tokens=20,
)

print(f"Result:\n{response}") # print out response

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

# Creates a session with the obtaind TLS certificate from the server after validating server state
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

## Fix for lack of a DNS entry:
The *upload.sh* script that uploads the diska nd creates a VM also adds DNS entries for the server on your local system. 

However, if you are using the client on another machine, you can add the following domains to your /etc/hosts file with the VM’s server IP address.


```
serverIP	attestation-endpoint.api.cloud.localhost
serverIP    api.cloud.localhost
```
