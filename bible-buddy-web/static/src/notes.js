// The floating card: a note, the note editor, or a Strong's dictionary entry — one native popover,
// dragged by its title row. Also the menu that appears when text in a verse is selected.
import {
  html, useRef, useEffect, useLayoutEffect,
  Slot, mdHtml, AUTHOR, KIND_ZH, DOTC, COLOR, Fragment,
} from './lib.js';
import { api } from './api.js';
import { offsetOf, trimSpan } from './anchor.js';
import { Refresh, BadgeCheck, ArrowRight, Pencil, Sparkle, Alert } from './icons.js';
import { Doodle } from './doodles.js';

// place the card below a rect (labels hang ~70px under a span, so a span rect gets extra room);
// flip above if it would overflow
function place(el, r, gap = 8) {
  if (!el || !r) return;
  let top = r.bottom + gap;
  if (top + el.offsetHeight > innerHeight - 8) top = Math.max(8, r.top - el.offsetHeight - 8);
  el.style.top = top + 'px';
  el.style.left = Math.max(8, Math.min(r.left, innerWidth - el.offsetWidth - 8)) + 'px';
}

// 拖曳：抓標題列（或編輯器的說明列）移動卡片；按鈕和輸入框不當把手
function onDragStart(e) {
  const d = e.currentTarget;
  if (!e.target.closest('.hd, .cap') || e.target.closest('button, input, select, textarea')) return;
  const r = d.getBoundingClientRect(), dx = e.clientX - r.left, dy = e.clientY - r.top;
  const move = ev => {
    d.style.left = Math.max(0, Math.min(ev.clientX - dx, innerWidth - r.width)) + 'px';
    d.style.top = Math.max(0, Math.min(ev.clientY - dy, innerHeight - r.height)) + 'px';
  };
  d.setPointerCapture(e.pointerId);
  d.addEventListener('pointermove', move);
  d.addEventListener('pointerup', () => { d.removeEventListener('pointermove', move); d.releasePointerCapture(e.pointerId); }, { once: true });
  e.preventDefault();
}

function Card({ n, running, actions }) {
  const unverified = n.author === 'quick' && !n.verified;
  const tags = [`第 ${n.verse} 節`, AUTHOR[n.author] || n.author, KIND_ZH[n.kind] || n.kind,
    n.style === 'eli5' && 'ELI5', n.edited && '已編輯', n.verified && 'agent 已驗證'].filter(Boolean);
  const busy = running ? { disabled: true, title: 'agent 忙碌中' } : {};
  return html`
    <${Fragment}>
      <div className="hd">
        <span className="dot" style=${{ '--c': DOTC[COLOR[n.kind]] }}></span>
        <${Slot} tag="b" text=${n.label} stagger=${25} />
        <${Doodle} name=${n.doodle} className="doodle cdood" style=${{ '--c': DOTC[COLOR[n.kind]] }} />
      </div>
      <div className="meta">
        ${tags.map(t => html`<span className="tag" key=${t}>${t}</span>`)}
        ${unverified ? html`<span className="tag unv" title="AI 筆記，未經 bible-buddy 驗證流程">未驗證</span>` : null}
      </div>
      <div className="body" dangerouslySetInnerHTML=${mdHtml((n.body || '（沒有內文）').replace(/\n*（速讀筆記，未經 bible-buddy 驗證流程）$/, ''))}></div>
      <div className="ft">
        <button id="edit" onClick=${actions.edit}>編輯</button>
        <button id="del" className="danger" onClick=${actions.del}>刪除</button>
        ${n.author === 'quick' && n.anchor ? html`<button id="regen" title="用模型重寫這條" onClick=${actions.regen}><${Refresh} />重新產生</button>`
          : n.author === 'agent' ? html`<button id="rewrite" title="請 agent 重新查證並重寫這條" ...${busy} onClick=${actions.rewrite}><${Refresh} />請 agent 重寫</button>`
          : null}
        ${unverified ? html`<button id="verify" ...${busy} onClick=${actions.verify}><${BadgeCheck} />請 agent 驗證</button>` : null}
        <button id="ask" ...${busy} onClick=${actions.ask}>追問<${ArrowRight} /></button>
      </div>
    <//>`;
}

