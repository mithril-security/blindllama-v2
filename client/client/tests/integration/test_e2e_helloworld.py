import copy

import pytest
import requests
from blindllamav2.attestation.attestation_retriever import (
    AttestationValidatorProtocol,
    PlatformKind,
)
from blindllamav2.attestation.attested_session import AttestedSession
from blindllamav2.attestation.errors import AttestationError
from blindllamav2.attestation_validator import AttestationValidator
from blindllamav2.security_config import (
    APPLICATION_DISK_ROOTHASH,
    EXPECTED_OS_MEASUREMENTS,
)

"""
All the tests defined in this file are integration tests 
for the "Hello World" application disk running on the Mithril OS.
They are expected to run against either:
 * a live QEMU VM 
 * a live Azure VM 

** QEMU VM ** : ./run_test_qemu_helloworld.sh script at the root of the repository.

** Azure VM : **
You need to setup the VM and then update your hosts file.
To update your hosts file accordingly you can use :
```
VM_IP_ADDRESS="REPLACE_WITH_YOUR_VM"
sudo ./update_hosts_entry.sh "$VM_IP_ADDRESS" "api.helloworld-app.example.com"
sudo ./update_hosts_entry.sh "$VM_IP_ADDRESS" "attestation-endpoint.api.helloworld-app.example.com"
```
Then run in the (dev) virtual env and at the root of the poetry project (client/client/)
pytest tests/integration/test_e2e_helloworld.py -k azure
"""

API_URL = "https://api.helloworld-app.example.com"
ATTESTATION_ENDPOINT_BASE_URL = (
    "https://attestation-endpoint.api.helloworld-app.example.com/"
)


def create_attested_session(
    attestation_validator: AttestationValidatorProtocol,
    fetch_attestation_document_over_insecure_connection: bool = True,
):
    """Short form for AttestedSession with URL set."""
    return AttestedSession(
        api_url=API_URL,
        attestation_endpoint_base_url=ATTESTATION_ENDPOINT_BASE_URL,
        attestation_validator=attestation_validator,
        fetch_attestation_document_over_insecure_connection=fetch_attestation_document_over_insecure_connection,
    )


@pytest.mark.parametrize(
    "platform_kind",
    [PlatformKind.AZURE_TRUSTED_LAUNCH, PlatformKind.SIMULATION_QEMU],
    ids=["azure", "qemu"],
)
class Test:
    def test_helloworld(self, platform_kind):
        attestation_validator = AttestationValidator(
            platform_kind=platform_kind,
            expected_application_disk_roothash=APPLICATION_DISK_ROOTHASH,
            expected_os_measurements=EXPECTED_OS_MEASUREMENTS[
                platform_kind
            ],
        )
        session = create_attested_session(
            attestation_validator=attestation_validator,
        )

        req = session.get(API_URL)
        req.raise_for_status()
        assert "HTTP Hello World" in req.text

    def test_helloworld_bad_app_disk_roothash(self, platform_kind):
        bad_app_disk_roothash = 64 * "0"
        attestation_validator = AttestationValidator(
            platform_kind=platform_kind,
            expected_application_disk_roothash=bad_app_disk_roothash,
            expected_os_measurements=EXPECTED_OS_MEASUREMENTS[platform_kind],
        )
        with pytest.raises(AttestationError):
            create_attested_session(
                attestation_validator=attestation_validator,
            )

    def test_helloworld_bad_expected_os_measurements(self, platform_kind):
        # Mutate PCR[0]
        expected_os_measurements = copy.deepcopy(EXPECTED_OS_MEASUREMENTS[platform_kind])
        expected_os_measurements.measurements[0] = 64 * "0"

        attestation_validator = AttestationValidator(
            platform_kind=platform_kind,
            expected_application_disk_roothash=APPLICATION_DISK_ROOTHASH,
            expected_os_measurements=expected_os_measurements,
        )
        with pytest.raises(AttestationError):
            create_attested_session(
                attestation_validator=attestation_validator,
            )

def test_qemu_helloworld_fetch_att_doc_over_https_should_fail():
    # Since the local QEMU server certificate is not added to the client's trust store
    # (or OS trust store) we expect an error while fetching the attestation document.
    
    attestation_validator = AttestationValidator(
        platform_kind=PlatformKind.SIMULATION_QEMU,
        expected_application_disk_roothash=APPLICATION_DISK_ROOTHASH,
        expected_os_measurements=EXPECTED_OS_MEASUREMENTS[PlatformKind.SIMULATION_QEMU],
    )

    with pytest.raises(requests.exceptions.SSLError):
        create_attested_session(
            attestation_validator=attestation_validator,
            fetch_attestation_document_over_insecure_connection=False,
        )
