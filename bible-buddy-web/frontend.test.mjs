// Pure logic behind the page, run with `node --test` — no browser, no React, no dependencies.
// Everything here was a bug in a module that had no interface a test could reach.
import { test } from 'node:test';
import assert from 'node:assert/strict';

import { readTurn } from './static/src/turn.js';
import { offsetOf, trimSpan } from './static/src/anchor.js';

// ── the turn always ends ──────────────────────────────────────────────────────
// A turn that never reports its end leaves the composer disabled with no way back but a refresh,
// so `end` running exactly once is the whole contract.

const stream = (...frames) => ({
  body: {
    getReader() {
      const enc = new TextEncoder();
      let i = 0;
      return { read: async () => (i < frames.length ? { value: enc.encode(frames[i++]), done: false } : { done: true }) };
    },
  },
});

const ev = o => `data: ${JSON.stringify(o)}\n\n`;

test('a normal turn ends once, as done', async () => {
  const seen = [], ends = [];
  const reason = await readTurn(stream(ev({ type: 'text', text: 'hi' }), ev({ type: 'done', turns: 3 })), {
    text: e => seen.push(e.text), done: () => seen.push('done'), end: r => ends.push(r),
  });
  assert.deepEqual(seen, ['hi', 'done']);
  assert.deepEqual(ends, ['done']);
  assert.equal(reason, 'done');
});

test('a stream that stops before done still ends the turn', async () => {
  const ends = [];
  await readTurn(stream(ev({ type: 'text', text: 'half' })), { end: r => ends.push(r) });
  assert.deepEqual(ends, ['closed']);
});

test('a malformed frame does not lose the turn', async () => {
  const ends = [], seen = [];
  await readTurn(stream('data: {not json\n\n', ev({ type: 'done', turns: 1 })), {
    done: () => seen.push('done'), end: r => ends.push(r),
  });
  assert.deepEqual(seen, ['done'], 'the frames after a bad one still arrive');
  assert.deepEqual(ends, ['done']);
});

test('a dead socket ends the turn instead of wedging it', async () => {
  const ends = [];
  const dead = { body: { getReader: () => ({ read: async () => { throw new Error('network'); } }) } };
  const reason = await readTurn(dead, { end: r => ends.push(r) });
  assert.deepEqual(ends, ['failed']);
  assert.equal(reason, 'failed');
});

test('a response with no body ends the turn instead of throwing at the caller', async () => {
  const ends = [];
  await assert.doesNotReject(() => readTurn({ body: null }, { end: r => ends.push(r) }));
  assert.deepEqual(ends, ['failed']);
});

test('a handler that throws still ends the turn', async () => {
  const ends = [];
  await readTurn(stream(ev({ type: 'note', note: {} })), {
    note: () => { throw new Error('render blew up'); }, end: r => ends.push(r),
  });
  assert.deepEqual(ends, ['failed']);
});

test('keepalive comments are not frames', async () => {
  const seen = [];
  await readTurn(stream(': keepalive\n\n', ev({ type: 'done' })), { done: () => seen.push('done'), end: () => {} });
  assert.deepEqual(seen, ['done']);
});

test('a frame split across two reads is still one frame', async () => {
  const whole = ev({ type: 'text', text: '被split的一節' });
  const seen = [];
  await readTurn(stream(whole.slice(0, 9), whole.slice(9)), { text: e => seen.push(e.text), end: () => {} });
  assert.deepEqual(seen, ['被split的一節']);
});

// ── a selection anchors where the reader dragged ──────────────────────────────
// A verse renders more than its text: the verse number, the 原 button, doodles and footnote
// markers all sit in the same element. Only the nodes carrying verse text count towards an offset.

const nodes = (...texts) => texts.map(data => ({ data }));

test('an offset in the first text node is its own offset', () => {
  const ns = nodes('必有童女懷孕生子');
  assert.equal(offsetOf(ns, ns[0], 2), 2);
});

test('earlier verse-text nodes are counted in', () => {
  // 「必有童女」<sup>1</sup>「懷孕生子」 — the sup is not in the list, so its digit adds nothing
  const ns = nodes('必有童女', '懷孕生子');
  assert.equal(offsetOf(ns, ns[1], 2), 6);
});

