# Use Rocky Linux 8 as the base image
FROM rockylinux:8

# Set the working directory in the container
WORKDIR /EventPlaza

# Install system-level dependencies
RUN dnf update -y && dnf install -y \
    python3 python3-pip python3-devel python3-virtualenv \
    mariadb-devel make automake gcc gcc-c++ kernel-devel \
    git \
    && dnf clean all

# Clone the Git repository into the container
RUN git clone https://github.com/DVMZCS/EventPlaza.git .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt
