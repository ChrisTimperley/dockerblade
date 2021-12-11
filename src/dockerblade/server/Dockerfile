FROM python:3.9-slim-bullseye AS builder
ENTRYPOINT ["/bin/bash"]
WORKDIR /tmp
RUN apt-get update \
 && apt-get install -y binutils \
 && rm -rf /var/lib/apt/lists/*
RUN pip3 install pyinstaller==4.7
COPY server.py .
RUN pyinstaller --name dockerbladed --onefile server.py \
 && pyinstaller dockerbladed.spec \
 && mkdir -p /opt/dockerblade \
 && mv dist/dockerbladed /opt/dockerblade/dockerbladed
