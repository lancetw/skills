// Shared primitives: the React/htm binding, the CDN globals this page trusts, and the two
// wrappers that let React coexist with libraries that write to the DOM themselves.
import React from '../vendor/react.mjs';
import { html } from '../vendor/htm-react.mjs';
// slot-text is the one dependency still fetched at runtime: it is an ES module, so it cannot carry
// an SRI hash the way the classic scripts in <head> do. Version-pinned only.
import { slotText } from 'https://cdn.jsdelivr.net/npm/slot-text@0.3.4/dist/index.js';
// libraries.dev effects, vendored like React: a canvas thinking indicator and a beam that rides a
// border. Both are peer-dep-only on React, which the <head> import map resolves to our vendored copy.
import { ThinkingOrb } from '../vendor/thinking-orbs.mjs';
import { BorderBeam } from '../vendor/border-beam.mjs';

export { React, html, ThinkingOrb, BorderBeam };
export const {
  useState, useEffect, useLayoutEffect, useRef, useMemo, useCallback, Fragment,
} = React;

// one arrow per ~9 chars and at most 3 per verse, so labels don't pile up; the rest become chips
export const MAX_ARROWS = 3, MIN_GAP = 9;
export const COLOR = { lexical: 'amber', history: 'blue', misread: 'red', crossref: 'purple', personal: 'green' };
export const DOTC = { amber: '#b8751a', blue: '#3b72c4', green: '#2f8f5b', red: '#c45a38', purple: '#8657c8' };
export const KIND_ZH = { lexical: '原文字義', history: '歷史背景', misread: '誤讀/翻譯', crossref: '相關經文', personal: '個人' };
export const AUTHOR = { agent: 'agent', quick: 'AI', refs: 'references', user: '我' };
export const TOOL_ZH = {
  Bash: '執行抓經文腳本', WebSearch: '搜尋', WebFetch: '讀網頁', Read: '讀參考資料', Grep: '查參考資料',
  Glob: '找檔案', Write: '寫檔案', Edit: '修改檔案', Skill: '載入 skill', ToolSearch: '找工具',
  mcp__notes__add_annotation: '加筆記', mcp__notes__update_annotation: '更新筆記',
};

export const api = (url, method, body) =>
  fetch(url, { method, headers: { 'content-type': 'application/json' }, body: body && JSON.stringify(body) }).then(r => r.json());

// Note bodies and agent replies are model text quoting a passage fetched off the internet: markdown,
// never trusted HTML. Everything that reaches innerHTML as markdown goes through here, so a
// <script>/onerror/javascript: smuggled into either is stripped. marked and DOMPurify are the
// SRI-pinned classic scripts in <head>, so they have run before this module does.
export const md = s => DOMPurify.sanitize(marked.parse(String(s)));
export const mdHtml = s => ({ __html: md(s) });

export const elapsed = t0 => {
  const n = Math.round((Date.now() - t0) / 1000);
  return n < 60 ? `${n}s` : `${Math.floor(n / 60)}:${String(n % 60).padStart(2, '0')}`;
};

// localStorage is optional everywhere: a private window or a blocked origin must not break the page.
export const local = {
  get(k, d = null) { try { const v = localStorage.getItem(k); return v === null ? d : v; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch {} },
  json(k, d = null) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
};

// slot-text animates by owning the element's text nodes, so React must never render children into
// the same element: this renders an empty tag and hands it over. `apiRef` exposes the instance for
// the one-off .flash() call.
export function Slot({ text = '', stagger = 20, tag = 'span', apiRef = null, ...rest }) {
  const ref = useRef(null), inst = useRef(null), shown = useRef(String(text));
  useEffect(() => {
    inst.current = slotText(ref.current, shown.current);
    if (apiRef) apiRef.current = inst.current;
    return () => {
      try { inst.current?.destroy?.(); } catch {}
      inst.current = null;
      if (apiRef) apiRef.current = null;
    };
  }, []);
  useEffect(() => {
    const t = String(text);
    if (!inst.current || t === shown.current) return;
    shown.current = t;
    inst.current.set(t, { stagger });
  }, [text]);
  return html`<${tag} ref=${ref} ...${rest} />`;
}

// elapsed seconds since t0, ticking while `on`; frozen at its last value once the job ends
export function useTicker(t0, on = true) {
  const [, bump] = useState(0);
  useEffect(() => {
    if (!on) return;
    const id = setInterval(() => bump(n => n + 1), 1000);
    return () => clearInterval(id);
  }, [on, t0]);
  return t0 ? elapsed(t0) : '';
}
