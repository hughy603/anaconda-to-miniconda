#!/usr/bin/env python
"""
Helper script to install packages using UV.

This script ensures that all package installations use UV instead of regular pip,
which helps maintain consistent dependency management in the project.

Usage:
    python scripts/install_package.py package_name [package_name2 ...]
    python scripts/install_package.py -e package_name  # Install in editable mode
    python scripts/install_package.py -r requirements.txt  # Install from requirements file
"""

import argparse
import subprocess
import sys


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Install packages using UV instead of regular pip")
    parser.add_argument("packages", nargs="*", help="Package(s) to install")
    parser.add_argument("-e", "--editable", action="store_true", help="Install in editable mode")
    parser.add_argument("-r", "--requirement", help="Install from requirements file")
    parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    parser.add_argument("--test", action="store_true", help="Install test dependencies")
    parser.add_argument("--docs", action="store_true", help="Install documentation dependencies")
    parser.add_argument("--all", action="store_true", help="Install all optional dependencies")
    return parser.parse_args()


def check_uv_installed():
    """Check if UV is installed."""
    try:
        subprocess.run(
            ["uv", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def install_packages(args):
    """Install packages using UV."""
    if not check_uv_installed():
        print("ERROR: UV is not installed. Please install it with:")
        print("    pipx install uv")
        print("    or")
        print("    pip install uv")
        sys.exit(1)

    # Build the command
    cmd = ["uv", "pip", "install"]

    # Handle editable mode for the current project
    if args.editable and not args.packages and not args.requirement:
        cmd.append("-e")
        extras = []
        if args.dev:
            extras.append("dev")
        if args.test:
            extras.append("test")
        if args.docs:
            extras.append("docs")
        if args.all:
            cmd.append("-e")
            cmd.append(".[all]")
            return cmd

        if extras:
            cmd.append(f".[{','.join(extras)}]")
        else:
            cmd.append(".")
        return cmd

    # Handle editable mode for specific packages
    if args.editable:
        for pkg in args.packages:
            editable_cmd = cmd.copy()
            editable_cmd.extend(["-e", pkg])
            run_install_command(editable_cmd)
        return None

    # Handle requirements file
    if args.requirement:
        cmd.extend(["-r", args.requirement])
        return cmd

    # Handle regular packages
    if args.packages:
        cmd.extend(args.packages)
        return cmd

    # No packages specified
    if not any([args.editable, args.requirement, args.packages]):
        print("ERROR: No packages specified. Use -h for help.")
        sys.exit(1)

    return None


def run_install_command(cmd):
    """Run the install command."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print("Installation completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Installation failed with error code {e.returncode}")
        sys.exit(e.returncode)


def main():
    """Main entry point."""
    args = parse_args()
    cmd = install_packages(args)
    if cmd:
        run_install_command(cmd)


if __name__ == "__main__":
    main()
