---
name: app-device-fix
description: Sweep a running web app in the browser at several widths, with touch emulation and on throttled 3G; fix what looks broken or feels off with a before and after screenshot for each, and list the rest for review.
disable-model-invocation: true
argument-hint: "[URL or routes, default: the running dev server]"
---

# App Device Fix

Target: `$ARGUMENTS`, or the dev server that is already running when empty, opening its home page and the routes it links to directly. If nothing is running, start the project's dev script. If it still isn't clear what to test, ask.

## Setup

- **Shots dir**: put screenshots in `<session scratchpad>/polish/` (no scratchpad means `mktemp -d`), outside the repo. Every path inside a browser script must be a literal absolute path, because the script inherits neither cwd nor env.
- **Browser**: use ego-browser. Run `ego-browser skill` first and follow its guide. Use one TaskSpace for the whole run.

## Conditions

Each condition below is one **pass**:

| Pass | Width × height | Touch | Network |
|------|----------------|-------|---------|
| phone-s | 320 × 640 | on | fast |
| phone | 375 × 812 | on | fast |
| tablet | 768 × 1024 | on | fast |
| laptop | 1024 × 768 | off | fast |
| desktop | 1440 × 900 | off | fast |
| 3g | 375 × 812 | on | 3G |

"3G" here means a chosen profile of 400 ms latency at 400 kbps both ways, with the cache disabled. It is not a Chrome preset. A dev build is slow on 3G because of its bundle size, so judge the loading states, layout shift, flashes of unstyled content and dead taps while things load. Don't judge the total load time.

Each `ego-browser nodejs` run is a fresh process. Paste this at the top of **every** script, call it before `goto`, and call it again (then `reload`) when you switch passes:

```js
async function emulate(page, { width, height, touch, slow }) {
  await page.cdp("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: touch ? 3 : 1, mobile: touch });
  // maxTouchPoints must be 1-16 even when disabling, so send it only when enabling.
  await page.cdp("Emulation.setTouchEmulationEnabled", touch ? { enabled: true, maxTouchPoints: 5 } : { enabled: false });
  await page.cdp("Emulation.setEmitTouchEventsForMouse", { enabled: touch, configuration: "mobile" });
  await page.cdp("Network.enable");
  await page.cdp("Network.setCacheDisabled", { cacheDisabled: slow });
  await page.cdp("Network.emulateNetworkConditions", slow
    ? { offline: false, latency: 400, downloadThroughput: 51200, uploadThroughput: 51200 }
    : { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
}
```

Give screenshots a `fullPage: true` option, unless the defect is the viewport itself (a sticky header or the keyboard covering an input).

## Steps

1. **Sweep.** Run every pass on every route. Look at each screenshot and interact the way a real user would: tap the menus, open the dialogs, fill the forms and scroll. On every route, run this check:

   ```js
   await page.evaluate(() => {
     // clientWidth, not innerWidth: in mobile emulation innerWidth grows to fit overflowing content.
     const vw = document.documentElement.clientWidth;
     return {
       overflowX: document.documentElement.scrollWidth > vw,
       wide: [...document.querySelectorAll("body *")].filter(e => e.getBoundingClientRect().right > vw + 1).slice(0, 10).map(e => e.tagName + "." + e.className),
       smallTaps: matchMedia("(pointer: coarse)").matches ? [...document.querySelectorAll("a,button,input,select,[role=button]")].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.width < 44 || r.height < 44); }).slice(0, 10).map(e => e.tagName + ":" + (e.textContent || e.name || "").trim().slice(0, 30)) : [],
     };
   })
   ```

   Look for clipped or overlapping text, horizontal scroll, controls that need hover (dead under touch), tap targets under 44 px, inputs hidden by fixed bars, unthrottled-only loading states, layout shift, missing image dimensions, and motion that feels sluggish or janky.

   The step is done when every route × pass cell has been viewed, and every finding has a number, a pass, a route, and a **before** shot named `NN-<slug>-before.png`. Capture every before shot during the sweep, since editing code destroys the before state.

2. **Fix.** Fix the findings one at a time, at the root cause, in the shared component or style rather than with a per-page patch: one commit per finding in a git repo, otherwise note the diff beside the finding. A finding that needs a design call, sits outside the repo, or would take a large refactor moves to **For review**.
   Done when every finding is fixed or moved to For review with its reason.

3. **Recapture.** For each fix, take the **after** shot `NN-<slug>-after.png` under the same pass, route, scroll position and UI state as its before shot. Open both and confirm the defect is gone. Then rerun the evaluate check for that route under every pass, so a fix at one width doesn't break another width. A fix whose after shot still shows the defect, or that breaks another pass, moves back to step 2.
   Done when every fix has an after shot showing the defect gone and a clean evaluate check under every pass.

4. **Finish.** Call `await task.finish({ keep: [] })` once, in the last script.

5. **Report.** Hand off with:
   - **Fixed**: one row per fix, giving the number, the pass and route, what was wrong, what changed (file and symbol), and the before and after paths as full absolute paths.
   - **For review**: each finding left open, worst first, with its before shot and the decision needed.
   - **Skipped**: the routes or states you never reached, such as authenticated pages or empty and error states that need data.

   To attach the shots to a PR, use the before-and-after skill.
