import click
from client import TunnelClient, ProtocolSwitcher

@click.command()
@click.option('--server', required=True, help='Server IP address')
@click.option('--port', default=51820, help='Initial connection port')
@click.option('--protocol', default='auto', help='Protocol to use (wg/ovpn/ss/socks5/auto)')
def connect(server, port, protocol):
    """Connect to VPN server"""
    try:
        with TunnelClient(server_ip=server, server_port=port, protocol=protocol) as client:
            click.echo(f"Connected to {server} using {client.current_protocol}")
            while True:
                pass
    except Exception as e:
        click.echo(f"Connection failed: {e}", err=True)

if __name__ == '__main__':
    connect()