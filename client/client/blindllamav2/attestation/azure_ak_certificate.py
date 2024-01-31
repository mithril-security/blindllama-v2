import pkgutil

from OpenSSL import crypto

from .errors import *

AZURE_VTPM_ROOT_CA_PEM = pkgutil.get_data(
    __package__, "Azure Virtual TPM Root Certificate Authority 2023.crt"
)


def validate_azure_ak_cert(cert_chain: list[str]) -> crypto.X509:
    """Validate the Attestation Key (AK) certificate from an Azure Trusted Launch VM and return the AK certificate if successful.

    The validation is done using the Azure vTPM Root CA that is embedded in the client.
    The CA was obtained from <https://learn.microsoft.com/en-us/azure/virtual-machines/trusted-launch-faq?tabs=cli#certificates>

    Args:
        cert_chain (list[str]): A certificate chain, a list of PEM-encoded certificates provided by the server.
                                The certificates must be ordered from the leaf to the root.

    Returns:
        crypto.X509: The verified AK certificate as an OpenSSL X509 object.

    Raises:
        AttestationError: If the certificate chain is empty or invalid.
    """
    # Verify the certificate's chain with Python's OpenSSL bindings

    if not cert_chain:
        raise AttestationError("Certificate chain is empty")

    # cert_chain[0] is the leaf certificate
    ak_cert = crypto.load_certificate(
        crypto.FILETYPE_PEM, cert_chain[0].encode("ascii")
    )

    # X509Store should only contain trusted CAs, so in our case
    # We want a store with only the Azure vTPM Root CA
    store = crypto.X509Store()

    if not AZURE_VTPM_ROOT_CA_PEM:
        raise AssertionError("Could not get Azure vTPM root CA")

    rootca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, AZURE_VTPM_ROOT_CA_PEM)
    store.add_cert(rootca_cert)

    # Here the chain contains only the intermediate certificates (for Azure there is only one intermediate certificate)
    chain = [
        crypto.load_certificate(crypto.FILETYPE_PEM, cert_pem.encode("ascii"))
        for cert_pem in cert_chain[1:-1]
    ]

    store_ctx = crypto.X509StoreContext(store, ak_cert, chain=chain)

    # If the cert is invalid, it will raise a X509StoreContextError
    try:
        store_ctx.verify_certificate()
    except crypto.X509StoreContextError:
        raise AttestationError("Invalid AK certificate")

    return ak_cert
