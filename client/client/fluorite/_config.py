import os
from dataclasses import dataclass, field

from fluorite.attestation.verifier import PlatformKind

from .logging import log


@dataclass
class FeatureFlags:
    fetch_attestation_document_over_insecure_connection: bool = True


@dataclass
class Config:
    """Configuration of Fluorite."""

    target: PlatformKind = PlatformKind.AZURE_TRUSTED_LAUNCH  # qemu or azure
    attestation_endpoint_base_url: str = (
        "https://attestation-endpoint.api.localhost"
    )
    api_url: str = "https://api.cloud.localhost"
    debug: bool = False
    feature_flags: FeatureFlags = field(default_factory=FeatureFlags)


def warn_if_insecure_config(config: Config) -> bool:
    is_insecure = False
    if config.target != "azure":
        log.warning(
            "Insecure config detected. Target is {config.target}, not 'azure'. "
        )
        is_insecure = True
    if config.debug:
        log.warning("Insecure config detected. Debug mode enabled.")
        is_insecure = True
    if config.feature_flags.fetch_attestation_document_over_insecure_connection:
        log.warning(
            "Insecure config detected. Feature fetch_attestation_document_over_insecure_connection enabled."
        )
        is_insecure = True

    return is_insecure


API_KEY = os.getenv("BLIND_LLAMA_API_KEY", "")
CONFIG = Config()
warn_if_insecure_config(CONFIG)
