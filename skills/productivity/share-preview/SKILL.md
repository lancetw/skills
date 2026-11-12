---
name: share-preview
description: Hand over a working link to a page served on this computer, checked by the Agent before it is sent — a `*.ts.net` link for the user's own phone and laptop, or a `*.trycloudflare.com` link only listed emails can open, for a client. Use when the user asks for a preview link, to look at a local page on their phone, or to share a page or local server with a client or someone outside the office (「給我預覽」「手機上看」「分享給客戶看」「開到外網」).
license: MIT
---

# Share Preview

`localhost` opens only on the computer running the Agent, so it is never the link you hand over. Who will look decides the link:

| Viewer | Link | Section |
|---|---|---|
| The user, on their own devices | `https://<machine>.<tailnet>.ts.net:<port>`, reachable only inside the user's tailnet | 3 |
| A client, or anyone outside the office | `https://<random>.trycloudflare.com`, opened only by the listed emails after a one-time PIN | 4 |

**Every link is checked before it is sent.** A server left on the same port answers 200 too, so a page that loads proves nothing: the check is that the change you made shows at the very URL you send.

A colleague is neither: they are not on the user's tailnet, so they go through section 4 with their emails.

## 1. Probe

- Section 3: `tailscale status` lists this computer, and `tailscale status --json` has `Self.DNSName` ending in `.ts.net.`.
- Section 4: `cloudflared --version` prints 2026.9.2 or later (the first version with `--allowed-mail`).

Probe the tool for the viewer the request names; a request naming no viewer probes both, so the question in step 2 comes after a passing probe. A failed probe → follow [`references/setup.md`](references/setup.md), then probe again. Done when the probe passes.

## 2. Pick the section

The user named who will look → that decides it. Otherwise ask once: 只有你自己看，還是要給客戶（外部的人）看？

## 3. Own devices: Tailscale Serve

1. Find the local port `PORT` of the server showing the page. No server yet (a plain HTML file or folder) → serve its folder as in section 4 step 2.
2. Pick an unused external port `EXT`: one absent from `tailscale serve status`. When `PORT` is `18xxx`, `EXT` is `PORT − 10000`, so the link tells which server it reaches.
3. `tailscale serve --bg --https=EXT PORT`.
4. Check: `curl -s https://<Self.DNSName without the trailing dot>:EXT/<path>` returns the page with the change you made (a word, a value, a heading the change added). Done when it does.
5. Reply with the link first, then one line: 只有你登入同一個 Tailscale 帳號的裝置打得開；要關就說一聲（`tailscale serve --https=EXT off`）。

## 4. Client: Cloudflare Quick Tunnel with an email list

A quick tunnel serves everything the local server serves, and anyone it lets in can open every path on it. `--allowed-mail` is what keeps the link to the listed people; without it, anyone holding the URL opens the page.

1. **Get the list.** `LIST` is the emails or wildcard domains the user gives (`a@client.com`, `*@client.com`, comma-separated). The user names no one → ask: 要給誰看？請給信箱或 `*@網域`。 Wait for the answer; the tunnel opens only with a list.
2. **Serve only what is shared.** Copy or build the page into a new empty folder `SITE` in the session's temp directory, holding only the files the client should see (no `.git`, `.env`, source, other pages). Output that exists only after a build → build into `SITE`. Pick a free local port `PORT` and serve it in the background, keeping the task ID: `python3 -m http.server PORT --bind 127.0.0.1 --directory SITE` (Windows: `py -m http.server …`).
   The page needs its own running server (API calls, a dev server) → that server is what gets shared: tell the user every route it answers becomes reachable to the listed people, and proceed on their yes.
3. **Check locally.** `curl -s http://127.0.0.1:PORT/` returns the page with the change. Done when it does.
4. **Open the tunnel** in the background, keeping its task ID: `cloudflared tunnel --url http://127.0.0.1:PORT --allowed-mail 'LIST'`. The link is the `https://<random>.trycloudflare.com` line in its output (it appears within about 10 seconds).
5. **Check the gate.** `curl -s -o /dev/null -w '%{http_code} %{redirect_url}' <link>/` answers `302` to `https://login.trycloudflare.com/authorize…`, and following it (`curl -sL`) lands on a page titled `Sign in ・ Cloudflare Access`. A `200` with the page means the list is not in force: stop the tunnel at once and tell the user. `000` with curl exit code 6 (could not resolve host) can last about 80 seconds on a fresh tunnel while public DNS already answers. Retry every 5 seconds for up to 2 minutes before calling it a failure.
6. **Hand over**, in the user's language, the link first:

   ```
   https://<random>.trycloudflare.com
   只有 <LIST> 的信箱打得開：輸入信箱、收一次性 PIN 就能看，不用 Cloudflare 帳號。說「看完了」我就關掉，連結立刻失效。
   ```

   Add only what the user must know to act: the link changes every time the tunnel restarts, so a new list or a restart means sending a new link; the link dies when this computer sleeps or the Agent session ends.
7. **Stop** when the user says done (看完了、關掉): stop the tunnel and the server by the task IDs from steps 2 and 4, then confirm the link is dead: `curl` on it answers `530` or `000`. Done when it does.
