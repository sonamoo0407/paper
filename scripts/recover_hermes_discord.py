"""Recover VMware NAT on Windows and the Hermes Discord gateway on Ubuntu."""

import argparse
import json
import subprocess
import sys
import time


DISCORD_API = "https://discord.com/api/v10/gateway"
HERMES_SERVICE = "hermes-gateway.service"


def recover_windows():
    print("Restarting VMware NAT Service...", flush=True)
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "$ErrorActionPreference = 'Stop'; "
            "Restart-Service -DisplayName 'VMware NAT Service'; "
            "if ((Get-Service -DisplayName 'VMware NAT Service').Status -ne 'Running') "
            "{ throw 'VMware NAT Service is not running' }",
        ],
        check=True,
        timeout=45,
    )
    print("VMware NAT is running. Run this script in Ubuntu to recover Hermes.")


def recover_ubuntu():
    for attempt in range(1, 4):
        print(f"Checking Discord API ({attempt}/3)...", flush=True)
        try:
            response = subprocess.run(
                ["curl", "-fsS", "--max-time", "8", DISCORD_API],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            gateway = json.loads(response.stdout)["url"]
            if not isinstance(gateway, str) or not gateway.startswith("wss://"):
                raise ValueError("Discord API did not return a gateway URL")
            break
        except (subprocess.SubprocessError, ValueError, KeyError, TypeError) as error:
            detail = getattr(error, "stderr", None) or str(error)
            print(f"Discord check failed: {detail.strip()}", file=sys.stderr)
            if attempt == 3:
                print("Check VMware NAT on Windows, then run this script again.", file=sys.stderr)
                for command in (["ip", "route"], ["ip", "neigh"]):
                    subprocess.run(command, check=False, timeout=5)
                return 1
            time.sleep(2)

    subprocess.run(
        ["systemctl", "--user", "restart", HERMES_SERVICE], check=True, timeout=30
    )
    subprocess.run(
        ["systemctl", "--user", "is-active", HERMES_SERVICE], check=True, timeout=5
    )
    print("Discord API is reachable and Hermes is running. Check its status in Discord.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Run in Ubuntu as the Hermes user. If connectivity fails, run in Windows as administrator and retry in Ubuntu.",
    )
    parser.parse_args()
    try:
        if sys.platform == "win32":
            recover_windows()
            return 0
        if sys.platform == "linux":
            return recover_ubuntu()
        parser.error("Run this script on Windows or the Ubuntu VM.")
    except (OSError, subprocess.SubprocessError) as error:
        print(f"Recovery failed: {error}", file=sys.stderr)
        if sys.platform == "win32":
            print("Use an administrator PowerShell window.", file=sys.stderr)
        elif sys.platform == "linux":
            print(
                f"Check logs: journalctl --user -u {HERMES_SERVICE} -n 20 --no-pager",
                file=sys.stderr,
            )
        return 1


if __name__ == "__main__":
    sys.exit(main())
