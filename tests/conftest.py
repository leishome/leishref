import socket
import subprocess

import pytest

#: External programs that talk to the network.
NETWORK_COMMANDS = ("datasets", "curl")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail any test that reaches the network instead of letting it hang or flake.

    NCBI and Zenodo are mocked where a test needs them (see docs/development.rst); this makes a test
    that forgets to do so fail at once, with the address it tried, rather than depending on connectivity.
    """

    def blocked(self, address, *args, **kwargs):
        if self.family in (socket.AF_INET, socket.AF_INET6):
            raise RuntimeError(f"test tried to open a network connection to {address!r}; mock it")
        return real_connect(self, address, *args, **kwargs)

    real_connect = socket.socket.connect
    monkeypatch.setattr(socket.socket, "connect", blocked)

    real_run = subprocess.run

    def run(cmd, *args, **kwargs):
        if cmd and cmd[0] in NETWORK_COMMANDS:
            raise RuntimeError(f"test tried to run {cmd[0]!r}, which uses the network; mock it")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
