# Stage 1: Build
FROM alpine:3.21 AS builder

# Create user and group
RUN adduser -h /code -u 1000 -D -H discord

# Set environment variables
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/code/.local/bin:${PATH}"

# Copy only requirements to leverage Docker cache
COPY --chown=discord:discord /discord/requirements.txt /tmp/requirements.txt

# Install dependencies
RUN mkdir /code \
    && chown discord:discord /code \
    && apk update --no-cache \
    && apk add --no-cache \
        python3>=3.11 \
        py3-pip>=23 \
    && apk add --no-cache --virtual .build-deps \
        gcc>=13 \
        libc-dev>=0.7 \
        python3-dev>=3.11 \
    && su discord -c \
        "pip3 install --break-system-packages --user -U -r /tmp/requirements.txt" \
    && apk del .build-deps

# Stage 2: Final
FROM alpine:3.21

# Create user and group
RUN adduser -h /code -u 1000 -D -H discord

# Set environment variables
ENV PATH="/code/.local/bin:${PATH}"

# Install dependencies
RUN apk update --no-cache \
    && apk add --no-cache \
        python3>=3.11 \
        py3-pip>=23

# Copy the necessary files from the build stage
COPY --chown=discord:discord --from=builder /code /code

# Copy application code
COPY --chown=discord:discord /discord   /code
COPY --chown=discord:discord /mongo     /code/mongo

# Set working directory
WORKDIR /code

# Set user
USER discord