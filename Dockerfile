# Use Python 3.12 slim as base image
FROM python:3.12-slim

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Setup timezone and install dependencies
RUN echo 'Etc/UTC' > /etc/timezone \
    && ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime \
    && apt-get update \
    && apt-get -y --no-install-recommends install \
    tzdata build-essential git ca-certificates curl tmux \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
ARG USER_NAME=dev
RUN useradd -m -s /bin/bash ${USER_NAME}

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /usr/local/bin/uv

# Set working directory and switch to non-root user
RUN mkdir -p /home/${USER_NAME}/data-analysis && chown ${USER_NAME}:${USER_NAME} /home/${USER_NAME}/data-analysis
WORKDIR /home/${USER_NAME}/data-analysis
USER ${USER_NAME}

# Install dependencies first (layer caching)
COPY --chown=${USER_NAME}:${USER_NAME} pyproject.toml uv.lock ./
RUN uv sync --no-install-project

# Copy source code
COPY --chown=${USER_NAME}:${USER_NAME} . .