test('the second occurrence of a repeated phrase anchors to the second occurrence', () => {
  // this is the bug: v.text.indexOf('神') returns 0 no matter which 神 was dragged
  const text = '神說要有光，神就分開光暗';
  const ns = nodes('神說要有光，', '神就分開光暗');
  const start = offsetOf(ns, ns[1], 0);
  assert.equal(start, 6);
  assert.equal(text.slice(start, start + 1), '神');
  assert.notEqual(start, text.indexOf('神'));
});

test('a node that is not verse text has no offset', () => {
  const ns = nodes('必有童女');
  assert.equal(offsetOf(ns, { data: '10' }, 0), -1);
});

test('a span is trimmed to its non-blank text, in offset space', () => {
  assert.deepEqual(trimSpan('必有 童女 懷孕', 2, 6), [3, 5]);
  assert.deepEqual(trimSpan('必有童女', 0, 4), [0, 4]);
});

test('a span that is all blank trims to nothing', () => {
  const [a, b] = trimSpan('必有   童女', 2, 5);
  assert.equal(a, b);
});

// ── talking to the server ─────────────────────────────────────────────────────
// Every call used to decide for itself what a failure looks like, so the same 529 reached the reader
// in two different wordings and a 500 with an HTML body reached them as a SyntaxError.

const { api, apiErrorText, parseRef } = await import('./static/src/api.js');

const withFetch = async (impl, fn) => {
  const real = globalThis.fetch;
  globalThis.fetch = impl;
  try { return await fn(); } finally { globalThis.fetch = real; }
};

test('a good response comes back parsed', async () => {
  const r = await withFetch(async () => ({ ok: true, status: 200, json: async () => ({ notes: [] }) }),
    () => api('/api/notes'));
  assert.deepEqual(r, { notes: [] });
});

test('a 500 becomes an error message, not a SyntaxError', async () => {
  const r = await withFetch(async () => ({ ok: false, status: 500, json: async () => { throw new SyntaxError('Unexpected token <'); } }),
    () => api('/api/notes'));
  assert.match(r.error, /500/);
});

test('a body that is not JSON becomes an error message', async () => {
  const r = await withFetch(async () => ({ ok: true, status: 200, json: async () => { throw new SyntaxError('Unexpected token <'); } }),
    () => api('/api/notes'));
  assert.ok(r.error, 'an unreadable body is reported, not thrown');
});

test('a dead connection becomes an error message', async () => {
  const r = await withFetch(async () => { throw new TypeError('Failed to fetch'); }, () => api('/api/notes'));
  assert.ok(r.error);
});

test('api never rejects, so no caller has to guard it', async () => {
  await assert.doesNotReject(() => withFetch(async () => { throw new Error('boom'); }, () => api('/x')));
});

test('a 529 reads the same wherever it surfaces', () => {
  const long = 'API Error: 529 Overloaded. This is a server-side error and retrying may help.';
  assert.equal(apiErrorText(long), apiErrorText(long, 40), 'the pill and the banner say the same thing');
  assert.match(apiErrorText(long), /529/);
  assert.ok(!apiErrorText(long).includes('server-side'), 'the sentence is for the tooltip, not the pill');
});

test('another API code still names its number', () => {
  assert.match(apiErrorText('API Error: 500 Internal'), /500/);
});

test('a plain message is clipped, not decoded', () => {
  assert.equal(apiErrorText('經文載入失敗', 60), '經文載入失敗');
  assert.equal(apiErrorText('x'.repeat(80), 40).length, 40);
});

test('nothing at all still says something', () => {
  assert.ok(apiErrorText(undefined).length > 0);
  assert.ok(apiErrorText('').length > 0);
});

// ── what the reader typed ─────────────────────────────────────────────────────
// A reference the parser misreads loads the wrong passage silently, so each shape is pinned.

test('a book, chapter and verse range reads as all four', () => {
  assert.deepEqual(parseRef('以賽亞書 7:10-17'), { book: '以賽亞書', chapter: 7, start: 10, end: 17 });
});

test('a bare chapter is the whole chapter', () => {
  assert.deepEqual(parseRef('創世記 1'), { book: '創世記', chapter: 1, start: 1, end: 200 });
});

test('one verse is a range of itself, not the rest of the chapter', () => {
  assert.deepEqual(parseRef('Matt 5:17'), { book: 'Matt', chapter: 5, start: 17, end: 17 });
});

