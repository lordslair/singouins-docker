# Stage 1: Build
FROM alpine:3.21 AS builder

# Create user and group
RUN adduser -h /code -u 1000 -D -H ws

# Set environment variables
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/code/.local/bin:${PATH}"

# Copy only requirements to leverage Docker cache
COPY --chown=ws:ws /ws/requirements.txt /code/requirements.txt

# Install dependencies
RUN apk update --no-cache \
    && apk add --no-cache \
        python3>=3.11 \
        py3-pip>=23 \
    && apk add --no-cache --virtual .build-deps \
        gcc>=13 \
        python3-dev>=3.11 \
    && su ws -c \
        "pip3 install --break-system-packages --user -U -r /code/requirements.txt" \
    && apk del .build-deps

# Stage 2: Final
FROM alpine:3.21

# Create user and group
RUN adduser -h /code -u 1000 -D -H ws

# Set environment variables
ENV PATH="/code/.local/bin:${PATH}"

# Install dependencies
RUN apk update --no-cache \
    && apk add --no-cache \
        python3>=3.11 \
        py3-pip>=23

# Copy the necessary files from the build stage
COPY --chown=ws:ws --from=builder /code /code

# Copy application code
COPY --chown=ws:ws /ws/main.py  /code/main.py

# Set working directory
WORKDIR /code

# Set user
USER ws

# Entry point
ENTRYPOINT ["/code/main.py"]