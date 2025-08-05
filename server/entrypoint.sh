#!/bin/bash

# Initialize environment
export PYTHONPATH=/app

# Start services
declare -A services=(
    ["wireguard"]=$ENABLE_WIREGUARD
    ["openvpn"]=$ENABLE_OPENVPN
    ["shadowsocks"]=$ENABLE_SHADOWSOCKS
    ["socks5"]=$ENABLE_SOCKS5
    ["doh"]=$ENABLE_DOH
)

cd /app || exit 1

for service in "${!services[@]}"; do
    if [ "${services[$service]}" = "true" ]; then
        echo "Starting $service..."
        python -m "server.${service}_server" &
    fi
done

# Health check
while true; do
    for service in "${!services[@]}"; do
        if [ "${services[$service]}" = "true" ]; then
            if ! pgrep -f "server.${service}_server" >/dev/null; then
                echo "Restarting $service..."
                python -m "server.${service}_server" &
            fi
        fi
    done
    sleep 30
done