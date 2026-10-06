"""Offline-profile entrypoint for the UI container: remove every default route, drop root, exec.

Docker cannot publish a host port from an `internal: true` network, so in the closed-network
profile the ui container also joins `ui_edge`, a normal bridge whose default gateway would give
it a route to the internet (Docker Desktop NATs that traffic even with ip-masquerade disabled).
This entrypoint closes that route from inside the container:

1. runs as root with only NET_ADMIN + SETUID + SETGID (compose `cap_drop: [ALL]`),
2. deletes all IPv4 default routes (SIOCDELRT ioctl, stdlib only; no iproute2 in the image),
3. switches to the unprivileged uid/gid, which clears every capability, so the app can never
   re-add a route,
4. execs the real command (Streamlit).

Directly connected subnets keep working: the bridge gateway that delivers published-port traffic
and the internal network that reaches the api. External DNS is cut separately by pointing the
container's embedded-DNS upstream at a dead address (`dns: [127.0.0.1]` in compose).
"""

from __future__ import annotations

import fcntl
import os
import pwd
import socket
import struct
import sys

SIOCDELRT = 0x890C
RTF_UP = 0x0001
RTF_GATEWAY = 0x0002
APP_UID = int(os.getenv("APP_UID", "10001"))
APP_GID = int(os.getenv("APP_GID", "10001"))


def default_routes(route_table: str = "/proc/net/route") -> list[tuple[str, int]]:
    """Return (interface, gateway) for every IPv4 default route (destination and mask 0)."""
    routes = []
    with open(route_table, encoding="ascii") as fh:
        next(fh)  # header
        for line in fh:
            fields = line.split()
            iface, dest, gateway, mask = fields[0], fields[1], fields[2], fields[7]
            if int(dest, 16) == 0 and int(mask, 16) == 0:
                routes.append((iface, int(gateway, 16)))
    return routes


def _sockaddr_in(addr_le: int) -> bytes:
    # struct sockaddr_in: family, port, 4-byte address (kept in /proc byte order), 8 bytes zero
    return struct.pack("<HH", socket.AF_INET, 0) + struct.pack("<I", addr_le) + b"\0" * 8


def rtentry(gateway_le: int) -> bytes:
    """struct rtentry for LP64 Linux (amd64 and arm64) describing `default via <gateway>`."""
    return (
        struct.pack("@L", 0)  # rt_pad1
        + _sockaddr_in(0)  # rt_dst 0.0.0.0
        + _sockaddr_in(gateway_le)  # rt_gateway
        + _sockaddr_in(0)  # rt_genmask 0.0.0.0
        + struct.pack("@Hh", RTF_UP | RTF_GATEWAY, 0)  # rt_flags, rt_pad2
        + b"\0" * 4  # alignment
        + struct.pack("@LP", 0, 0)  # rt_pad3, rt_pad4
        + struct.pack("@h", 0)  # rt_metric
        + b"\0" * 6  # alignment
        + struct.pack("@PLLH", 0, 0, 0, 0)  # rt_dev, rt_mtu, rt_window, rt_irtt
        + b"\0" * 6  # tail padding
    )


def drop_default_routes() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        for iface, gateway in default_routes():
            fcntl.ioctl(sock.fileno(), SIOCDELRT, rtentry(gateway))
            print(f"[no-egress] removed default route via {iface}", file=sys.stderr)
    remaining = default_routes()
    if remaining:
        raise SystemExit(f"[no-egress] default route still present: {remaining}")


def drop_privileges() -> None:
    os.setgroups([])
    os.setgid(APP_GID)
    os.setuid(APP_UID)  # root -> non-root clears permitted/effective capabilities
    try:
        os.environ["HOME"] = pwd.getpwuid(APP_UID).pw_dir
    except KeyError:
        os.environ["HOME"] = "/tmp"


def main(argv: list[str]) -> None:
    if not argv:
        raise SystemExit("usage: no_egress_entrypoint.py <command> [args...]")
    if os.getuid() != 0:
        raise SystemExit("[no-egress] must start as root (user: '0') to remove the default route")
    drop_default_routes()
    drop_privileges()
    os.execvp(argv[0], argv)


if __name__ == "__main__":
    main(sys.argv[1:])
