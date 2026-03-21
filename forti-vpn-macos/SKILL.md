---
name: forti-vpn-macos
description: Manage FortiClient SSL VPN connections on macOS via openfortivpn CLI. Supports connect, disconnect, and status check. Trigger when the user says "connect VPN", "VPN connect", "disconnect VPN", "VPN status", "vpn status", "open VPN", "close VPN", "connect to office network", or anything related to VPN connections, FortiClient, or openfortivpn. Even asking "is VPN connected?" should trigger this skill.
---

# FortiClient SSL VPN on macOS (via openfortivpn)

Use `openfortivpn` CLI instead of the FortiClient GUI to manage SSL VPN connections.

## Prerequisites

openfortivpn must be installed. Check first:

```bash
which openfortivpn || echo "NOT_INSTALLED"
```

If not installed, prompt the user to run `brew install openfortivpn`.

## Configuration

VPN settings are stored in `~/.config/openfortivpn/config`. For first-time setup, guide the user to create the config file:

```bash
mkdir -p ~/.config/openfortivpn
```

Config file format:

```
host = <VPN_SERVER_IP>
port = <PORT>
username = <USERNAME>
trusted-cert = <CERT_HASH>
```

The VPN password is provided via the `FORTIVPN_PASSWORD` environment variable, set in `~/.zshrc`:

```bash
export FORTIVPN_PASSWORD="your_password_here"
```

If the user doesn't have a config file yet, ask for their server, port, username, and trusted-cert, then create it for them. If they don't know the trusted-cert, suggest connecting once without it — openfortivpn will display the cert hash on first attempt.

## Commands

### Connect VPN

```bash
sudo openfortivpn -c ~/.config/openfortivpn/config --password="$FORTIVPN_PASSWORD" &
```

Notes:
- `sudo` — requires the user to enter their macOS system password (interactive)
- `--password="$FORTIVPN_PASSWORD"` — VPN account password is supplied automatically from the env var
- `&` — runs in background so the terminal stays usable

**Important**: This command requires interactive sudo password input and cannot be executed by Claude automatically. Prompt the user to run it with the `!` prefix in Claude Code:

> Run: `! sudo openfortivpn -c ~/.config/openfortivpn/config --password="$FORTIVPN_PASSWORD" &`

### Check VPN Status

Use the built-in script (outputs JSON):

```bash
bash "$(dirname -- "${BASH_SOURCE[0]:-$0}")/scripts/vpn-status.sh"
```

Or use a direct command:

```bash
pgrep -x openfortivpn > /dev/null && ifconfig ppp0 2>/dev/null | grep "inet " | awk '{print "VPN_CONNECTED: "$2}' || echo "VPN_DISCONNECTED"
```

### Disconnect VPN

```bash
sudo pkill -x openfortivpn
```

Confirm after disconnecting:

```bash
pgrep -x openfortivpn > /dev/null && echo "STILL_RUNNING" || echo "DISCONNECTED"
```

## Response Format

1. First check current VPN status using the status command
2. Execute the appropriate action based on user intent
3. Report the result concisely

**Status report format**:

```
VPN Status: Connected
IP: 10.x.x.x
Interface: ppp0
```

or

```
VPN Status: Disconnected
```

**Connect**: Since sudo requires interactive password input, tell the user to run the command themselves using the `!` prefix in Claude Code. The VPN password is auto-filled if `FORTIVPN_PASSWORD` is set.

**Disconnect**: Can execute `sudo pkill` directly and report the result.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Gateway certificate validation failed` | First connection, certificate not trusted | Add the cert hash shown by openfortivpn to the config's `trusted-cert` field |
| `Permission denied` | No sudo privileges | Verify the user has admin rights |
| `Could not authenticate` | Wrong credentials | Verify username and password |
| `pppd: The link was terminated` | Connection terminated by gateway | Possible EMS compliance issue — must use the official FortiClient app |
| `host check failed` | FortiGate requires EMS compliance | openfortivpn doesn't support this — must use the official FortiClient app |
