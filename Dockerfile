FROM scratch

ADD mkosi/initrd/image /initrd/image.cpio.zst
ADD mkosi/initrd/image.manifest /initrd/image.manifest

ADD mkosi/rootfs/image /rootfs/image
ADD mkosi/rootfs/image.manifest /rootfs/image.manifest