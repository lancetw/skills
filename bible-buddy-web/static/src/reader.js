// The notebook page: title bar, the verses with their arrows / chips / 原文 blocks, translator
// footnotes, the 對照 column, and the whole-Bible search popover.
import {
  html, useRef, useState, useEffect, useLayoutEffect, useMemo, Fragment,
  Slot, MAX_ARROWS, MIN_GAP, COLOR, DOTC, useTicker, ThinkingOrb,
} from './lib.js';
import { Search, Columns, Moon, Sun, Chat, Close, Back, Check, Alert } from './icons.js';
import { Doodle, DOODLES } from './doodles.js';

// ── verse text ────────────────────────────────────────────────────────────────
// A slice of the verse text with its footnote markers dropped in at their offsets
// (the text itself is already clean). Returns React nodes, so the text is never HTML.
function seg(v, a, b, fnNum) {
  const out = [];
  let p = a;
  for (const [i, f] of (v.footnotes || []).entries()) {
    if (f.pos < a || f.pos > b || (f.pos === b && b !== v.text.length)) continue;
    const n = fnNum[`${v.verse}:${i}`];
    out.push(v.text.slice(p, f.pos));
    out.push(html`<sup className="fn" id=${`fnref-${n}`} data-fn=${n} title=${f.text} key=${`f${n}`}>${n}</sup>`);
    p = f.pos;
  }
  out.push(v.text.slice(p, b));
  return out;
}

// Which notes get an arrow and which fall back to a chip. The greedy pass is identical whether or
// not a note was later demoted by measurement, so demoting one can never promote another — that is
// what keeps the measure → re-render → measure loop from oscillating.
function arrange(v, notes, demoted) {
  const anchored = notes.filter(n => n.verse === v.verse && n.anchor).sort((a, b) => a.anchor.start - b.anchor.start);
  const chips = notes.filter(n => n.verse === v.verse && !n.anchor);
  const arrows = [];
  let pos = 0, shown = 0, lastStart = -99;
  for (const n of anchored) {
    if (n.anchor.start < pos || shown >= MAX_ARROWS || n.anchor.start - lastStart < MIN_GAP) { chips.push(n); continue; }
    pos = n.anchor.end; shown++; lastStart = n.anchor.start;
    (demoted.has(n.id) ? chips : arrows).push(n);
  }
  return { arrows, chips };
}

function Chip({ n, onClick }) {
  return html`<span className="chip" data-id=${n.id} style=${{ '--c': DOTC[COLOR[n.kind]] }}
    onClick=${e => onClick(n, e.currentTarget.getBoundingClientRect())}>${n.label}</span>`;
}

// ELI5 單條筆記的狀態列掛在那一節的 chip 列（頁首 pill 留給整段 ELI5）
function PendingChip({ p, onRetry, onDismiss }) {
  const t = useTicker(p.t0, !p.error);
  const q = p.quote.slice(0, 10);
  if (p.error) return html`
    <span className="chip err" title=${p.full || ''}>
      <${Alert} /> 「${q}」${p.error}
      <button onClick=${() => onRetry(p)}>再試</button>
      <button title="關掉" aria-label="關掉" onClick=${() => onDismiss(p)}><${Close} /></button>
    </span>`;
  return html`
    <span className="chip pending">
      <span className="spin"></span>「${q}」${p.replace ? 'ELI5 筆記重新產生中' : 'ELI5 筆記產生中'}
      <span className="st">${p.status ? ` · ${p.status}` : ''}</span>
      <span className="t">${t}</span>
    </span>`;
}

// A Hebrew/Greek fragment inside a Chinese parsing string ("冠詞 הַ + 名詞") drags the neutral " + "
// and the digits after it into its own run, printing them backwards. First-strong isolates pin each
// fragment so only the fragment itself is RTL.
const BIDI = /[\u0590-\u05FF\uFB1D-\uFB4F\u0370-\u03FF\u1F00-\u1FFF]+/g;
const isolate = s => (s || '').replace(/\s+/g, ' ').trim().replace(BIDI, m => `\u2068${m}\u2069`);

