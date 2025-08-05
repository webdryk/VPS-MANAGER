FROM python:3.9-slim as builder

WORKDIR /app
COPY client/requirements.txt .

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && pip install --user -r requirements.txt

FROM python:3.9-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY client/ .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    netcat-openbsd \ 
    iptables \
    iproute2 \
    net-tools \
    curl \
    dnsutils \
     procps \
    && rm -rf /var/lib/apt/lists/*

# Set up entrypoint
COPY client/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

ENTRYPOINT ["/entrypoint.sh"]