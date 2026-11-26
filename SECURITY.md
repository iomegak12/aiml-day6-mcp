# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | ✅ |

## Important: demo scope

This project is a **teaching demonstration**. By design it:

- runs **without authentication**,
- binds to **all interfaces** (`0.0.0.0`),
- stores data in a local, unencrypted SQLite file.

**Do not expose it to the internet or use it with real or sensitive data.** If you deploy it anywhere beyond your own machine, put authentication (for example, FastMCP auth providers or a reverse proxy) and TLS in front of it, and restrict network access.

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Email **jd.ramkumar@gmail.com** with:

- a description of the issue and its impact,
- steps to reproduce (a proof of concept if possible),
- affected version or commit.

You can expect:

- an acknowledgement within **3 business days**,
- a status update within **10 business days**,
- credit in the changelog once a fix is released, unless you would rather stay anonymous.
