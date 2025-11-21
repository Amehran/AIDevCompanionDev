# We MUST use the AL2 base to fix the persistent "unsupported media type" error 
# with cross-compiled ARM64 images in AWS Lambda.
FROM public.ecr.aws/lambda/python:3.9
WORKDIR /var/task

# 1. Install Base Build Tools (Use yum, as this is Amazon Linux 2)
RUN yum update -y && \
    yum install -y \
    gcc gcc-c++ make bzip2-devel libffi-devel openblas-devel wget tar xz-devel \
    sqlite-devel zlib-devel readline-devel findutils patch gzip pkgconfig perl \
    # ldconfig is typically available, but glibc-devel is a safe inclusion for AL2
    glibc-devel && \
    yum clean all

# 2. Install Rust (Required for 'hf-xet')
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# 3. Build OpenSSL 1.1.1w and Prepare Linker
RUN wget --tries=5 --waitretry=5 https://github.com/openssl/openssl/releases/download/OpenSSL_1_1_1w/openssl-1.1.1w.tar.gz && \
    tar xzf openssl-1.1.1w.tar.gz && \
    cd openssl-1.1.1w && \
    ./config --prefix=/usr/local/openssl --openssldir=/usr/local/openssl no-shared && \
    make -j$(nproc) && make install_sw

# 4. Update Linker Cache and Library Path (Using the absolute path for reliability)
RUN /sbin/ldconfig
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# 5. Build and Install Python 3.11 (Consolidated steps)
RUN wget https://www.python.org/ftp/python/3.11.8/Python-3.11.8.tgz && \
    tar xzf Python-3.11.8.tgz && \
    cd Python-3.11.8 && \
    CPPFLAGS="-I/usr/local/openssl/include" LDFLAGS="-L/usr/local/openssl/lib -Wl,-rpath=/usr/local/lib" \
    ./configure --enable-optimizations --enable-shared --with-openssl=/usr/local/openssl && \
    make -j$(nproc) && make install

# 6. Environment Setup and Install Python Build Tools
# This installs tools into the new Python 3.11 environment
RUN ln -sf /usr/local/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/local/bin/pip3.11 /usr/bin/pip3 && \
    python3 -m ensurepip && pip3 install --upgrade pip && \
    pip3 install wheel setuptools meson meson-python cython ninja

# 7. Install Dependencies (Directly into /var/task/python)
RUN pip3 install --no-build-isolation --prefix=/var/task/python "numpy>=1.22.5,<3"
COPY requirements-aws.txt ./
RUN pip3 install --prefix=/var/task/python -r requirements-aws.txt

# 8. Final App Code and Configuration
COPY . .
ENV PYTHONPATH=/var/task/python/lib/python3.11/site-packages

# Set the ENTRYPOINT to the custom compiled Python 3.11 binary
ENTRYPOINT ["/var/task/python/bin/python3.11"]
CMD ["lambda_handler.handler"]