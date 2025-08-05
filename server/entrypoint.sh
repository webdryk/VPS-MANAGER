#!/bin/bash

# Initialize environment
export PYTHONPATH=/app

# Initialize configs if empty
if [ -z "$(ls -A /etc/wireguard)" ]; then
    echo "Initializing WireGuard configuration..."
    python -m server.cli init-wireguard || echo "WireGuard init failed"
fi

if [ -z "$(ls -A /etc/openvpn)" ]; then
    echo "Initializing OpenVPN configuration..."
    python -m server.cli init-openvpn || echo "OpenVPN init failed"
fi

# Install procps if pgrep is missing
if ! command -v pgrep &> /dev/null; then
    apt-get update && apt-get install -y procps
fi

# Start services based on environment variables
declare -A services=(
    ["wireguard"]=$ENABLE_WIREGUARD
    ["openvpn"]=$ENABLE_OPENVPN
    ["shadowsocks"]=$ENABLE_SHADOWSOCKS
    ["socks5"]=$ENABLE_SOCKS5
    ["doh"]=$ENABLE_DOH
)

for service in "${!services[@]}"; do
    if [ "${services[$service]}" = "true" ]; then
        echo "Starting $service..."
        python -m server.cli $service &
    fi
done

# Health check
while true; do
    for service in "${!services[@]}"; do
        if [ "${services[$service]}" = "true" ]; then
            if ! pgrep -f "python -m server.cli $service" >/dev/null; then
                echo "Service $service is down, restarting..."
                python -m server.cli $service &
            fi
        fi
    done
    sleep 30
done