// one editor for new manual notes and for editing any note (auto notes included);
// the anchor never changes here
function Editor({ n, quote, onCancel, onSave }) {
  const f = useRef(null);
  useEffect(() => { f.current?.label?.focus(); }, []);
  const isNew = !n.id;
  return html`
    <form className="ed" ref=${f} onSubmit=${e => {
      e.preventDefault();
      const el = f.current;
      onSave({ label: el.label.value.trim().slice(0, 20), body: el.body.value, kind: el.kind.value });
    }}>
      <div className="cap">${isNew ? '新增筆記' : '編輯筆記'} · 第 ${n.verse} 節${quote ? ` · 「${quote}」` : ''}</div>
      <input name="label" maxLength=${20} placeholder="標籤（≤20 字）" defaultValue=${n.label || ''} required />
      <textarea name="body" placeholder="內文，可用 Markdown" defaultValue=${n.body || ''}></textarea>
      <div className="row">
        <select name="kind" defaultValue=${n.kind || 'personal'}>
          ${Object.keys(KIND_ZH).map(k => html`<option key=${k} value=${k}>${KIND_ZH[k]}</option>`)}
        </select>
        <button type="button" id="cancel" onClick=${onCancel}>取消</button>
        <button className="primary" type="submit">${isNew ? '新增' : '儲存'}</button>
      </div>
    </form>`;
}

// FHL 回的是純文字（音譯、欽定本次數、字義樹），不是 markdown，所以只放進 <pre>，不 render
function Lexicon({ lex }) {
  if (!lex) return html`<div className="lex"><span className="spin"></span> 查字典…</div>`;
  if (lex.error) return html`<p className="lex err"><${Alert} /> ${lex.error}</p>`;
  return html`
    <${Fragment}>
      <div className="hd"><b>${lex.orig}</b></div>
      <div className="meta"><span className="tag">Strong's ${lex.sn}</span></div>
      <pre className="lex">${lex.text || '（字典沒有這個編號）'}</pre>
    <//>`;
}

export function Detail({ detail, setDetail, running, verses, notes, setNotes, send, prefillInput, aiNote, banner }) {
  const ref = useRef(null);
  const quoteOf = n => (n?.anchor ? verses.find(v => v.verse === n.verse)?.text.slice(n.anchor.start, n.anchor.end) ?? '' : '');

  // light dismiss and Esc close the popover without going through setDetail
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const on = e => { if (e.newState === 'closed') setDetail(null); };
    el.addEventListener('toggle', on);
    return () => el.removeEventListener('toggle', on);
  }, [setDetail]);
  // Show and place in one layout pass, in that order: a closed popover is display:none, so measuring it
  // first reports 0px tall and the card is never flipped above — it just hangs off the bottom of the window.
  // Runs after every content change too, since the card's height decides which side it hangs on.
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (detail && !el.matches(':popover-open')) el.showPopover();
    else if (!detail && el.matches(':popover-open')) el.hidePopover();
    if (detail) place(el, detail.rect, detail.gap);
  });

  let inner = null;
  if (detail?.mode === 'lex') inner = html`<${Lexicon} lex=${detail.lex} />`;
  else if (detail?.mode === 'edit') {
    const n = detail.note;
    inner = html`<${Editor} n=${n} quote=${quoteOf(n)}
      onCancel=${() => (n.id ? setDetail({ ...detail, mode: 'card' }) : setDetail(null))}
      onSave=${async patch => {
        const saved = n.id ? await api('/api/notes/' + n.id, 'PUT', patch) : await api('/api/notes', 'POST', { ...n, ...patch });
        if (saved.error) { banner(saved.error, { spin: false, tone: 'err', hideAfter: 4000 }); return; }
        setNotes(cur => (n.id ? cur.map(x => (x.id === n.id ? { ...x, ...saved } : x)) : [...cur, saved]));
        setDetail(null);
      }} />`;
  } else if (detail?.mode === 'card') {
    const n = notes.find(x => x.id === detail.note.id) || detail.note;
    inner = html`<${Card} n=${n} running=${running} actions=${{
      edit: () => setDetail({ ...detail, mode: 'edit', note: n }),
      del: async () => {
        if (!confirm(`確定刪除這條筆記「${n.label}」？無法復原。`)) return;
        await api('/api/notes/' + n.id, 'DELETE');
        setNotes(cur => cur.filter(x => x.id !== n.id));
        setDetail(null);
      },
      ask: () => { setDetail(null); prefillInput(`針對「${n.label}」追問：`); },
      regen: () => { setDetail(null); aiNote({ verse: n.verse, quote: quoteOf(n), replace: n.id }); },
      rewrite: () => {
        setDetail(null);
        send(`重寫筆記 ${n.id}（第 ${n.verse} 節「${quoteOf(n)}」）：\nlabel：${n.label}\nbody：${n.body}\n請依 bible-buddy 流程重新查證這個點，修正錯誤或換更精確、更有價值的角度，然後呼叫 mcp__notes__update_annotation（id=${n.id}）回填：label 20 字內；body 1 到 3 句、100 字內，口氣與格式跟原筆記一樣${n.style === 'eli5' ? '（ELI5 淺白）' : ''}。詳細分析寫在對話裡即可，不要另外新增筆記。`);
      },
      // hand the quick note to the agent; it answers by calling update_annotation, which comes back as a "note" event
      verify: () => {
        setDetail(null);
        send(`驗證 AI 筆記 ${n.id}（第 ${n.verse} 節「${quoteOf(n)}」）：${n.style === 'eli5' ? '（這條是 ELI5 淺白風格，回填也要同樣淺白）' : ''}\nlabel：${n.label}\nbody：${n.body}\n請依 bible-buddy 流程查證原文字義、歷史背景與資料來源，有誤就改正。完成後呼叫 mcp__notes__update_annotation（id=${n.id}）回填。回填的口氣與格式要跟原筆記一樣：label 20 字內，原文字義類寫「希伯來/希臘字 音譯＝意思」；body 1 到 3 句、100 字內，直接陳述結論與主要依據，像原本那條筆記的寫法，不要寫「經查證」「已驗證」「原筆記正確」這類過程描述，不要教會式應用。詳細分析寫在對話裡即可，不要塞進筆記，也不要另外新增筆記。`);
      },
    }} />`;
  }

  return html`<div id="detail" popover="auto" ref=${ref} onPointerDown=${onDragStart}>${inner}</div>`;
}

