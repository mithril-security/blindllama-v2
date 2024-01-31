import hashlib
from dataclasses import dataclass

from . import security_config
from .attestation import tpm
from .attestation.attestation_retriever import PlatformKind
from .attestation.errors import AttestationError
from .attestation.verifier import VerifiedAttestationDocument


@dataclass(frozen=True)
class AttestationValidator:
    """Class to validate attestation for BlindLlamav2.

    The validator only supports a single baseline. If you need more complex
    validation you will need to implement your own validator.

    Args:
        platform_kind (PlatformKind): Type of platform. Should be set to AZURE_TRUSTED_LAUNCH
         in production.
        expected_measurements_os (tpm.ExpectedMeasurements): Expected measurements for the OS
        expected_application_disk_roothash (str): Expected roothash for the application disk
    """

    platform_kind: PlatformKind
    expected_os_measurements: tpm.ExpectedMeasurements
    expected_application_disk_roothash: str

    def validate_measurements(
        self, verified_attestation_doc: VerifiedAttestationDocument
    ) -> None:
        """Validate the measurements in the quote.

        1. Checks the quoted measurements against the expected measurements of the OS and firmware.
        2. Checks the application_disk_roothash is as expected
        3. Using PCR[15], verifies the authenticity of the claimed application_disk
        hash AND the web server root CA by replaying the TPM_Extend operations.

        Args:
            verified_attestation_doc (VerifiedAttestationDocument): a verified attestation document.

        Raises:
            AttestationError: If the attestation document does not pass the validation checks,
                indicating a potential security issue or mismatch in the system's integrity.
        """
        quoted_measurements = verified_attestation_doc.quoted_measurements
        ##  Step 1 : Verifies the quote's PCR values against the expected measurements for the OS and firmware
        for (
            index,
            expected_pcr_value,
        ) in self.expected_os_measurements.measurements.items():
            if index not in quoted_measurements.pcrs.sha256:
                raise AttestationError((f"Quote is missing PCR[{index}], ",))

            if quoted_measurements.pcrs.sha256[index] != expected_pcr_value:
                raise AttestationError(
                    f"Wrong PCR value for PCR[{index}], "
                    f"expected {expected_pcr_value}, "
                    f"got {quoted_measurements.pcrs.sha256[index]} instead"
                )

        ## Step 2: Check the application_disk_roothash is as expected

        if (
            self.expected_application_disk_roothash
            != verified_attestation_doc.application_disk_roothash
        ):
            raise AttestationError(
                "Application disk hash mismatch. Malicious disk may be mounted."
            )

        ## Step 3 : Check the application PCR
        # Verifies the authenticity of both the application_disk roothash AND
        # the web server root CA by replaying the TPM_Extend operations on this PCR.

        SENTINEL_HASH = 32 * b"\0"

        measured_hashes = [
            bytes.fromhex(verified_attestation_doc.application_disk_roothash),
            SENTINEL_HASH,
            hashlib.sha256(verified_attestation_doc.webserver_rootca.encode()).digest(),
        ]

        # Verifies the PCR state in the quote matches the one replayed
        expected_app_pcr = tpm.replay_extend_operations(measured_hashes)
        if (
            quoted_measurements.pcrs.sha256[security_config.APPLICATION_PCR]
            != expected_app_pcr
        ):
            raise AttestationError("Application PCR is invalid.")

    def webserver_rootca(
        self, verified_attestation_doc: VerifiedAttestationDocument
    ) -> str:
        return verified_attestation_doc.webserver_rootca
