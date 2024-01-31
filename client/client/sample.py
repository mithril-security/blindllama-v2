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