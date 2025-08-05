from setuptools import setup, find_packages

setup(
    name="vpn-tunnel-package",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'cryptography>=3.4',
        'requests>=2.25',
        'dnslib>=0.9',
        'python-iptables>=1.0',
        'psutil>=5.8',
        'backoff>=1.10',
    ],
    entry_points={
        'console_scripts': [
            'vpn-tunnel-server=server.cli:main',
            'vpn-tunnel-client=client.cli:main',
        ],
    },
    python_requires='>=3.7',
    include_package_data=True,
    package_data={
        'server': ['config_templates/*.conf'],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Comprehensive VPN tunneling package with multiple protocols and obfuscation",
    license="MIT",
    keywords="vpn tunnel wireguard shadowsocks openvpn socks5",
    url="https://github.com/yourusername/vpn-tunnel-package",
)