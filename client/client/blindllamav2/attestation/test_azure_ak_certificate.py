import pytest

from blindllamav2.attestation.azure_ak_certificate import validate_azure_ak_cert
from blindllamav2.attestation.errors import AttestationError


def test_empty_cert_chain_should_fail():
    with pytest.raises(AttestationError):
        validate_azure_ak_cert([])