test('a book on its own is its first chapter', () => {
  assert.deepEqual(parseRef('約翰福音'), { book: '約翰福音', chapter: 1, start: 1, end: 200 });
});

test('a reference that names no book is not a reference', () => {
  assert.equal(parseRef('7:10-17'), null);
});

test('nothing typed is not a reference', () => {
  assert.equal(parseRef(''), null);
  assert.equal(parseRef(null), null);
});

// ── one list of notes, one set of rules, one failure policy ───────────────────
// The rules were tested here on their own while the verb that earns each one, and what happens when
// that verb fails, stayed at six call sites in two files. That is where the bug was: 刪除 in the note
// card dropped the note whether or not the server had agreed, so a failed delete disappeared and came
// back on the next load. These drive the store, not the rules, so the pairing is what is pinned.

const { makeNotes } = await import('./static/src/notes-store.js');

const n = (id, extra = {}) => ({ id, verse: '4', label: id, ...extra });

// A store over a recorded server. `routes` is keyed "METHOD url", or just the url for a GET.
const desk = (list, routes = {}) => {
  const calls = [];
  let cur = list;
  const api = async (url, method = 'GET', body) => {
    calls.push(`${method} ${url}`);
    const r = routes[`${method} ${url}`] ?? routes[url];
    return typeof r === 'function' ? r(body) : r;
  };
  return { ...makeNotes({ api, apply: fn => { cur = fn(cur); } }), calls, list: () => cur };
};

// ── deleting ──────────────────────────────────────────────────────────────────

test('a delete the server never answered keeps the note on screen', async () => {
  // the note is still on the server, so taking it off the screen only hides it until the next load
  const d = desk([n('a'), n('b')], { 'DELETE /api/notes/a': { error: '連線失敗：network' } });
  const r = await d.remove('a');
  assert.match(r.error, /連線失敗/);
  assert.deepEqual(d.list().map(x => x.id), ['a', 'b']);
});

test('a delete the server confirms takes the note off screen', async () => {
  const d = desk([n('a'), n('b')], { 'DELETE /api/notes/a': { ok: true } });
  assert.deepEqual(await d.remove('a'), { ok: true });
  assert.deepEqual(d.list().map(x => x.id), ['b']);
});

test('a note the server no longer has leaves the screen too', async () => {
  // ok:false is "already gone", not "the request failed": keeping it would show a note nobody holds
  const d = desk([n('a')], { 'DELETE /api/notes/a': { ok: false } });
  assert.ok(!(await d.remove('a')).error);
  assert.deepEqual(d.list(), []);
});

test('clearing automatic notes keeps only what the reader wrote', async () => {
  const list = [n('a', { author: 'quick' }), n('b', { author: 'user' }), n('c', { author: 'refs' }), n('d', { author: 'agent' })];
  const d = desk(list, { 'DELETE /api/notes/quick': { ok: true, removed: 3 } });
  assert.deepEqual(await d.clearAuto(), { removed: 3 });
  assert.deepEqual(d.list().map(x => x.id), ['b']);
});

test('a clear the server refused keeps every note', async () => {
  const d = desk([n('a', { author: 'quick' })], { 'DELETE /api/notes/quick': { error: '伺服器錯誤 500' } });
  assert.ok((await d.clearAuto()).error);
  assert.deepEqual(d.list().map(x => x.id), ['a']);
});

// ── saving ────────────────────────────────────────────────────────────────────

test('an edit the server refused keeps the note as it was', async () => {
  const d = desk([n('a', { label: 'old' })], { 'PUT /api/notes/a': { error: 'not found' } });
  assert.equal((await d.save(n('a'), { label: 'new' })).error, 'not found');
  assert.equal(d.list()[0].label, 'old');
});

test('an edit lands in the old note position, as the server returned it', async () => {
  const saved = n('a', { label: 'server said this' });
  const d = desk([n('a'), n('b')], { 'PUT /api/notes/a': saved });
  await d.save(n('a'), { label: 'what the form said' });
  assert.deepEqual(d.list().map(x => x.id), ['a', 'b'], 'order is kept, so the arrow does not jump');
  assert.equal(d.list()[0].label, 'server said this', 'the saved note lands, not the patch');
});

test('a note with no id yet is created and appended', async () => {
  const d = desk([n('a')], { 'POST /api/notes': body => ({ ...body, id: 'fresh' }) });
  await d.save({ verse: '4' }, { label: 'mine' });
  assert.deepEqual(d.list().map(x => x.id), ['a', 'fresh']);
  assert.deepEqual(d.calls, ['POST /api/notes']);
});

