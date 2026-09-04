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

// What the reader typed, as the passage endpoint's query — or null if it is not a reference.
// 「以賽亞書 7:10-17」「創世記 1」「Matt 5:17」「約翰福音」(= chapter 1) all parse; a leading digit does
// not, because 「7:10」 alone names no book. A missing end is the single verse; a missing verse is
// the whole chapter (200 is past the end of any of them, and the server clamps).
export function parseRef(refStr) {
  const m = (refStr || '').trim().match(/^(\S+?)\s*(\d+)?(?::(\d+)(?:-(\d+))?)?$/);
  if (!m || /^\d/.test(m[1])) return null;
  return { book: m[1], chapter: +(m[2] || 1), start: +(m[3] || 1), end: +(m[4] || m[3] || 200) };
}

export const passageUrl = (q, version) =>
  `/api/passage?book=${encodeURIComponent(q.book)}&chapter=${q.chapter}&start=${q.start}&end=${q.end}&version=${version || 'rcuv'}`;