// 原文逐字分析：一節一次（qp.php 整章會失敗），抓回來就留著，之後開合都不再打網路
function Interlinear({ data, onWord }) {
  if (!data) return html`<div className="inter"><span className="spin"></span> 原文分析載入中…</div>`;
  if (!data.words?.length) return html`<div className="inter">${data.error || '這一節沒有原文分析資料'}</div>`;
  const dir = data.ot ? 'rtl' : 'ltr';
  return html`
    <div className=${`inter${data.ot ? ' he' : ''}`}>
      ${data.text ? html`<p className="ot" dir=${dir}>${data.text}</p>` : null}
      <div className="ws" dir=${dir}>
        ${data.words.map((x, i) => {
          // Greek splits 詞性 (pro) from the parsing (wform); Hebrew puts both in wform and leaves pro empty
          const gram = [x.pro, x.wform].map(isolate).filter(Boolean).join(' · ');
          return html`
            <button type="button" className="w" key=${i} title=${[x.exp, gram].filter(Boolean).join('\n')}
                    onClick=${e => onWord(x, data.ot, e.currentTarget.getBoundingClientRect())}>
              <b>${x.word}</b>
              <i>${isolate(x.exp)}</i>
              ${gram ? html`<em>${gram}</em>` : null}
            </button>`;
        })}
      </div>
      ${data.literal ? html`<p className="lit" dir="ltr"><span className="lb">直譯</span>${data.literal}</p>` : null}
    </div>`;
}

