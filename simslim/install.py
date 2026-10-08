#!/usr/bin/env python3
"""Install or remove the current user's automatic simulator slimming service."""

import argparse
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "uninstall"])
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("This service requires macOS.")

    label = "com.macdevtools.simslim-watch"
    domain = f"gui/{os.getuid()}"
    service = f"{domain}/{label}"
    plist_path = Path.home() / "Library/LaunchAgents" / f"{label}.plist"
    loaded = subprocess.run(["launchctl", "print", service], capture_output=True).returncode == 0

    if args.action == "uninstall":
        if loaded:
            subprocess.run(["launchctl", "bootout", service], check=True)
        plist_path.unlink(missing_ok=True)
        print("Watcher removed. Existing simulator profiles remain applied.")
        return

    binary = shutil.which(os.environ.get("SIMSLIM_BIN", "simslim"))
    if binary is None:
        parser.error("Install SimSlim first, or set SIMSLIM_BIN to its executable.")
    # Keep Homebrew's stable symlink rather than pinning a Cellar version.
    binary = os.path.abspath(binary)
    version_output = subprocess.run(
        [binary, "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    version = re.fullmatch(r"simslim v?(\d+)\.(\d+)\.(\d+)", version_output)
    if version is None or tuple(map(int, version.groups())) < (0, 12, 0):
        parser.error("SimSlim 0.12.0 or newer is required for Apple TV support. Upgrade SimSlim first.")
    print(version_output)
    profile_source = Path(__file__).resolve().parent / "mobile-dev.json"
    # Store runtime files outside the worktree so cleanup cannot break the service.
    config_dir = Path.home() / ".config/simslim"
    log_dir = Path.home() / "Library/Logs/SimSlim"
    for directory in [config_dir, log_dir, plist_path.parent]:
        directory.mkdir(parents=True, exist_ok=True)
    profile = config_dir / "mobile-dev.json"
    profile_data = profile_source.read_bytes()

    plist_data = plistlib.dumps({
        "Label": label,
        "ProgramArguments": [binary, "watch", "--profile", str(profile), "--interval", "3s"],
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 10,
        "EnvironmentVariables": {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
        "StandardOutPath": str(log_dir / "watch.log"),
        "StandardErrorPath": str(log_dir / "watch-error.log"),
    })
    # Only boot out a registered service; surface other launchctl failures.
    if loaded:
        subprocess.run(["launchctl", "bootout", service], check=True)
    profile.write_bytes(profile_data)
    plist_path.write_bytes(plist_data)
    subprocess.run(["plutil", "-lint", str(plist_path)], check=True)
    subprocess.run(["launchctl", "bootstrap", domain, str(plist_path)], check=True)
    subprocess.run(["launchctl", "enable", service], check=True)
    subprocess.run(["launchctl", "kickstart", service], check=True)
    print(f"Automatic simulator slimming enabled. Logs: {log_dir}")


if __name__ == "__main__":
    main()
