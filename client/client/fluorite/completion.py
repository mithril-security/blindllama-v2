from .attestation.verifier import PlatformKind
from pydantic import BaseModel, validator

from .attestation.attested_session import AttestedSession
from .attestation_validator import AttestationValidator

from ._config import CONFIG
from .errors import *
from .security_config import APPLICATION_DISK_ROOTHASH, EXPECTED_OS_MEASUREMENTS


class PromptRequest(BaseModel):
    text_input: str
    max_tokens: int
    bad_words: str
    stop_words: str

    @validator("text_input")
    def valid_input(cls, v):
        if not v:
            raise ValidationError("The prompt cannot be empty")
        return v

    @validator("max_tokens")
    def valid_max_tokens(cls, v):
        if v < 0:
            raise ValidationError("Invalid max_tokens")
        return v


class Client:
    """A class to represent a connection to a Fluorite server."""

    def __init__(self, fetch_attestation_insecure) -> None:
        """Init the Client class.

        Returns:
            Client: Client object.
        """
        attestation_validator = AttestationValidator(
            platform_kind=PlatformKind.AZURE_TRUSTED_LAUNCH,
            expected_application_disk_roothash=APPLICATION_DISK_ROOTHASH,
            expected_os_measurements=EXPECTED_OS_MEASUREMENTS[CONFIG.target],
        )

        self.__session = AttestedSession(
            api_url=CONFIG.api_url,
            attestation_endpoint_base_url=CONFIG.attestation_endpoint_base_url,
            attestation_validator=attestation_validator,
            fetch_attestation_document_over_insecure_connection=fetch_attestation_insecure,
        )
        super().__init__()

    def predict(
        self,
        text_input: str,
        max_tokens: int = 20,
        bad_words: str = "",
        stop_words: str = "",
    ) -> str:
        """Start a prediction.

        Args:
            text_input (str): The prompt on which you want to run a prediction on.
            max_tokens (int, default = 20): The max_tokens in response.
            bad_words (str): A list of bad words (can be empty)
            stop_words (str): A list of stop words (can be empty)

        Returns:
            str: The result of the prediction made by the server
        """
        req = PromptRequest(text_input=text_input, max_tokens=max_tokens, bad_words=bad_words, stop_words=stop_words)
        resp = self.__session.post(
            f"{CONFIG.api_url}/v2/models/ensemble/generate",
            json=req.dict(),
        )
        ret_json = resp.json()
        
        return ret_json["text_output"].strip()


def test_client() -> None:
    Client()


def create(
    fetch_attestation_insecure: bool = CONFIG.feature_flags.fetch_attestation_document_over_insecure_connection,
    model: str = "meta-llama/Llama-2-7b-hf",
    text_input: str = "",
    max_tokens: int = 20,
    bad_words: str = "",
    stop_words: str = "",
) -> str:
    """Start a prediction.

    Args:
        model (str, default = "meta-llama/Llama-2-7b-hf"): The model on which you want to run a prediction on.
        text_input (str): The prompt on which you want to run a prediction on.
        max_tokens (int, default = 20): The max_tokens in response.
        bad_words (str): A list of bad words (can be empty)
        stop_words (str): A list of stop words (can be empty)

    Returns:
        str: The result of the prediction made by the server
    """
    return Client(fetch_attestation_insecure).predict(text_input, max_tokens, bad_words, stop_words)
