#!/bin/bash

set -e

# Load config
source upload_config.sh

upload_disk () {
    DISK_SIZE=`qemu-img info  --output json local/$1.raw | jq '."virtual-size"'`
    DISK_SIZE_K=$(((DISK_SIZE + 1023) / 1024))
    DISK_SIZE_M=$(((DISK_SIZE_K + 1023) / 1024))

    qemu-img resize -f raw local/$1.raw "${DISK_SIZE_M}M"
    qemu-img convert -q -f raw -o subformat=fixed,force_size -O vpc local/$1.raw local/$1.img.vhd

    DISK_NAME=$2

    DISK_SIZE=`qemu-img info --output json  local/$1.img.vhd | jq '."virtual-size"'`

    az disk create \
        -g $AZ_RESOURCE_GROUP \
        -n $DISK_NAME \
        -l $AZ_REGION \
        --os-type Linux \
        --upload-type Upload \
        --upload-size-bytes $DISK_SIZE \
        --sku StandardSSD_LRS \
        --security-type TrustedLaunch \
        --hyper-v-generation V2

    URL_ACCESS_SAS=`az disk grant-access -n $DISK_NAME -g $AZ_RESOURCE_GROUP --access-level Write --duration-in-seconds 86400 | jq -r '.accessSas'`
    azcopy copy --blob-type PageBlob "local/$1.img.vhd" "$URL_ACCESS_SAS"
    az disk revoke-access -n $DISK_NAME -g $AZ_RESOURCE_GROUP
}

## Randomised ID to make disk and VM name unique for each run of this script 
ID=`openssl rand -hex 6`

## OS disk upload
OS_DISK_NAME="osdisk-$ID"
upload_disk "os_disk" $OS_DISK_NAME
echo "Uploaded OS disk"
echo "$OS_DISK_NAME"

## Data disk upload
APPLICATION_DISK_NAME="appdisk-$ID"
upload_disk "application_disk" $APPLICATION_DISK_NAME
echo "Uploaded application disk"
echo "$APPLICATION_DISK_NAME"

## Create VM
VM="BlindLlamav2VM-$ID"

az vm create \
    -g $AZ_RESOURCE_GROUP \
    -n $VM \
    --size Standard_NC24ads_A100_v4 \
    --attach-os-disk $OS_DISK_NAME\
    --attach-data-disks $APPLICATION_DISK_NAME \
    --security-type TrustedLaunch \
    --enable-secure-boot false \
    --enable-vtpm true \
    --os-type linux

echo "VM created"
echo "$VM"

az network nsg rule create -g $AZ_RESOURCE_GROUP --nsg-name "$VM"NSG -n "AllowHTTPSInbound" --destination-port-ranges 443 --direction Inbound --access Allow --protocol Tcp --priority 1010

VMpublicIP=`az vm show -d -g $AZ_RESOURCE_GROUP -n $VM --query publicIps -o tsv`
echo "VM's public IP: "
echo $VMpublicIP

./update_hosts_entry.sh $VMpublicIP "api.cloud.localhost"
./update_hosts_entry.sh $VMpublicIP "attestation-endpoint.api.localhost"