test('a save answered with something that is not a note is a failure', async () => {
  const d = desk([n('a')], { 'PUT /api/notes/a': { removed: 1 } });
  assert.ok((await d.save(n('a'), { label: 'x' })).error);
  assert.equal(d.list()[0].label, 'a');
});

// ── automatic passes ──────────────────────────────────────────────────────────

test('a pass adds only what is new', async () => {
  const d = desk([n('a')], { '/api/auto-notes/refs': [n('a', { label: 'stale' }), n('b')] });
  assert.equal((await d.applyPass('/api/auto-notes/refs')).added, 2);
  assert.deepEqual(d.list().map(x => x.id), ['a', 'b']);
  assert.equal(d.list()[0].label, 'a', 'a note already on screen is not overwritten by a cached pass');
});

test('the quick pass wraps its list, and it is still merged', async () => {
  const d = desk([], { '/api/auto-notes/quick': { notes: [n('a')], cost: 0.4, cached: true } });
  assert.deepEqual(await d.applyPass('/api/auto-notes/quick'), { added: 1, cached: true, cost: 0.4 });
  assert.deepEqual(d.list().map(x => x.id), ['a']);
});

test('a pass that failed does not touch the list', async () => {
  const d = desk([n('a')], { '/api/auto-notes/quick': { error: 'API Error: 529 Overloaded' } });
  assert.match((await d.applyPass('/api/auto-notes/quick')).error, /529/);
  assert.deepEqual(d.list().map(x => x.id), ['a']);
});

// ── notes that arrive without being asked for ─────────────────────────────────

test('an agent note replaces its own earlier version in place', () => {
  const d = desk([n('a'), n('b')]);
  d.applyServer(n('a', { label: 'verified' }));
  assert.deepEqual(d.list().map(x => x.id), ['a', 'b']);
  assert.equal(d.list()[0].label, 'verified');
});

test('an agent note the list has not seen is appended', () => {
  const d = desk([n('a')]);
  d.applyServer(n('b'));
  assert.deepEqual(d.list().map(x => x.id), ['a', 'b']);
});

test('a rewritten selection note takes the old one position', () => {
  const d = desk([n('a'), n('b')]);
  d.applyOne(n('c'), 'a');
  assert.deepEqual(d.list().map(x => x.id), ['c', 'b']);
});

test('a selection note with nothing to replace is appended', () => {
  const d = desk([n('a')]);
  d.applyOne(n('c'), undefined);
  assert.deepEqual(d.list().map(x => x.id), ['a', 'c']);
});

// ── switching passage ─────────────────────────────────────────────────────────

test('a refresh replaces the list with what the server holds', async () => {
  const d = desk([n('old')], { '/api/notes': [n('a'), n('b')] });
  assert.deepEqual(await d.refresh(), { count: 2 });
  assert.deepEqual(d.list().map(x => x.id), ['a', 'b']);
});

test('a refresh that failed still clears the previous passage notes', async () => {
  // they belong to verses that are no longer on screen; leaving them would anchor them onto new text
  const d = desk([n('old')], { '/api/notes': { error: '伺服器錯誤 500' } });
  assert.ok((await d.refresh()).error);
  assert.deepEqual(d.list(), []);
});

// ── React only re-renders on a new list ───────────────────────────────────────

test('every change hands back a new list, so React sees it', async () => {
  const start = [n('a', { author: 'quick' })];
  const routes = {
    '/api/notes': [n('z')],
    '/api/auto-notes/refs': [n('b')],
    'PUT /api/notes/a': n('a', { label: 'new' }),
    'DELETE /api/notes/a': { ok: true },
    'DELETE /api/notes/quick': { ok: true, removed: 1 },
  };
  for (const act of [
    d => d.refresh(), d => d.applyPass('/api/auto-notes/refs'), d => d.save(n('a'), {}),
    d => d.remove('a'), d => d.clearAuto(),
    async d => d.applyServer(n('b')), async d => d.applyOne(n('c'), 'a'),
  ]) {
    const d = desk(start, routes);
    await act(d);
    assert.notEqual(d.list(), start);
  }
  assert.deepEqual(start.map(x => x.id), ['a'], 'and none of them mutated the list they were given');
});
