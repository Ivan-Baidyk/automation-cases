FROM quay.io/docling-project/docling-serve-cpu:latest
USER root
RUN dnf install -y --setopt=tsflags=nodocs \
      libreoffice-headless libreoffice-writer libreoffice-calc libreoffice-impress \
      && dnf clean all \
      && rm -rf /var/cache/dnf
USER 1001
