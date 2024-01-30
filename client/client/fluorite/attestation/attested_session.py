import tempfile

import requests

from fluorite import attestation
from fluorite.attestation.attestation_retriever import AttestationValidatorProtocol


class AttestedSession(requests.Session):
    """A requests Session with attested TLS."""

    def __init__(
        self,
        attestation_endpoint_base_url: str,
        api_url: str,
        attestation_validator: AttestationValidatorProtocol,
        *,
        fetch_attestation_document_over_insecure_connection: bool = False
    ):
        """Initializes a new AttestedSession instance.

        Perform the remote attestation and establish an attested channel with the web server.

        Args:
            attestation_endpoint_base_url (str): The URL of the attestation endpoint
                from which the server's attestation document is retrieved.
            api_url (str): The URL of the API server to communicate with.
            attestation_validator (AttestationValidatorProtocol): An instance
                of a class that implements the AttestationValidatorProtocol,
                used to validate the remote server's attestation.
            fetch_attestation_document_over_insecure_connection (bool, optional):
                If set to True, allows fetching the attestation document over
                an insecure connection (HTTP). Defaults to False.

        Raises:
            AttestationError: If there is a problem with attestation verification.
            RequestsException: If there is an issue with the network request.
        """
        super().__init__()

        ca_cert = attestation.perform_remote_attestation_and_extract_webserver_ca(
            attestation_endpoint_base_url,
            attestation_validator=attestation_validator,
            fetch_attestation_document_over_insecure_connection=fetch_attestation_document_over_insecure_connection,
        )

        # requests (the HTTP library we use) takes a path to a file containing the CA
        # There is no easy way to provide the CA as a string/bytes directly
        # So we need to create a temporary file with the CA

        # This file must persist during the entire life of the session.
        # so we store it in the session else it might get garbage collected

        self.__server_ca_crt_file = tempfile.NamedTemporaryFile(mode="w+t")
        self.__server_ca_crt_file.write(ca_cert)
        self.__server_ca_crt_file.flush()
        self.verify = self.__server_ca_crt_file.name

        # Check we can reach the service
        self.get(api_url)

    def close(self):
        self.__server_ca_crt_file.close()
        super().close()
