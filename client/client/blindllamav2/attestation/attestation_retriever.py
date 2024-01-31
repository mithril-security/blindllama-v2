from typing import Protocol, runtime_checkable

import requests

from .errors import AttestationError
from .verifier import (
    AttestationDocument,
    PlatformKind,
    VerifiedAttestationDocument,
    verify_attestation_document,
)


@runtime_checkable
class AttestationValidatorProtocol(Protocol):
    @property
    def platform_kind(self) -> PlatformKind:
        ...

    def validate_measurements(
        self, verified_attestation_doc: VerifiedAttestationDocument
    ):
        """Check the measurements in the quote against expected measurements (or a policy to be defined).

        This validation is done after the quote authenticity checks.
        This method must check the quoted measurements are the expected measurements. These checks should cover the
        entire system (firmware, OS, loaded application).

        In addition, it must check that the webserver_rootca authenticity from the quoted measurements.

        Args:
            verified_attestation_doc (VerifiedAttestationDocument): a verified attestation document.

        Raises:
            AttestationError: If the attestation document does not pass the validation checks,
                indicating a potential security issue or mismatch in the system's integrity.
        """
        ...

    def webserver_rootca(
        self, verified_attestation_doc: VerifiedAttestationDocument
    ) -> str:
        """Extracts the webserver root CA from the attestation document.

        Args:
            verified_attestation_doc (VerifiedAttestationDocument): a verified attestation document.

        Note: The webserver_rootca must be bounded to the quote for the attestation protocol to be sound.
        It is expected that the link is checked by the `validate_measurements` method.
        """
        ...


def perform_remote_attestation_and_extract_webserver_ca(
    attestation_endpoint_base_url: str,
    attestation_validator: AttestationValidatorProtocol,
    fetch_attestation_document_over_insecure_connection: bool = False,
) -> str:
    """Perform the remote attestation of the remote service and returns the webserver root CA of the attested server.

    The function performs the following steps:
        1. Fetches the attestation document from the provided attestation endpoint URL.
        2. Verifies the authenticity of the quote contained within the attestation document.
        3. Validates the quoted measurements using the `attestation_validator`.
        4. Extracts the web server's root CA from the attestation document.

    The web server's root CA authenticity comes from the remote attestation. This root CA can then be
    used to establish an attested TLS channel with the server.

    Args:
        attestation_endpoint_base_url (str): The base URL of the attestation endpoint where
            the attestation document is available.
        attestation_validator (AttestationValidatorProtocol): An instance of a
            class implementing the AttestationValidatorProtocol, used for
            validating the quoted measurements.
        fetch_attestation_document_over_insecure_connection (bool, optional):
            If True, the attestation document will be fetched over an insecure
            connection. Defaults to False.

    Returns:
        str: The PEM-encoded certificate of the web server's root CA.

    Raises:
        AttestationError: If the attestation document fails the verification process.
        RequestsException: If there are issues encountered during the request
            to fetch the attestation document.
    """
    if not isinstance(attestation_validator, AttestationValidatorProtocol):
        raise TypeError(
            "attestation_validator does not implement AttestationValidatorProtocol"
        )
    try:
        r = requests.get(
            f"{attestation_endpoint_base_url}/attestation.json",
            verify=(not fetch_attestation_document_over_insecure_connection),
        )
        r.raise_for_status()
        attestation_doc_json = r.json()
        attestation_doc_parsed = AttestationDocument(**attestation_doc_json)
        verified_attestation_doc = verify_attestation_document(
            attestation_doc_parsed, plaform_kind=attestation_validator.platform_kind
        )
        attestation_validator.validate_measurements(verified_attestation_doc)
        webserver_rootca = attestation_validator.webserver_rootca(
            verified_attestation_doc
        )
    except AttestationError:
        raise
    except requests.exceptions.RequestException as e:
        raise
    except Exception as e:
        raise AttestationError("Unspecified attestation error") from e

    return webserver_rootca
