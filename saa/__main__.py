"""
SAA CLI Entry Point
Command-line interface for Smart Audio Agent
"""
import asyncio
import sys
from pathlib import Path

from saa.cli.app import cli


def main():
    """Main CLI entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
