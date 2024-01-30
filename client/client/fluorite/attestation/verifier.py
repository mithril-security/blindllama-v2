import base64
from typing import assert_never

from OpenSSL import crypto
from pydantic.dataclasses import dataclass
import logging

from .azure_ak_certificate import validate_azure_ak_cert
from .errors import *
from .quote import Quote, QuotedMeasurements, hazmat_read_quote, verify_quote

from enum import Enum


class PlatformKind(Enum):
    AZURE_TRUSTED_LAUNCH = "Azure Trusted Launch"
    SIMULATION_QEMU = "Qemu (Simulation)"


@dataclass
class AttestationDocument:
    """A dataclass representing the attestation document which contains data to verify the integrity of a system.

    This document is obtained by parsing the server response.
    Its content should not be trusted unless duly verified.

    Attributes:
        cert_chain (list[str]): List of X.509 PEM-encoded certificates forming a certificate chain.

        quote (dict[str, str]): A dictionary containing the quote as returned by the server.
            It includes the following keys:
                - 'message': Base64-encoded string of the message.
                - 'signature': Base64-encoded string of the quote's signature to verify the quote's authenticity.
                - 'pcr': Base64-encoded string of the Platform Configuration Register (PCR) raw values that attest to the system's state.

        application_disk_roothash (str): Hex string representing the root hash of the application disk.

        webserver_rootca (str): PEM-encoded string of the web server Root CA certificate.
    """

    cert_chain: list[str]
    quote: dict[str, str]
    application_disk_roothash: str
    webserver_rootca: str


@dataclass
class VerifiedAttestationDocument:
    """A dataclass representing the elements from the attestation document after its quote was verified.

    The quoted measurements authenticity is established but the rest of the document is still unverified.
    It is the role of the attestation validator to ensure that the other values are authentic. This can be done by checking that their values are embedded in the quoted measurements.

    Attributes:
        quoted_measurements (QuotedMeasurements): Verified PCRs state obtained from the quote

        application_disk_roothash (str): Unverified Hex string representing the root hash of the application disk declared, provided by the server.

        webserver_rootca (str): Unverified PEM-encoded string of the web server Root CA certificate, provided by the server.
    """

    quoted_measurements: QuotedMeasurements
    application_disk_roothash: str
    webserver_rootca: str


def verify_attestation_document(
    attestation_doc: AttestationDocument, plaform_kind: PlatformKind
) -> VerifiedAttestationDocument:
    """Verify attestation document is genuine.

    This function performs several steps to verify the integrity and authenticity of an attestation document:
    1. Verifies the certificate chain and extracts the Attestation Key (AK) public key.
    2. Verifies the signature of the quote and extracts the quoted measurements.

    Args:
        attestation_doc (AttestationDocument): A parsed attestation document

    Returns:
        VerifiedAttestationDocument: A document containaing the quoted measurements along with additional data sent by the server.

    Raises:
        AttestationError: If the attestation document is invalid or the verification fails.
    """
    ## Verify certificate chain and extract AK public key

    trusted_ak_cert = validate_azure_ak_cert(cert_chain=attestation_doc.cert_chain)

    trusted_ak_pub_key = trusted_ak_cert.get_pubkey()
    trusted_ak_pub_key_pem = crypto.dump_publickey(
        crypto.FILETYPE_PEM, trusted_ak_pub_key
    ).decode("ascii")

    ## Verify quote signature and extract the quoted measurements

    quote = Quote(**{k: base64.b64decode(v) for k, v in attestation_doc.quote.items()})

    match plaform_kind:
        case PlatformKind.AZURE_TRUSTED_LAUNCH:
            quoted_measurements = verify_quote(
                quote, trusted_pub_key_pem=trusted_ak_pub_key_pem
            )
        case PlatformKind.SIMULATION_QEMU:
            logging.warning("PlatformKind is set to Simulation QEMU. This is insecure.")
            quoted_measurements = hazmat_read_quote(
                quote,
            )
        case _ as unreachable:
            assert_never(unreachable)

    verified_attestation_doc = VerifiedAttestationDocument(
        quoted_measurements=quoted_measurements,
        application_disk_roothash=attestation_doc.application_disk_roothash,
        webserver_rootca=attestation_doc.webserver_rootca,
    )

    return verified_attestation_doc
