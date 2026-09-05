// The reading desk: passage state, notes, and the wiring between the page, the note card and the
// agent panel. Everything below the API boundary is unchanged — this file replaces the imperative
// render()/innerHTML page, not the server.
import { React, html, useState, useEffect, useRef, useCallback, Slot, local, ThinkingOrb } from './lib.js';
import { api, apiErrorText, parseRef, passageUrl } from './api.js';
import { makeNotes } from './notes-store.js';
import { createRoot } from '../vendor/react-dom-client.mjs';
import { TopBar, Banner, Verses, SearchPopover, useFootnoteJump } from './reader.js';
import { Sparkle, Trash, Check } from './icons.js';
import { Doodle } from './doodles.js';
import { Detail, SelectionMenu, useSelection } from './notes.js';
import { useChat, Chat } from './chat.js';

function App() {
  const savedPassage = useRef(local.json('passage', null)).current;
  const [pref, setPref] = useState(savedPassage?.ref || '以賽亞書 7:10-17');
  const [pver, setPver] = useState(savedPassage?.version || 'rcuv');
  const [loadLabel, setLoadLabel] = useState('載入');
  const [reference, setReference] = useState('載入中…');
  const [verses, setVerses] = useState([]);
  const [notes, setNotes] = useState([]);
  const [pending, setPending] = useState({});
  const [bannerState, setBannerState] = useState(null);
  const [inter, setInter] = useState({ open: new Set(), cache: {} });
  const [detail, setDetail] = useState(null);
  const [sel, setSel] = useState(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [quickBusy, setQuickBusy] = useState(false);
  const savedPar = useRef(local.get('par', '')).current;
  const [par, setPar] = useState({ on: !!savedPar, version: savedPar || 'auto', map: {}, rtl: false, autoLabel: '原文' });
  const [theme, setTheme] = useState(() => local.get('theme', 'light'));
  const [chatOn, setChatOn] = useState(() => local.get('chat', '0') === '1');

  const lastQ = useRef(null), lastRef = useRef(null), lastAuto = useRef({});
  // Every change to the note list goes through here: the store owns the rule, the request that earns
  // it, and what happens when the request fails. Built once — its verbs are stable identities.
  const storeRef = useRef(null);
  storeRef.current ||= makeNotes({ api, apply: setNotes });
  const store = storeRef.current;
  const versesRef = useRef(verses); versesRef.current = verses;
  const parRef = useRef(par); parRef.current = par;
  const readerRef = useRef(null);
  const seenRev = useRef(null);   // last /api/display rev this page has obeyed
  useFootnoteJump(readerRef);

  // ── banner ──────────────────────────────────────────────────────────────────
  const hideAt = useRef(null);
  const banner = useCallback((text, { spin = true, timer = false, hideAfter = 0, title = '', tone = '' } = {}) => {
    clearTimeout(hideAt.current);                     // a stale hideAfter must not wipe a newer error
    hideAt.current = null;
    setBannerState(text ? { text, spin, timer, title, tone, t0: Date.now() } : null);
    if (text && hideAfter) hideAt.current = setTimeout(() => setBannerState(null), hideAfter);
  }, []);

  // ── chat ────────────────────────────────────────────────────────────────────
  const openChat = useCallback(() => { setChatOn(true); local.set('chat', '1'); }, []);
  const chat = useChat({ openChat, onNote: store.applyServer });
  const chatRef = useRef(chat); chatRef.current = chat;
  const interRef = useRef(inter); interRef.current = inter;   // toggleInter has to read the cache without waiting for a re-render

  // ── passage ─────────────────────────────────────────────────────────────────
  const loadPassage = useCallback(async (refStr, version) => {
    const q = parseRef(refStr);
    if (!q) {
      banner('看不懂的經文位置，例：約翰福音 3:16', { spin: false, tone: 'err', hideAfter: 4000 });
      setLoadLabel('載入');
      return;
    }
    lastQ.current = q;
    banner('載入經文…');
    const r = await api(passageUrl(q, version));
    // a dropped connection used to leave the button on 「載入中…」 and the banner spinning forever
    if (r.error || !r.verses) { banner(apiErrorText(r.error || '伺服器回傳異常'), { spin: false, tone: 'err', hideAfter: 4000, title: r.error || '' }); setLoadLabel('載入'); return; }
    await store.refresh();   // the server keeps them unless the passage changed
    setVerses(r.verses);
    setInter({ open: new Set(), cache: {} });                 // the 原文 blocks belong to the verses we just replaced
    // the server drops the agent session on a passage change
    if (lastRef.current && lastRef.current !== r.reference) chatRef.current.note(`切換到 ${r.reference}，agent 對話重新開始`);
    lastRef.current = r.reference;
    setReference(`${r.reference} · ${r.version}`);
    setLoadLabel('載入');
    if (parRef.current.on) loadSide();                        // not awaited: the 對照 column fills in on its own
    const n = await addAuto('/api/auto-notes/refs');          // instant, from bible-buddy references
    banner(n ? `已驗證 ${n} 條` : null, { spin: false, tone: 'ok', hideAfter: 3000 });
  }, [banner]);

  // returns the number of new notes, or -1 on failure (the error stays on the banner until the next action)
  const addAuto = useCallback(async url => {
    const r = await store.applyPass(url);
    if (r.error) {
      // tone is what picks the icon and the ARIA role; without it a failure renders as a success
      banner(`ELI5 筆記失敗：${apiErrorText(r.error)}`, { spin: false, tone: 'err', title: r.error });   // the pill clips; the full error lives in the tooltip
      return -1;
    }
    lastAuto.current = r;
    return r.added;
  }, [banner]);

  // 對照欄：另一個譯本的同幾節。走 /api/side，不動伺服器的 passage 狀態，也不會重開 agent session
  const loadSide = useCallback(async () => {
    const q = lastQ.current;
    if (!q) return;
    const r = await api(`/api/side?book=${encodeURIComponent(q.book)}&chapter=${q.chapter}&start=${q.start}&end=${q.end}&version=${parRef.current.version}`);
    setPar(p => ({ ...p, map: Object.fromEntries((r.verses || []).map(v => [v.verse, v.text])), rtl: r.code === 'bhs', autoLabel: r.error ? '原文' : `原文（${r.version}）` }));
    if (r.error) banner(`對照譯本載入失敗：${r.error}`, { spin: false, tone: 'err', hideAfter: 4000 });
  }, [banner]);

  // ⇄ 雙欄對照：開關與譯本選擇都記在 localStorage，重新整理回到同一個畫面
  const parallel = useCallback((on, version) => {
    const v = version ?? parRef.current.version;
    local.set('par', on ? v : '');
    setPar(p => ({ ...p, on, version: v }));
    parRef.current = { ...parRef.current, on, version: v };
    if (on) loadSide();
  }, [loadSide]);

  // 原文逐字分析：一節一次（qp.php 整章會失敗），抓回來就留著，之後開合都不再打網路
  const toggleInter = useCallback(async vn => {
    // read the decision off the ref, not out of the updater: React only runs an updater eagerly when
    // the fiber's queue is empty, so a queued update left the fetch silently skipped and the block spinning
    const { open: cur, cache } = interRef.current;
    const willFetch = !cur.has(vn) && !(vn in cache);
    setInter(s => {
      const open = new Set(s.open);
      if (open.has(vn)) open.delete(vn);
      else open.add(vn);
      return { ...s, open };
    });
    if (!willFetch) return;
    const d = await api(`/api/interlinear?book=${encodeURIComponent(lastQ.current.book)}&chapter=${lastQ.current.chapter}&verse=${encodeURIComponent(vn)}`);
    setInter(s => ({ ...s, cache: { ...s.cache, [vn]: d } }));
  }, []);

  const showLex = useCallback(async (w, ot, rect) => {
    setDetail({ mode: 'lex', lex: null, rect, gap: 8 });
    const r = await api(`/api/lexicon?sn=${encodeURIComponent(w.sn)}&ot=${ot ? 1 : 0}`);
    setDetail(d => (d?.mode === 'lex' ? { ...d, lex: r } : d));
  }, []);

  // ── ELI5 notes ──────────────────────────────────────────────────────────────
  const aiNote = useCallback(async s => {
    const id = Math.random().toString(36).slice(2, 8);
    const p = { id, verse: s.verse, quote: s.quote, replace: s.replace, t0: Date.now(), status: '', error: null };
    setPending(cur => ({ ...cur, [id]: p }));
    const key = `one|${s.verse}|${s.quote}`;
    const poll = setInterval(async () => {
      const { status } = await api('/api/auto-notes/quick/status?key=' + encodeURIComponent(key));
      setPending(cur => (cur[id] ? { ...cur, [id]: { ...cur[id], status } } : cur));
    }, 2000);
    const r = await api('/api/auto-notes/one', 'POST', { verse: s.verse, quote: s.quote, replace: s.replace, eli5: true });
    clearInterval(poll);
    if (r.error) {
      setPending(cur => ({ ...cur, [id]: { ...cur[id], error: apiErrorText(r.error, 40), full: r.error } }));
      return;
    }
    setPending(cur => { const { [id]: _, ...rest } = cur; return rest; });
    store.applyOne(r, s.replace);
  }, []);

  // the model pass is manual: it costs money and a minute, and a 529 on page load used to look like "0 notes"
  const runQuick = useCallback(async () => {
    setQuickBusy(true);
    banner('ELI5 筆記產生中', { timer: true });
    // the CLI retries 529s with backoff; poll the server's progress line so the wait explains itself
    const poll = setInterval(async () => {
      const { status } = await api('/api/auto-notes/quick/status');
      if (status) setBannerState(b => (b ? { ...b, text: `ELI5 筆記產生中 · ${status}` } : b));
    }, 2000);
    const n = await addAuto('/api/auto-notes/quick');
    clearInterval(poll);
    setQuickBusy(false);
    // count what the pass returned, not the notes state: setNotes has not re-rendered yet
    if (n >= 0) banner(`ELI5 筆記 ${n} 條${lastAuto.current.cached ? '（快取）' : ''}`, { spin: false, tone: 'ok', hideAfter: 4000 });
  }, [addAuto, banner]);

  // delete every automatic note of the passage (ELI5, agent, references) after a native confirm
  const quickClear = useCallback(async () => {
    const n = notes.filter(x => x.author !== 'user').length;
    if (!confirm(`確定刪除這段全部 ${n} 條自動筆記（ELI5、agent 標注、references）？\n手動筆記會保留。這個動作無法復原。`)) return;
    const r = await store.clearAuto();
    if (r.error) { banner(`刪除失敗：${apiErrorText(r.error)}`, { spin: false, tone: 'err', hideAfter: 4000, title: r.error }); return; }
    banner(`已刪除 ${r.removed} 條自動筆記`, { spin: false, tone: 'ok', hideAfter: 3000 });
  }, [notes, banner]);

  // ── chrome ──────────────────────────────────────────────────────────────────
  useEffect(() => { document.documentElement.dataset.theme = theme; local.set('theme', theme); }, [theme]);
  useEffect(() => { document.getElementById('root').classList.toggle('chat-hidden', !chatOn); }, [chatOn]);
  useSelection(versesRef, setSel, quickBusy);

  const onGutterDown = e => {
    const g = e.currentTarget;
    g.setPointerCapture(e.pointerId);
    g.classList.add('on');
    const move = ev => document.body.style.setProperty('--chat-w', Math.max(280, Math.min(innerWidth * 0.7, innerWidth - ev.clientX)) + 'px');
    g.addEventListener('pointermove', move);
    g.addEventListener('pointerup', () => {
      g.removeEventListener('pointermove', move);
      g.classList.remove('on');
      const w = parseInt(document.body.style.getPropertyValue('--chat-w'));
      if (w) local.set('chatW', w);    // a click that never moved leaves the property unset, and NaN is not a width
    }, { once: true });
    e.preventDefault();
  };

  // double-click the gutter to give the width back. Dropping the inline property hands the column to
  // the stylesheet's own fallback, so the default lives in exactly one place (#root in app.css);
  // 0 is what the loader below already reads as "never set".
  const onGutterReset = () => {
    document.body.style.removeProperty('--chat-w');
    local.set('chatW', 0);
  };

  // A refresh must come back to the same passage, or it would switch the server's passage and drop the
  // running quick pass — unless the CLI asked for something else (a launch argument, or a command sent
  // while no page was open). Asking the server first is what keeps the old passage off the screen.
  useEffect(() => {
    const w = +local.get('chatW', 0);
    if (w) document.body.style.setProperty('--chat-w', w + 'px');
    (async () => {
      const d = await api('/api/display');
      seenRev.current = d?.rev ?? null;
      const ref = d?.ref || savedPassage?.ref || pref;
      const version = (d?.ref ? d.version : savedPassage?.version) || pver;
      if (d?.ref) {
        setPref(ref);
        setPver(version);
        local.set('passage', JSON.stringify({ ref, version }));
      }
      await loadPassage(ref, version);
      chatRef.current.reattach();
    })();
  }, []);

  const submitPassage = () => {
    setLoadLabel('載入中…');
    local.set('passage', JSON.stringify({ ref: pref.trim(), version: pver }));
    loadPassage(pref.trim(), pver);
  };

  // The host agent drives the page: POST /api/display bumps rev, and the next poll loads what it asked for.
  // The boot effect already recorded the rev in force, so this only fires on commands sent since.
  useEffect(() => {
    const t = setInterval(async () => {
      const d = await api('/api/display');
      if (!d?.ref || d.rev === seenRev.current) return;
      seenRev.current = d.rev;
      setPref(d.ref);
      setPver(d.version);
      setLoadLabel('載入中…');
      local.set('passage', JSON.stringify({ ref: d.ref, version: d.version }));   // a refresh stays where it was sent
      loadPassage(d.ref, d.version);
    }, 2000);
    return () => clearInterval(t);
  }, [loadPassage]);

  const hasQuick = notes.some(x => x.author === 'quick');
  const hasAuto = notes.some(x => x.author !== 'user');

  return html`
    <${React.Fragment}>
      <section id="reader" ref=${readerRef}>
        <${TopBar} pref=${pref} setPref=${setPref} pver=${pver} setPver=${setPver}
          loadLabel=${loadLabel} onLoad=${submitPassage}
          par=${par} togglePar=${() => parallel(!par.on)} setParVersion=${v => parallel(true, v)}
          onSearch=${() => setSearchOpen(true)}
          theme=${theme} toggleTheme=${() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))}
          chatOn=${chatOn} toggleChat=${() => { const on = !chatOn; setChatOn(on); local.set('chat', on ? '1' : '0'); }}
          actions=${html`
            <div className="actions">
              <button type="button" id="quick" className=${quickBusy ? 'busy' : ''} disabled=${quickBusy || chat.running}
                      title="一次模型掃整段，寫成淺顯易懂的 ELI5 筆記；產生過的段落直接回傳" onClick=${runQuick}>
                ${quickBusy ? html`<${ThinkingOrb} state="shaping" size=${20} className="orb" />` : html`<${Sparkle} />`}<${Slot} text=${hasQuick ? 'ELI5 筆記' : '生成 ELI5 筆記'} />${hasQuick ? html`<${Check} className="icon done" />` : null}
              </button>
              ${hasAuto ? html`
                <button type="button" id="quickClear" title="刪除這段所有自動筆記（ELI5、agent 標注、references）；手動筆記保留"
                        aria-label="清除自動筆記" onClick=${quickClear}><${Trash} /></button>` : null}
            </div>`} />
        <div id="page" className="page">
          <div className="hrow"><h1 id="ref"><${Slot} text=${reference} /></h1><${Banner} banner=${bannerState} /></div>
          <${Verses} verses=${verses} notes=${notes} pending=${pending} par=${par} inter=${inter}
            handlers=${{
              openNote: (n, rect, gap = 78) => setDetail({ mode: 'card', note: n, rect, gap }),
              toggleInter, showLex,
              retryPending: p => { setPending(cur => { const { [p.id]: _, ...rest } = cur; return rest; }); aiNote(p); },
              dismissPending: p => setPending(cur => { const { [p.id]: _, ...rest } = cur; return rest; }),
            }} />
          ${verses.length
            ? html`<div className="dood foot" aria-hidden="true">
                     <${Doodle} name="star" /><${Doodle} name="star" /><${Doodle} name="star" />
                   </div>`
            : html`<div className="dood blank" aria-hidden="true"><${Doodle} name="sprout" /></div>`}
        </div>
        <${Detail} detail=${detail} setDetail=${setDetail} running=${chat.running}
          verses=${verses} notes=${notes} store=${store}
          send=${chat.send} prefillInput=${chat.prefillInput} aiNote=${aiNote} banner=${banner} />
        <${SearchPopover} open=${searchOpen} onClose=${() => setSearchOpen(false)} version=${pver}
          onPick=${async x => {
            setSearchOpen(false);
            const ref = `${x.book} ${x.chapter}`;
            setPref(ref);
            local.set('passage', JSON.stringify({ ref, version: pver }));
            setLoadLabel('載入中…');
            await loadPassage(ref, pver);
            setTimeout(() => {
              const el = readerRef.current?.querySelector(`.verse[data-verse="${CSS.escape(String(x.verse))}"]`);
              if (!el) return;
              el.scrollIntoView({ block: 'center', behavior: 'smooth' });
              el.classList.add('flash');
              setTimeout(() => el.classList.remove('flash'), 2000);
            }, 0);
          }} />
        <${SelectionMenu} sel=${sel} onClose=${() => setSel(null)}
          onManual=${() => { const s = sel; setSel(null); if (s) setDetail({ mode: 'edit', note: { verse: s.verse, anchor: s.anchor, label: s.quote.slice(0, 20), body: '', kind: 'personal' }, rect: s.rect, gap: 8 }); }}
          onAi=${() => { const s = sel; setSel(null); window.getSelection()?.removeAllRanges(); if (s) aiNote(s); }} />
      </section>
      <${Chat} chat=${chat} theme=${theme} onGutterDown=${onGutterDown} onGutterReset=${onGutterReset} />
    <//>`;
}

createRoot(document.getElementById('root')).render(html`<${App} />`);
