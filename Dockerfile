# Multi-stage build for minimal image size
# 多阶段构建以最小化镜像大小

# Stage 1: Build stage
FROM python:3.11-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-alpine

# Install runtime dependencies only
RUN apk add --no-cache \
    openssh-client \
    sshpass \
    && rm -rf /var/cache/apk/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application files
COPY main.py .
COPY plugin_manager.py .
COPY config_loader.py .
COPY logger.py .
COPY lib/ lib/
COPY plugins/ plugins/

# Copy configuration sample (user can mount actual config)
COPY .tiny-disp.conf.sample .

# Create non-root user for security
RUN addgroup -g 1000 tinydisp && \
    adduser -D -u 1000 -G tinydisp tinydisp && \
    chown -R tinydisp:tinydisp /app

# Switch to non-root user
USER tinydisp

# Default command
CMD ["python3", "main.py"]
