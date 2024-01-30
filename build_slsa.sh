#!/bin/bash

set -e
set -x

ls -al /dev/kvm


df 

lsblk

exit 1
# This command is used to test privilege
#  unshare -m /bin/bash
# Hello World 
# echo "hello world" > output.txt

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install --assume-yes --no-install-recommends \
        cryptsetup libcryptsetup-dev \
        git \
        meson \
        gcc \
        gperf \
        libcap-dev \
        libmount-dev \
        libssl-dev \
        python3-jinja2 \
        pkg-config \
        ca-certificates \
        btrfs-progs \
        bubblewrap \
        debian-archive-keyring \
        dnf \
        e2fsprogs \
        erofs-utils \
        mtools \
        ovmf \
        python3-pefile \
        python3-pyelftools \
        qemu-system-x86 \
        squashfs-tools \
        swtpm \
        systemd-container \
        xfsprogs \
        zypper
        
bash /workspace/update_systemd.sh

apt install --assume-yes --no-install-recommends \
python3-pip python3-venv pipx
pipx install git+https://github.com/systemd/mkosi.git

apt-get install --assume-yes --no-install-recommends dosfstools cpio zstd

cd /workspace
cd /workspace/mkosi/initrd
~/.local/bin/mkosi -f

cd /workspace/mkosi/rootfs
~/.local/bin/mkosi -f