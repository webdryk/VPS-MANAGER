#!/bin/bash

# Wait for server to be ready (when using compose)
if [ -n "$SERVER_HOST" ]; then
    until nc -z $SERVER_HOST $SERVER_PORT; do
        echo "Waiting for server..."
        sleep 2
    done
fi

# Start the client
exec python -m client.cli connect \
    --server ${SERVER_HOST:-vpn-server} \
    --port ${SERVER_PORT:-51820} \
    --protocol ${PROTOCOL:-auto}