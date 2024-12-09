# Stage 1: Build
FROM alpine:3.21 AS builder

# Create user and group
RUN adduser -h /code -u 1000 -D -H ai

# Set environment variables
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/code/.local/bin:${PATH}"

# Copy only requirements to leverage Docker cache
COPY --chown=ai:ai /ai/requirements.txt /code/requirements.txt

# Install dependencies
RUN apk update --no-cache \
    && apk add --no-cache \
        python3>=3.11 \
        py3-pip>=23 \
    && su ai -c \
        "pip3 install --break-system-packages --user -U -r /code/requirements.txt"

# Stage 2: Final
FROM alpine:3.21

# Create user and group
RUN adduser -h /code -u 1000 -D -H ai

# Set environment variables
ENV PATH="/code/.local/bin:${PATH}"

# Install dependencies
RUN apk update --no-cache \
    && apk add --no-cache \
        python3>=3.11 \
        py3-pip>=23

# Copy the necessary files from the build stage
COPY --chown=ai:ai --from=builder /code /code

# Copy application code
COPY --chown=ai:ai /ai/bestiaire    /code/bestiaire
COPY --chown=ai:ai /ai/utils        /code/utils
COPY --chown=ai:ai /ai/main.py      /code/main.py
COPY --chown=ai:ai /ai/variables.py /code/variables.py
COPY --chown=ai:ai /mongo           /code/mongo

# Set working directory
WORKDIR /code

# Set user
USER ai

# Entry point
ENTRYPOINT ["/code/main.py"]