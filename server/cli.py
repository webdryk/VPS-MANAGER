import click
from server import WireGuardServer, OpenVPNServer, ShadowsocksServer, SOCKS5Server

@click.group()
def cli():
    """VPN Server Management CLI"""
    pass

@cli.command()
@click.option('--port', default=51820, help='WireGuard port')
def wireguard(port):
    """Start WireGuard server"""
    with WireGuardServer() as wg:
        click.echo(f"WireGuard server started on port {port}")
        while True:
            pass

@cli.command()
@click.option('--port', default=1194, help='OpenVPN port')
@click.option('--protocol', default='udp', help='Protocol (udp/tcp)')
def openvpn(port, protocol):
    """Start OpenVPN server"""
    with OpenVPNServer(port=port) as ovpn:
        click.echo(f"OpenVPN server started on port {port}/{protocol}")
        while True:
            pass

@cli.command()
@click.option('--port', default=8388, help='Shadowsocks port')
@click.option('--password', prompt=True, hide_input=True, help='Shadowsocks password')
def shadowsocks(port, password):
    """Start Shadowsocks server"""
    with ShadowsocksServer(port=port, password=password) as ss:
        click.echo(f"Shadowsocks server started on port {port}")
        while True:
            pass

if __name__ == '__main__':
    cli()