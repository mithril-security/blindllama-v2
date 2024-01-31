import json
from pathlib import Path

import pytest
from blindllamav2.attestation import (
    AttestationError,
    perform_remote_attestation_and_extract_webserver_ca,
)
from blindllamav2.attestation.tpm import ExpectedMeasurements
from blindllamav2.attestation.verifier import PlatformKind
from blindllamav2.attestation_validator import AttestationValidator

ATTESTATION_ENDPOINT_BASE_URL = (
    "https://attestation-endpoint.api.cloud.mithrilsecurity.io"
)

EXPECTED_APP_ROOT_HASH = (
    "16cda68838bdce2b4a7955e36ac7ed01be881144af62db0b001cd278ee0fd328"
)


@pytest.fixture
def measurements_azure():
    path = Path(__file__).parent / "measurements_azure.json"
    with open(path, "rt") as file:
        return ExpectedMeasurements(**json.load(file))


@pytest.fixture
def sample_attestation_json():
    return json.loads(
        open(Path(__file__).parent / "sample_azure_attestation.json", "rt").read()
    )


@pytest.fixture
def mock_attestation_endpoint(requests_mock):
    def _mock_attestation(attestation_doc):
        requests_mock.get(
            f"{ATTESTATION_ENDPOINT_BASE_URL}/attestation.json",
            json=attestation_doc,
        )

    return _mock_attestation


def test_perform_remote_attestation_success(
    mock_attestation_endpoint, sample_attestation_json, measurements_azure
):
    """Test perform_remote_attestation_and_extract_webserver_ca
    by mocking a connection that receives a valid attestation document
    that attest the correct server identity.
    """
    mock_attestation_endpoint(sample_attestation_json)
    attestation_validator = AttestationValidator(
        platform_kind=PlatformKind.AZURE_TRUSTED_LAUNCH,
        expected_application_disk_roothash=EXPECTED_APP_ROOT_HASH,
        expected_os_measurements=measurements_azure,
    )
    webserver_rootca = perform_remote_attestation_and_extract_webserver_ca(
        attestation_endpoint_base_url=ATTESTATION_ENDPOINT_BASE_URL,
        attestation_validator=attestation_validator,
    )
    assert webserver_rootca == sample_attestation_json["webserver_rootca"]


def test_perform_remote_attestation_fail_doesnt_match_expected_measurements(
    mock_attestation_endpoint, sample_attestation_json, measurements_azure
):
    """Ensure perform_remote_attestation_and_extract_webserver_ca fails
    when the attestation doen't attest the expected server identity (wrong PCR[0])
    """
    mock_attestation_endpoint(sample_attestation_json)
    measurements_azure.measurements[0] = 64 * "0"

    attestation_validator = AttestationValidator(
        platform_kind=PlatformKind.AZURE_TRUSTED_LAUNCH,
        expected_application_disk_roothash=EXPECTED_APP_ROOT_HASH,
        expected_os_measurements=measurements_azure,
    )
    with pytest.raises(AttestationError):
        perform_remote_attestation_and_extract_webserver_ca(
            attestation_endpoint_base_url=ATTESTATION_ENDPOINT_BASE_URL,
            attestation_validator=attestation_validator,
        )


def test_perform_remote_attestation_altered(
    mock_attestation_endpoint, measurements_azure, sample_attestation_json
):
    """Test that it rejects a tampered attestation document where
    an attacker has replaced the webserver_rootca with its own.
    """
    sample_attestation_json["webserver_rootca"] = (
        Path(__file__).parent / "snakeoil_ca.crt"
    ).read_text()
    mock_attestation_endpoint(sample_attestation_json)

    attestation_validator = AttestationValidator(
        platform_kind=PlatformKind.AZURE_TRUSTED_LAUNCH,
        expected_application_disk_roothash=EXPECTED_APP_ROOT_HASH,
        expected_os_measurements=measurements_azure,
    )
    with pytest.raises(AttestationError):
        perform_remote_attestation_and_extract_webserver_ca(
            attestation_endpoint_base_url=ATTESTATION_ENDPOINT_BASE_URL,
            attestation_validator=attestation_validator,
        )


def test_perform_remote_attestation_altered_application_disk_roothash(
    mock_attestation_endpoint, measurements_azure, sample_attestation_json
):
    """Test that it rejects a tampered attestation document where
    an attacker has modified the application disk roothash.

    This check aimed at checking that we verify the cryptographic link between PCR[15] and
    the "claimed" roothash.
    """
    sample_attestation_json["application_disk_roothash"] = 64 * "a"

    expected_app_roothash = 64 * "a"

    mock_attestation_endpoint(sample_attestation_json)

    attestation_validator = AttestationValidator(
        platform_kind=PlatformKind.AZURE_TRUSTED_LAUNCH,
        expected_application_disk_roothash=expected_app_roothash,
        expected_os_measurements=measurements_azure,
    )
    with pytest.raises(AttestationError, match="Application PCR is invalid"):
        perform_remote_attestation_and_extract_webserver_ca(
            attestation_endpoint_base_url=ATTESTATION_ENDPOINT_BASE_URL,
            attestation_validator=attestation_validator,
        )


def test_perform_remote_attestation_fail_application_disk_roothash(
    mock_attestation_endpoint, sample_attestation_json, measurements_azure
):
    """Test that it rejects a attestation document
    that attest a VM with an unexpected application disk roothash.

    To test that we take a good document but we configure everything so that
    it expects a different roothash.
    """

    expected_app_roothash = 64 * "a"

    mock_attestation_endpoint(sample_attestation_json)

    attestation_validator = AttestationValidator(
        platform_kind=PlatformKind.AZURE_TRUSTED_LAUNCH,
        expected_application_disk_roothash=expected_app_roothash,
        expected_os_measurements=measurements_azure,
    )
    with pytest.raises(AttestationError, match="Application disk hash mismatch"):
        perform_remote_attestation_and_extract_webserver_ca(
            attestation_endpoint_base_url=ATTESTATION_ENDPOINT_BASE_URL,
            attestation_validator=attestation_validator,
        )


# def test_azure(override_config):
#     webserver_rootca = retrieve_and_validate_attested_server_ca(
#         blindllamav2._config.CONFIG.attestation_endpoint,
#         expected_measurements=
#     )

#     server_ca_crt_file = tempfile.NamedTemporaryFile(mode="w+t", delete=False)
#     server_ca_crt_file.write(webserver_rootca)
#     server_ca_crt_file.flush()
#     session = requests.Session()
#     session.verify = server_ca_crt_file.name

#     # Test application endpoint
#     r = session.get(blindllamav2._config.CONFIG.api_url)
#     r.raise_for_status()
#     assert "HTTP Hello World" in r.text
