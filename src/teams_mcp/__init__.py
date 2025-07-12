"""Teams MCP Server - Microsoft Teams integration via MCP."""

from .server import TeamsServer
from .config import TeamsConfig

__version__ = "0.1.0"

__all__ = [
    "TeamsServer",
    "TeamsConfig",
]