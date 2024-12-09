# Stage 1: Build
FROM alpine:3.21 AS builder

# Create user and group
RUN adduser -h /code -u 1000 -D -H api

# Set environment variables
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/code/.local/bin:${PATH}"

# Copy only requirements to leverage Docker cache
COPY --chown=api:api /api/requirements.txt /code/requirements.txt

# Install dependencies
RUN apk update --no-cache \
    && apk add --no-cache \
        python3>=3.11 \
        py3-pip>=23 \
        tzdata>=2023 \
    && apk add --no-cache --virtual .build-deps \
        gcc>=13 \
        g++>=13 \
        libc-dev>=0.7 \
        libffi-dev>=3.4 \
        python3-dev>=3.11 \
    && su api -c \
        "pip3 install --break-system-packages --user -U -r /code/requirements.txt" \
    && apk del .build-deps

# Stage 2: Final
FROM alpine:3.21

# Create user and group
RUN adduser -h /code -u 1000 -D -H api

# Set environment variables
ENV PATH="/code/.local/bin:${PATH}"

# Install dependencies
RUN apk update --no-cache \
    && apk add --no-cache \
        python3>=3.11 \
        py3-pip>=23

# Copy the necessary files from the build stage
COPY --chown=api:api --from=builder /code /code

# Copy application code
COPY --chown=api:api /api   /code
COPY --chown=api:api /mongo /code/mongo

# Set working directory
WORKDIR /code

# Set user
USER api

# Entry point
ENTRYPOINT ["/code/main.py"]