// ── the page ──────────────────────────────────────────────────────────────────
export function Verses({ verses, notes, pending, par, inter, nudge, handlers }) {
  const box = useRef(null);
  const [win, setWin] = useState(0);                         // bumped on resize: wrapping decides the arrows
  useEffect(() => {
    const on = () => setWin(n => n + 1);
    addEventListener('resize', on);
    return () => removeEventListener('resize', on);
  }, []);

  const fnNum = {}, fnList = [];                             // translator footnotes numbered once across the passage
  let fnN = 0;
  for (const v of verses) for (const [i, f] of (v.footnotes || []).entries()) {
    fnNum[`${v.verse}:${i}`] = ++fnN;
    fnList.push({ n: fnN, verse: v.verse, text: f.text });
  }

  // Labels hang ~70px under their span, so an arrow on any line but the last would cover the next
  // line. The original page fixed that by rewriting the DOM after layout; here the measurement only
  // produces state (which ids lost their arrow, which lean right) and React re-renders from it.
  const key = useMemo(
    () => [win, nudge, par.on, verses.map(v => v.verse).join(), notes.map(n => n.id).join(), [...inter.open].join()].join('|'),
    [win, nudge, par.on, verses, notes, inter.open]);
  const [lay, setLay] = useState({ key: '', dem: [], nw: [] });
  const cur = lay.key === key ? lay : { key, dem: [], nw: [] };
  const demoted = new Set(cur.dem), nwSet = new Set(cur.nw);

  useLayoutEffect(() => {
    if (!box.current) return;
    const dem = new Set(cur.dem), nw = new Set(cur.nw);
    let changed = false;
    for (const vEl of box.current.querySelectorAll('.verse.has-notes')) {
      const eol = vEl.querySelector('.eol');
      if (!eol) continue;
      const lastTop = eol.getBoundingClientRect().top, left = vEl.getBoundingClientRect().left;
      for (const a of vEl.querySelectorAll('.ann')) {
        const r = a.getBoundingClientRect(), id = a.dataset.id;
        if (r.bottom >= lastTop) {                                   // on the last line: keep the arrow
          if (r.left - left < 110 && !nw.has(id)) { nw.add(id); changed = true; }   // near left edge: lean right
          continue;
        }
        if (!dem.has(id)) { dem.add(id); changed = true; }
      }
    }
    if (changed || lay.key !== key) setLay({ key, dem: [...dem], nw: [...nw] });
  });

  // ↩ from a footnote lights its verse briefly: 3 s lit, then a slow fade
  const jumpVerse = n => {
    const el = box.current?.querySelector(`#fnref-${n}`)?.closest('.verse');
    if (!el) return;
    el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    el.classList.add('flash');
    setTimeout(() => el.classList.remove('flash'), 3000);
  };

  return html`
    <div id="verses" ref=${box} className=${par.on ? 'par' : ''}>
      ${verses.map(v => {
        const { arrows, chips } = arrange(v, notes, demoted);
        const pend = Object.values(pending).filter(p => p.verse === v.verse);
        // one doodle per verse, not one per note: the margin holds 32px and a stack of them would
        // read as a legend. First note wins, which is the one nearest the top of the verse.
        const dood = notes.find(n => n.verse === v.verse && DOODLES[n.doodle]);
        const body = [];
        let pos = 0;
        for (const n of arrows) {
          body.push(...seg(v, pos, n.anchor.start, fnNum));
          const lean = n.anchor.start === 0 || nwSet.has(n.id) ? 'ann-nw' : 'ann-n';
          body.push(html`
            <span key=${n.id} className=${`ann ${lean} ann-${COLOR[n.kind] || 'amber'}`} data-note=${n.label} data-id=${n.id}
                  onClick=${e => handlers.openNote(n, e.currentTarget.getBoundingClientRect(), 78)}>
              ${seg(v, n.anchor.start, n.anchor.end, fnNum)}
            </span>`);
          pos = n.anchor.end;
        }
        body.push(...seg(v, pos, v.text.length, fnNum));
        return html`
          <${Fragment} key=${v.verse}>
            <div className=${`verse ${arrows.length ? 'has-notes' : ''}`} data-verse=${v.verse}>
              <span className="n">${v.verse}</span>
              <button type="button" className=${`ob${inter.open.has(v.verse) ? ' on' : ''}`} title="原文逐字分析"
                      onClick=${() => handlers.toggleInter(v.verse)}>原</button>
              ${dood ? html`
                <span className="vdood" title=${dood.label} style=${{ '--c': DOTC[COLOR[dood.kind]] }}>
                  <${Doodle} name=${dood.doodle} />
                </span>` : null}
              ${body}
              <span className="eol">${'​'}</span>
              ${chips.length || pend.length ? html`
                <div className="chips">
                  ${chips.map(n => html`<${Chip} key=${n.id} n=${n} onClick=${handlers.openNote} />`)}
                  ${pend.map(p => html`<${PendingChip} key=${p.id} p=${p} onRetry=${handlers.retryPending} onDismiss=${handlers.dismissPending} />`)}
                </div>` : null}
              ${inter.open.has(v.verse) ? html`<${Interlinear} data=${inter.cache[v.verse]} onWord=${handlers.showLex} />` : null}
            </div>
            ${par.on ? html`<div className="parv" dir=${par.rtl ? 'rtl' : undefined}>${par.map[v.verse] || ''}</div>` : null}
          <//>`;
      })}
      ${fnList.length ? html`
        <section className="fns">
          <h3>譯註</h3>
          <ol>
            ${fnList.map(f => html`
              <li key=${f.n} id=${`fn-${f.n}`}>
                <span className="v">${f.verse}</span>${f.text}
                <a className="back" href=${`#fnref-${f.n}`} title="回到經文"
                   onClick=${e => { e.preventDefault(); jumpVerse(f.n); }} aria-label="回到經文"><${Back} /></a>
              </li>`)}
          </ol>
        </section>` : null}
    </div>`;
}

// A footnote marker jumps to its entry in 譯註. The markers live inside <Verses>, so the click is
// caught here, on the container, rather than wired onto every <sup>.
export function useFootnoteJump(scopeRef) {
  useEffect(() => {
    const el = scopeRef.current;
    if (!el) return;
    const on = e => {
      const fn = e.target.closest?.('.fn');
      if (!fn) return;
      const t = el.querySelector(`#fn-${fn.dataset.fn}`);
      if (!t) return;
      t.scrollIntoView({ block: 'center', behavior: 'smooth' });
      t.classList.add('flash');
      setTimeout(() => t.classList.remove('flash'), 3000);
    };
    el.addEventListener('click', on);
    return () => el.removeEventListener('click', on);
  }, [scopeRef]);
}

// ── title bar ─────────────────────────────────────────────────────────────────
const VERSIONS = [['rcuv', '和合本修訂版'], ['lcc', '呂振中'], ['bhs', 'BHS 希伯來文'], ['fhlwh', 'NT 希臘文']];

