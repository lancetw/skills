# First-time setup

Reached from a failed probe in `SKILL.md` step 1. Work through only the section for the tool that failed. Ask the user before installing anything; on their yes, run the install yourself. On a no, give them the same command for their own terminal window and wait.

A terminal window opened before an install keeps its old PATH, so every command the user runs afterwards goes in a window opened after it.

## Tailscale (own devices)

1. Install:
   - Windows: `winget install --id Tailscale.Tailscale -e --accept-source-agreements --accept-package-agreements`, then reload PATH on the same command line before calling it: `$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User"); tailscale version`.
   - macOS: `brew install --cask tailscale-app` (the standalone app, updates itself). `tailscale` missing from the shell afterwards → the user turns on Settings → CLI integration in the app.
2. Log in: the user's own step. Windows: right-click the tray icon → Log in. macOS: open the app and log in. Done when `tailscale status` lists this computer.
3. The phone: the user installs the Tailscale app from App Store / Google Play and logs in with the same account.
4. HTTPS links: the user opens the Tailscale admin console's DNS page (`https://login.tailscale.com/admin/dns`), turns on MagicDNS, and under HTTPS Certificates picks Enable HTTPS. The machine and tailnet names go into public certificate logs, so they should carry nothing sensitive. Done when `tailscale status --json` shows `Self.DNSName` ending in `.ts.net.`.

## cloudflared (client)

No account is needed: a quick tunnel runs without login.

- Windows: `winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements` (reload PATH as above). It does not update itself; an older version is updated with `winget upgrade --id Cloudflare.cloudflared`.
- macOS: `brew install cloudflared`; an older version: `brew upgrade cloudflared`.

Done when `cloudflared --version` prints 2026.9.2 or later.
