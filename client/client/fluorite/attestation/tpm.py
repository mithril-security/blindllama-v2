import hashlib
import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel
from pydantic.dataclasses import dataclass

SHA256_HEX_REGEX = re.compile(r"^[0-9a-fA-F]{64}$")


def validate_sha256_hex(v: str):
    if SHA256_HEX_REGEX.fullmatch(v):
        return v.lower()
    else:
        raise AssertionError("Invalid SHA-256")


def validate_pcr_index(index: int):
    if 0 <= index <= 23:
        return index
    else:
        raise AssertionError("Invalid PCR index")


Sha256Hash = Annotated[str, AfterValidator(validate_sha256_hex)]
PcrIndex = Annotated[int, AfterValidator(validate_pcr_index)]


class ExpectedMeasurements(BaseModel):
    measurements: dict[PcrIndex, Sha256Hash]


@dataclass
class Sha256BankPCRMeasurements:
    sha256: dict[PcrIndex, Sha256Hash]


def replay_extend_operations(
    hashes: list[bytes],
    initial_pcr="0000000000000000000000000000000000000000000000000000000000000000",
) -> str:
    """Compute the expected PCR state after a series of TPM_Extend operations.

    This function simulates the TPM_Extend operation by iterating over a list of hash values and
    applying each to the current state of the PCR (Platform Configuration Register), starting from
    an initial PCR state.

    Args:
        hashes (list[bytes]): A list of SHA256 digest used in the TPM_Extend operations.
        initial_pcr (str, optional): The initial state of the PCR as a hexadecimal string. Defaults to 00s.

    Returns:
        str: The final state of the PCR as a hexadecimal string.
    """
    initial_pcr = bytes.fromhex(initial_pcr)
    current_pcr = initial_pcr
    for e in hashes:
        current_pcr = hashlib.sha256(current_pcr + e).digest()

    return current_pcr.hex()
