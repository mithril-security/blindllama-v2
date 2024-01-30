import base64
import json
import subprocess
import tempfile
import time
import os.path
from typing import Dict, List
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

import hashlib

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

PCR_INDEX = 15

def get_caddy_rootca():
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    s.mount("http://", HTTPAdapter(max_retries=retries))
    
    r = s.get("http://localhost:2019/pki/ca/local")
    r.raise_for_status()
    caddy_root_ca = r.json()['root_certificate']
    
    if not caddy_root_ca:
    	raise ValueError("Expected a Caddy root CA, got nothing")
    	
    return caddy_root_ca
    
def tpm_extend_pcr(pcr_index: int, hash: bytes) -> None:
    """
    Extend PCR pcr_index from SHA256 bank with a hash

    >>> hex_hash_value = (
    ...      bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000")
    ... )
    >>> pcr_index = 15
    >>> tpm_extend_pcr(pcr_index, hex_hash_value)
    """
    if not isinstance(hash, bytes):
        raise TypeError("Expected hash to be of type bytes.")
    
    if len(hash) != hashlib.sha256().digest_size:
        raise ValueError(f"Invalid hash length. Expected {hashlib.sha256().digest_size} bytes for a SHA256 hash.")
    
    hex_hash_value = hash.hex()
    subprocess.run(
        ["tpm2_pcrextend", f"{pcr_index}:sha256={hex_hash_value}"], check=True
    )


def get_quote() -> Dict[str, bytes]:
    """
    Produce a quote attesting all the PCRs from the SHA256 PCR bank

    Quote is signed using the AIK_PUB_INDEX key

    """
    AIK_PUB_INDEX = "0x81000003"
    with (
        tempfile.NamedTemporaryFile() as quote_msg_file,
        tempfile.NamedTemporaryFile() as quote_sig_file,
        tempfile.NamedTemporaryFile() as quote_pcr_file,
    ):
        # Note: We only includes PCR 0 to 15 (included). Those PCRs are not resettable and constitutes
        # the SRTM (Static Root of Trust for Measurements)
        # The other index are either part of DRTM(Dynamic Root of Trust for Measurements) and/or resettable which makes them unsuitable 
        # to attest the state of system in case of a latter compromise (because one could reset the PCR and 
        # then extend with the expected measurements to fake the right PCR value).
        # The DRTM is only used if one uses Intel TXT or similar technologies which is not our case.
        #
        # Regarding the PCR16 and above 
        # PCR16 : Usage "Debug", resettable
        # PCR17..22 : Used for DRTM
        # PCR23: Usage "Application Specific", resettable

        # fmt:off
        subprocess.run(["tpm2_quote", "--quiet",
                        "--key-context", AIK_PUB_INDEX, 
                        "--pcr-list", "sha256:0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15", 
                        "--message" , quote_msg_file.name, 
                        "--signature", quote_sig_file.name, 
                        "--pcr", quote_pcr_file.name, 
                        "--hash-algorithm", "sha256"], check=True)
        # fmt:on

        quote_msg = quote_msg_file.read()
        quote_sig = quote_sig_file.read()
        quote_pcr = quote_pcr_file.read()

        quote_msg = base64.b64encode(quote_msg).decode("utf-8")
        quote_sig = base64.b64encode(quote_sig).decode("utf-8")
        quote_pcr = base64.b64encode(quote_pcr).decode("utf-8")

    return {"message": quote_msg, "signature": quote_sig, "pcr": quote_pcr}

def tpm_nvread(offset: str) -> bytes:
    return subprocess.run(
        ["tpm2_nvread", "-Co", offset], capture_output=True, check=True
    ).stdout


def get_cert_chain() -> List[str]:
    root_cert = open("Azure Virtual TPM Root Certificate Authority 2023.crt", "r").read()
    intermediate_cert = open("intermediate_ca.crt", "r").read()
    
    AIK_CERT_INDEX = "0x01C101D0"
    cert_der = tpm_nvread(AIK_CERT_INDEX)
    # Parse the DER certificate
    cert = x509.load_der_x509_certificate(cert_der, default_backend())
    # Convert the certificate to PEM format
    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM).decode("utf-8")

    cert_chain = [cert_pem, intermediate_cert, root_cert]
    return cert_chain


def replay_extend_operations(root_hash):
    # Inital PCR
    pcr_val = 32 * b"\00"
    SENTINEL_HASH = 32 * b"\0"
    hashes = [bytes.fromhex(root_hash), SENTINEL_HASH]
    
    for e in hashes:
        pcr_val = hashlib.sha256(pcr_val + e).digest()

    return pcr_val.hex()


if not os.path.isfile("/srv/attestation.json"):

    root_hash_file = open("/application_disk_root_hash","r")
    root_hash = root_hash_file.read()
    root_hash_file.close()

    caddy_root_ca = get_caddy_rootca()
    hash_caddy_root_ca = hashlib.sha256(caddy_root_ca.encode('utf-8')).digest()

    cert_chain = get_cert_chain()

    # Check that the PCR value is as expected before extending in case of failure of pod and restart between extension of PCR
    # and creation of attestation json file    
    expected_pcr_val = replay_extend_operations(root_hash)

    measured_pcr_val = subprocess.run(["tpm2_pcrread", f"sha256:{PCR_INDEX}"], capture_output=True, check=True, text=True).stdout
 
    #Extract just the PCR hex string
    if measured_pcr_val.split("0x")[1][:-1].lower() == expected_pcr_val :
        tpm_extend_pcr(PCR_INDEX, hash_caddy_root_ca)

    quote = get_quote()

    with open("/srv/attestation.json", 'w') as json_file:
        json.dump({"cert_chain": cert_chain, "quote": quote, "webserver_rootca": caddy_root_ca, "application_disk_roothash": root_hash}, json_file)

while True:
   time.sleep(300)