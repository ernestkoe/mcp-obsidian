from . import server
import asyncio

__version__ = "0.6.1"


def main():
    """Main entry point for the package."""
    asyncio.run(server.main())


# Optionally expose other important items at package level
__all__ = ["main", "server"]
