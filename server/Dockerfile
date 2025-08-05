FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libxtables-dev \
    iptables \
    iproute2 \
    wireguard-tools \
    openvpn \
    dnsmasq \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy both server and utils packages
COPY server/ ./server/
COPY utils/ ./utils/

# Install Python dependencies
RUN pip install --no-cache-dir -r server/requirements.txt

# Set Python path to include /app
ENV PYTHONPATH=/app

# Entrypoint
COPY server/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]