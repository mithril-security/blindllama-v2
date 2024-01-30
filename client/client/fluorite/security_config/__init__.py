import importlib
import json

from ..attestation.tpm import ExpectedMeasurements
from ..attestation.verifier import PlatformKind

EXPECTED_OS_MEASUREMENTS = {
    PlatformKind.SIMULATION_QEMU: ExpectedMeasurements(
        **json.loads(
            importlib.resources.files(__package__)  # type: ignore
            .joinpath("measurements_qemu.json")
            .read_text()
        )
    ),
    PlatformKind.AZURE_TRUSTED_LAUNCH: ExpectedMeasurements(
        **json.loads(
            importlib.resources.files(__package__)  # type: ignore
            .joinpath("measurements_azure.json")
            .read_text()
        )
    ),
}

app_identity = json.loads(
    importlib.resources.files(__package__).joinpath("application.json").read_text()  # type: ignore
)
APPLICATION_DISK_ROOTHASH = app_identity["application_disk_roothash"]
APPLICATION_PCR = 15
