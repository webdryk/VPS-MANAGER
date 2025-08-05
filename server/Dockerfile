FROM python:3.9-slim as builder

WORKDIR /app
COPY server/requirements.txt .

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && pip install --user -r requirements.txt

FROM python:3.9-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY server/ .

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    iptables \
    iproute2 \
    wireguard-tools \
    openvpn \
    dnsmasq \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set up entrypoint
COPY server/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

ENTRYPOINT ["/entrypoint.sh"]