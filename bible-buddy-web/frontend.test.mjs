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

const { api, apiErrorText } = await import('./static/src/api.js');

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
