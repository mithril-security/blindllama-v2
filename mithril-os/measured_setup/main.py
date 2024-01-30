import os
import subprocess
import re
import uuid
import hashlib
import shutil

def test_tpm_extend():
    tpm_extend_pcr(15,32*b'\0')

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

def verity_setup_open(device, name, hash_device, root_hash):
    cmd = ["veritysetup", "open", device, name, hash_device, root_hash.hex()]
    subprocess.check_call(cmd)


def verity_setup_close(name):
    cmd = ["veritysetup", "close", name]
    subprocess.check_call(cmd)


def get_partition_uuid(device):
    cmd = ["blkid", device]
    output = subprocess.check_output(cmd).decode()

    # Use a regular expression to extract the UUID
    matches = re.search(r'PARTUUID="([^"]+)"', output)
    if matches:
        return uuid.UUID(matches.group(1))
    else:
        raise ValueError(f"PARTUUID not found for partition {device}")


def mount(source_path, mount_point):
    cmd = ["mount", "-t", "squashfs", "--read-only", source_path, mount_point]
    subprocess.check_call(cmd)


def umount(mount_point):
    cmd = ["umount", mount_point]
    subprocess.check_call(cmd)

PCR_INDEX = 15

def main():
    uuid_app_partition = get_partition_uuid("/dev/disk/by-partlabel/app")
    uuid_app_verity_hash_partition = get_partition_uuid("/dev/disk/by-partlabel/app-verity")
    hash_value = uuid_app_partition.bytes + uuid_app_verity_hash_partition.bytes

    tpm_extend_pcr(PCR_INDEX, hash_value)

    hash_file = open("/root/application_disk_root_hash","w")
    hash_file.write(hash_value.hex())
    hash_file.close()

    verity_setup_open("/dev/disk/by-partlabel/app", "app", "/dev/disk/by-partlabel/app-verity", hash_value)

    os.makedirs("/mnt/app", exist_ok=True)

    mount("/dev/mapper/app", "/mnt/app")

    cmd = ["/mnt/app/setup.d/main"]
    subprocess.check_call(cmd)

    shutil.copytree("/mnt/app/run.d", "/root/run.d")

    umount("/mnt/app")
    verity_setup_close("app")

    SENTINEL_HASH = 32*b'\0'

    tpm_extend_pcr(PCR_INDEX, SENTINEL_HASH)

    subprocess.check_call("/root/run.d/main")



if __name__ == "__main__":
    main()