"""IT Support Ticket MCP Server built with FastMCP."""

import warnings

# Silence third-party deprecation noise (authlib, pulled in by fastmcp) for a clean console.
# authlib installs an "always" filter on import, so import it first and then add ours on top.
try:
    import authlib.deprecate  # noqa: F401
except ImportError:  # pragma: no cover
    pass
warnings.filterwarnings("ignore", message=r".*authlib\.jose module is deprecated.*")
warnings.filterwarnings("ignore", message=r".*httpx module is deprecated.*")

__version__ = "0.1.0"
