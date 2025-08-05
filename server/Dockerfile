FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    iptables \
    iproute2 \
    wireguard-tools \
    openvpn \
    dnsmasq \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy entire server directory
COPY server/ .

# Install Python dependencies
RUN pip install -r requirements.txt

# Make sure Python can find our modules
ENV PYTHONPATH=/app

# Entrypoint
COPY server/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]