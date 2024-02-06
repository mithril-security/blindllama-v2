VERSION 0.7

debian-systemd:
    FROM debian:bookworm-slim

    ENV DEBIAN_FRONTEND=noninteractive

    RUN apt-get update
    RUN apt-get install --assume-yes --no-install-recommends \
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
    COPY update_systemd.sh .
    RUN bash update_systemd.sh
    SAVE IMAGE debian-systemd

mithril-os:
    FROM +debian-systemd

    RUN apt install --assume-yes --no-install-recommends \
        python3-pip python3-venv pipx
    RUN pipx install git+https://github.com/systemd/mkosi.git@466851c60166954f5c185497486546d419ceaca3


    RUN  apt-get install --assume-yes --no-install-recommends dosfstools cpio zstd
    WORKDIR /workdir

    COPY mithril-os/render_template ./render_template
    RUN pipx install render_template/

    COPY mithril-os/*.yaml .

    ARG OS_CONFIG="config.yaml"
    
    WORKDIR /workdir/initrd
    CACHE mkosi.cache
    COPY mithril-os/mkosi/initrd .
    RUN /root/.local/bin/render_template "../$OS_CONFIG" mkosi.conf.j2
    
    RUN --privileged /root/.local/bin/mkosi

    SAVE ARTIFACT image AS LOCAL local/initrd_image.cpio.zst
    SAVE ARTIFACT image.manifest AS LOCAL local/initrd.manifest

    # RUN --privileged error

    WORKDIR /workdir/rootfs
    CACHE mkosi.cache

    COPY mithril-os/mkosi/rootfs .
    RUN /root/.local/bin/render_template "../$OS_CONFIG" mkosi.conf.j2
    COPY mithril-os/measured_setup/* mkosi.extra/opt/measured_setup/

    # RUN --privileged error

    RUN --privileged /root/.local/bin/mkosi


    # RUN  --privileged error

    SAVE ARTIFACT image.raw AS LOCAL local/os_disk.raw
    SAVE ARTIFACT image.manifest AS LOCAL local/os_disk.manifest


mithril-os-ci:
    FROM +debian-systemd

    RUN apt install --assume-yes --no-install-recommends \
        python3-pip python3-venv pipx
    RUN pipx install git+https://github.com/systemd/mkosi.git@466851c60166954f5c185497486546d419ceaca3


    RUN  apt-get install --assume-yes --no-install-recommends dosfstools cpio zstd
    WORKDIR /workdir

    COPY mithril-os/render_template ./render_template
    RUN pipx install render_template/

    COPY mithril-os/*.yaml .

    ARG OS_CONFIG="config.yaml"
    
    WORKDIR /workdir/initrd
    CACHE mkosi.cache
    COPY mithril-os/mkosi/initrd .
    RUN /root/.local/bin/render_template "../$OS_CONFIG" mkosi.conf.j2
    
    RUN --privileged /root/.local/bin/mkosi

    SAVE ARTIFACT image AS LOCAL local/initrd_image.cpio.zst
    SAVE ARTIFACT image.manifest AS LOCAL local/initrd.manifest

    # RUN --privileged error

    WORKDIR /workdir/rootfs
    CACHE mkosi.cache

    COPY mithril-os/mkosi/rootfs .
    RUN /root/.local/bin/render_template "../$OS_CONFIG" mkosi.conf.j2
    COPY mithril-os/measured_setup/* mkosi.extra/opt/measured_setup/

    # RUN --privileged error

    RUN --privileged /root/.local/bin/mkosi


    # RUN  --privileged error

    SAVE ARTIFACT image.raw AS LOCAL output/osdisk/os_disk.raw
    SAVE ARTIFACT image.manifest AS LOCAL output/osdisk/os_disk.manifest

attestation-generator-image:
    FROM DOCKERFILE server/attestation_generator
    SAVE IMAGE attestation-generator


k8s-tpm-device-plugin-image:
    FROM DOCKERFILE server/k8s-tpm-device-plugin/
    SAVE IMAGE k8s-tpm-device-plugin

helloworld-appdisk:
    FROM +debian-systemd

    DO github.com/earthly/lib+INSTALL_DIND

    WORKDIR /workdir/disk/container-images

    WITH DOCKER --load attestation-generator:latest=+attestation-generator-image
        RUN docker save -o attestation-generator-image.tar attestation-generator:latest
    END

    WITH DOCKER --pull strm/helloworld-http:latest
        RUN docker tag strm/helloworld-http:latest  helloworld-http:latest && \
            docker save -o app-image.tar helloworld-http:latest
    END

    WITH DOCKER --pull halverneus/static-file-server:latest
        RUN docker tag halverneus/static-file-server:latest attestation-server:latest && \
            docker save -o attestation-server.tar attestation-server:latest
    END
    
    WITH DOCKER --load k8s-tpm-device-plugin:latest=+k8s-tpm-device-plugin-image
        RUN docker save -o k8s-tpm-device-plugin-image.tar k8s-tpm-device-plugin:latest
    END

    WITH DOCKER --pull caddy/ingress:latest
        RUN docker tag caddy/ingress:latest ingress-controller:latest && \
            docker save -o ingress-controller.tar ingress-controller:latest
    END

    WORKDIR /workdir
    COPY application_disk/*.conf .
    COPY application_disk/helloworld-app ./disk


    RUN touch disk.raw

    ENV SOURCE_DATE_EPOCH=0

    # The seed is fixed to produce reproducible disk image
    RUN  systemd-repart \
        --empty=allow \
        --size=auto \
        --dry-run=no \
        --json=pretty \
        --no-pager \
        --offline=yes \
        --seed 71601f80-beac-47c3-80f8-97f8c2ff4fcf \
        --definitions=. \
        disk.raw > application_disk_info.json

    SAVE ARTIFACT application_disk_info.json AS LOCAL local/application_disk_info.json
    SAVE ARTIFACT disk.raw AS LOCAL local/application_disk.raw

blindllamav2-appdisk-without-images:
    FROM +debian-systemd

    RUN apt install --assume-yes --no-install-recommends \
        python3-pip python3-venv pipx moreutils

    WORKDIR /workdir

    COPY application_disk/*.conf .
    COPY application_disk/blindllamav2-app ./disk
    # COPY application_disk/model/ ./disk/model/

    COPY mithril-os/render_template ./render_template
    RUN pipx install render_template/

    COPY application_disk/blindllamav2-app/*.yaml .
    COPY tritonRT/launch_script.sh ./disk
    COPY tritonRT/modify_configpb.sh .
    COPY tensorrtllm_backend/all_models/inflight_batcher_llm/ ./disk/inflight_batcher_llm/
    
    # Copy model engine created by running the launch_container_create_model_engine.sh script (required prerequisite before running earthly build)
    # COPY engines ./disk/engines

    #ARG MODEL_CONFIG="config-codellama.yaml"
    ARG MODEL="Llama-2-7b-hf"
    
    RUN /root/.local/bin/render_template "$MODEL.yaml" ./disk/run.d/deployment.yml.j2
    
    #Sets the pre and post processing configuration and removes safetensor weights to reduce disk size
    #Converted weights are in the engines/1-gpu folder. We don't remove the original model folder because it contains the tokenizer model
    RUN ./modify_configpb.sh $MODEL
    
    COPY tensorrtllm_backend ./disk/tensorrtllm_backend
    COPY tensorrtllm_backend/scripts/launch_triton_server.py ./disk/

    SAVE ARTIFACT ./*


blindllamav2-appdisk:
    FROM +debian-systemd

    RUN apt install --assume-yes --no-install-recommends \
        python3-pip python3-venv pipx

    DO github.com/earthly/lib+INSTALL_DIND

    WORKDIR /workdir/disk/container-images

    WITH DOCKER --load attestation-generator:latest=+attestation-generator-image
        RUN docker save -o attestation-generator-image.tar attestation-generator:latest
    END

    WITH DOCKER --pull halverneus/static-file-server:latest
        RUN docker tag halverneus/static-file-server:latest attestation-server:latest && \
            docker save -o attestation-server.tar attestation-server:latest
    END

    WITH DOCKER --load k8s-tpm-device-plugin:latest=+k8s-tpm-device-plugin-image
        RUN docker save -o k8s-tpm-device-plugin-image.tar k8s-tpm-device-plugin:latest
    END

    WITH DOCKER --pull nvcr.io/nvidia/k8s-device-plugin:v0.14.3
        RUN docker tag nvcr.io/nvidia/k8s-device-plugin:v0.14.3 nvidia-device-plugin:latest && \
            docker save -o nvidia-gpu-device-plugin-image.tar nvidia-device-plugin:latest
    END

    WITH DOCKER --pull caddy/ingress:latest
        RUN docker tag caddy/ingress:latest ingress-controller:latest && \
            docker save -o ingress-controller.tar ingress-controller:latest
    END

    WITH DOCKER --pull nvcr.io/nvidia/tritonserver:23.10-trtllm-python-py3
       RUN docker save -o text-inference-generation.tar nvcr.io/nvidia/tritonserver:23.10-trtllm-python-py3
    END

    WORKDIR /workdir

    COPY application_disk/*.conf .
    COPY application_disk/blindllamav2-app ./disk
    ARG MODEL="gpt2-medium"
    COPY application_disk/model/$MODEL ./disk/model/$MODEL

    COPY mithril-os/render_template ./render_template
    RUN pipx install render_template/

    COPY application_disk/blindllamav2-app/*.yaml .
    COPY tritonRT/launch_script.sh ./disk
    COPY tritonRT/modify_configpb.sh .
    COPY tensorrtllm_backend/all_models/inflight_batcher_llm/ ./disk/inflight_batcher_llm/
    
    # Copy model engine created by running the launch_container_create_model_engine.sh script (required prerequisite before running earthly build)
    COPY engines/$MODEL ./disk/engines/$MODEL
    
    RUN /root/.local/bin/render_template $MODEL.yaml ./disk/run.d/deployment.yml.j2
    RUN ./modify_configpb.sh $MODEL

    # Sets the pre and post processing configuration and removes safetensor weights to reduce disk size
    # Converted weights are in the engines/1-gpu folder. We don't remove the original model folder because it contains the tokenizer model
    RUN chmod +x modify_configpb.sh && ./modify_configpb.sh
    
    COPY tensorrtllm_backend ./disk/tensorrtllm_backend
    COPY tensorrtllm_backend/scripts/launch_triton_server.py ./disk/

    RUN touch disk.raw

    ENV SOURCE_DATE_EPOCH=0

    # The seed is fixed to produce reproducible disk image
    RUN  systemd-repart \
        --empty=allow \
        --size=auto \
        --dry-run=no \
        --json=pretty \
        --no-pager \
        --offline=yes \
        --seed 71601f80-beac-47c3-80f8-97f8c2ff4fcf \
        --definitions=. \
        disk.raw > application_disk_info.json

    SAVE ARTIFACT application_disk_info.json AS LOCAL local/application_disk_info.json
    SAVE ARTIFACT disk.raw AS LOCAL local/application_disk.raw

