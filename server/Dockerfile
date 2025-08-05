FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including build tools
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

# Copy requirements first to leverage Docker cache
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY server/ .

# Make sure Python can find our modules
ENV PYTHONPATH=/app

# Entrypoint
COPY server/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]