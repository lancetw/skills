// Talking to the server. No imports, so the failure shaping is testable without a browser.
//
// Every call goes through here so that a failure looks the same wherever it surfaces. It used to be
// `fetch(...).then(r => r.json())`: a 500 with an HTML error page reached the caller as a
// SyntaxError, a dropped connection as a rejected promise, and each call site invented its own
// wording for both.

// Never rejects. A failure comes back as { error } — the shape every caller already checks for,
// because the server answers that way too.
export async function api(url, method, body) {
  let r;
  try {
    r = await fetch(url, { method, headers: { 'content-type': 'application/json' }, body: body && JSON.stringify(body) });
  } catch (e) {
    return { error: `連線失敗：${e.message}` };
  }
  if (!r.ok) return { error: `伺服器錯誤 ${r.status}` };
  try {
    return await r.json();
  } catch {
    return { error: '伺服器回傳的不是 JSON' };
  }
}

// A model-pass failure arrives as a whole English sentence ("API Error: 529 Overloaded. This is a
// server-side error and retrying may help."). A banner pill or a chip clips it, so give the reader
// the part that tells them what to do and leave the sentence for the tooltip.
export function apiErrorText(msg, max = 60) {
  const s = String(msg ?? '');
  const code = s.match(/API Error: (\d+)/)?.[1];
  if (code === '529') return 'API 529 過載，稍後再試';
  if (code) return `API ${code} 錯誤`;
  return s.slice(0, max) || '伺服器回傳異常';
}
