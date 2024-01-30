import base64
import json
from pathlib import Path

from fluorite.attestation.quote import Quote, hazmat_read_quote
from fluorite.attestation.verifier import AttestationDocument


def test_hazmat_read_quote():
    sample_attestation_json = json.loads(
        (Path(__file__).parent / "sample_azure_attestation.json").read_text()
    )
    attestation_doc = AttestationDocument(**sample_attestation_json)
    quote = Quote(**{k: base64.b64decode(v) for k, v in attestation_doc.quote.items()})
    hazmat_read_quote(quote)