export function TopBar({ pref, setPref, pver, setPver, loadLabel, onLoad, par, setParVersion, togglePar, onSearch, theme, toggleTheme, chatOn, toggleChat, actions }) {
  return html`
    <form id="pf" className="top" onSubmit=${e => { e.preventDefault(); onLoad(); }}>
      <${Slot} tag="span" className="brand" text="Bible Buddy ELI5" stagger=${30} />
      <div className="pgrp">
        <input id="pref" value=${pref} onChange=${e => setPref(e.target.value)} />
        <select id="pver" value=${pver} onChange=${e => setPver(e.target.value)}>
          ${VERSIONS.map(([v, n]) => html`<option key=${v} value=${v}>${n}</option>`)}
        </select>
        <button className="primary" id="pload" type="submit"><${Slot} text=${loadLabel} /></button>
      </div>
      ${actions}
      <div className="icons">
        <select id="parver" hidden=${!par.on} title="對照欄用哪個譯本" value=${par.version}
                onChange=${e => setParVersion(e.target.value)}>
          <option value="auto">${par.autoLabel}</option>
          ${VERSIONS.map(([v, n]) => html`<option key=${v} value=${v}>${n}</option>`)}
        </select>
        <button type="button" id="parToggle" className=${par.on ? 'on' : ''} title="雙欄對照：右邊另一個譯本" aria-pressed=${par.on} onClick=${togglePar}><${Columns} /></button>
        <button type="button" id="searchToggle" title="全本經文關鍵字搜尋" onClick=${onSearch}><${Search} /></button>
        <button type="button" id="theme" title="切換深淺色" onClick=${toggleTheme}>${theme === 'dark' ? html`<${Sun} />` : html`<${Moon} />`}</button>
        <button type="button" id="chatToggle" className=${chatOn ? 'on' : ''} title="顯示 / 隱藏 agent 對話" aria-pressed=${chatOn} onClick=${toggleChat}><${Chat} /></button>
      </div>
    </form>`;
}

export function Banner({ banner }) {
  const t = useTicker(banner?.timer ? banner.t0 : 0, !!banner?.timer);
  if (!banner) return html`<div id="banner" hidden></div>`;
  const tone = banner.tone || (banner.spin === false ? 'ok' : 'busy');
  return html`
    <div id="banner" className=${tone} title=${banner.title || ''} role=${tone === 'err' ? 'alert' : 'status'}>
      ${tone === 'busy' ? html`<${ThinkingOrb} state="breathing" size=${20} className="orb" aria-label=${banner.text} />`
        : tone === 'err' ? html`<${Alert} />` : html`<${Check} />`}
      <${Slot} tag="span" id="bannerText" text=${banner.text} stagger=${20} />
      <span className="t">${t}</span>
    </div>`;
}

// ── 全本搜尋 ──────────────────────────────────────────────────────────────────
// hits are FHL text, not markup, so the keyword is highlighted by splitting the string into nodes
function marked_(text, key) {
  if (!key) return text;
  const parts = text.split(key);
  return parts.flatMap((p, i) => (i ? [html`<mark key=${i}>${key}</mark>`, p] : [p]));
}

export function SearchPopover({ open, onClose, onPick, version }) {
  const ref = useRef(null), input = useRef(null);
  const [q, setQ] = useState('');
  const [res, setRes] = useState(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (open) { el.showPopover(); input.current?.focus(); input.current?.select(); }
    else if (el.matches(':popover-open')) el.hidePopover();
  }, [open]);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const on = e => { if (e.newState === 'closed') onClose(); };
    el.addEventListener('toggle', on);
    return () => el.removeEventListener('toggle', on);
  }, [onClose]);

  const search = async e => {
    e.preventDefault();
    const t = q.trim();
    if (!t) return;
    setRes({ loading: true });
    const r = await fetch(`/api/search?q=${encodeURIComponent(t)}&version=${version}`).then(x => x.json()).catch(x => ({ error: x.message }));
    setRes({ ...r, key: t });
  };

  return html`
    <div id="search" popover="auto" ref=${ref}>
      <form id="sf" onSubmit=${search}>
        <input id="sq" ref=${input} value=${q} onChange=${e => setQ(e.target.value)} placeholder="搜尋全本經文，例：虛空" autoComplete="off" />
        <button className="primary" type="submit">搜尋</button>
      </form>
      <div id="sres">
        ${!res ? null
          : res.loading ? html`<p className="hint">搜尋中…</p>`
          : res.error ? html`<p className="hint err"><${Alert} /> ${res.error}</p>`
          : !res.total ? html`<p className="hint">找不到。換個詞，或換一個譯本再搜（原文譯本查不到中文）。</p>`
          : html`
            <p className="hint">${res.total} 筆${res.records.length < res.total ? `，顯示前 ${res.records.length} 筆` : ''}</p>
            ${res.records.map((x, i) => html`
              <button type="button" className="hit" key=${i} onClick=${() => onPick(x)}>
                <b>${x.ref}</b><span>${marked_(x.text, res.key)}</span>
              </button>`)}`}
      </div>
    </div>`;
}
