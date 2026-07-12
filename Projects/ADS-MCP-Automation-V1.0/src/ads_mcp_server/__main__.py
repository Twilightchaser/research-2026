"""Entry point for python -m ads_mcp_server.

Usage:
    python -m ads_mcp_server              # Auto-detect ADS
    python -m ads_mcp_server --ads-path "/path/to/ADS"  # Specify ADS path
"""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="ADS MCP Server for Keysight Advanced Design System")
    parser.add_argument(
        "--ads-path",
        default=None,
        help="Path to the ADS installation root or bundled Python. Auto-detected if omitted.",
    )
    args = parser.parse_args()

    if args.ads_path:
        os.environ["ADS_PATH"] = args.ads_path

    from ads_mcp_server.server import run

    run()


if __name__ == "__main__":
    main()
