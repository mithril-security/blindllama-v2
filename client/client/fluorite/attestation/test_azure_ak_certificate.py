import pytest

from fluorite.attestation.azure_ak_certificate import validate_azure_ak_cert
from fluorite.attestation.errors import AttestationError


def test_empty_cert_chain_should_fail():
    with pytest.raises(AttestationError):
        validate_azure_ak_cert([])