// 反白一節內的文字 → 選單：手動筆記（自己寫）或 ELI5 筆記（模型針對這幾個字寫一條淺白的）
export function SelectionMenu({ sel, onClose, onManual, onAi }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (sel) {
      el.showPopover();
      let top = sel.rect.bottom + 6;   // below the selection; above only when it would run off the bottom
      if (top + el.offsetHeight > innerHeight - 8) top = Math.max(8, sel.rect.top - el.offsetHeight - 6);
      el.style.top = top + 'px';
      el.style.left = Math.max(8, Math.min(sel.rect.left, innerWidth - el.offsetWidth - 8)) + 'px';
    } else if (el.matches(':popover-open')) el.hidePopover();
  }, [sel]);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const on = e => { if (e.newState === 'closed') onClose(); };
    el.addEventListener('toggle', on);
    return () => el.removeEventListener('toggle', on);
  }, [onClose]);
  return html`
    <div id="selmenu" popover="auto" ref=${ref}>
      <button type="button" id="selManual" onClick=${onManual}><${Pencil} />手動筆記</button>
      <button type="button" id="selAi" title="用模型針對這幾個字寫一條淺顯易懂的筆記" onClick=${onAi}><${Sparkle} />ELI5 筆記</button>
    </div>`;
}

// captured at mouseup: the click on the menu clears the browser selection before its handler runs
// A verse renders more than its text. Everything matched here sits inside .verse but is not part of
// the verse, so its characters must not shift a selection's offset.
const NOT_VERSE_TEXT = '.n, .ob, .mg, .vdood, .fn, .eol, .chips, .inter';

// The verse's own text nodes, in reading order. `.ann` spans wrap verse text, so they are kept.
function verseTextNodes(vEl) {
  const w = document.createTreeWalker(vEl, NodeFilter.SHOW_TEXT, {
    acceptNode: t => (t.parentElement?.closest(NOT_VERSE_TEXT) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
  });
  const out = [];
  for (let t; (t = w.nextNode());) out.push(t);
  return out;
}

export function useSelection(versesRef, setSel, off) {
  useEffect(() => {
    // the quick pass rewrites the whole passage's notes: a selection menu opened mid-pass would
    // anchor a note onto a list that is about to be replaced, so close it and stop listening
    if (off) { setSel(null); return; }
    const on = e => {
      if (e.target.closest?.('#selmenu, #detail')) return;
      const s = window.getSelection();
      if (!s || s.isCollapsed) return;
      const vEl = s.anchorNode?.parentElement?.closest('.verse');
      if (!vEl) return;
      const v = versesRef.current.find(x => String(x.verse) === vEl.dataset.verse);
      if (!v) return;
      // Take the offsets off the range the reader actually dragged. Searching the verse for the
      // selected string instead would anchor every repeated phrase to its first occurrence.
      const r = s.getRangeAt(0);
      const ns = verseTextNodes(vEl);
      let [start, end] = [offsetOf(ns, r.startContainer, r.startOffset), offsetOf(ns, r.endContainer, r.endOffset)];
      if (start < 0 || end < 0) return;
      if (start > end) [start, end] = [end, start];   // a backwards drag
      [start, end] = trimSpan(v.text, start, end);
      const q = v.text.slice(start, end);             // from the verse, so a footnote marker inside the drag is not part of the quote
      if (!q) return;
      setSel({ verse: v.verse, quote: q, anchor: { start, end }, rect: r.getBoundingClientRect() });
    };
    document.addEventListener('mouseup', on);
    return () => document.removeEventListener('mouseup', on);
  }, [versesRef, setSel, off]);
}
