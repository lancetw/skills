// The sticky-notes column: the agent conversation, its SSE turn stream, and the log that survives
// a refresh. Messages are stored as data, not as HTML — the markdown is rendered (and sanitised)
// on the way to the screen every time.
import {
  html, useRef, useState, useEffect, useCallback,
  Slot, mdHtml, local, useTicker, TOOL_ZH, Fragment, ThinkingOrb, BorderBeam,
} from './lib.js';
import { Check, Alert, Stop } from './icons.js';

const LOG_KEY = 'chatlog2';     // v1 stored raw innerHTML; this one stores messages
let seq = 0;
const nid = () => `m${++seq}${Date.now().toString(36)}`;

// 「請選擇 (1-N)」→ 按鈕
function options(text) {
  if (!/請選擇\s*\(1-\d\)/.test(text)) return null;
  const opts = [...text.matchAll(/^\s*(\d)[\.、．]\s*(.+)$/gm)].slice(-6);
  return opts.length ? opts.map(([, n, t]) => [n, t.slice(0, 60)]) : null;
}

export function useChat({ openChat, onNote }) {
  const [messages, setMessages] = useState(() => {
    const saved = local.json(LOG_KEY, []);
    return Array.isArray(saved) ? saved.map(m => ({ ...m, pending: false, act: null })) : [];
  });
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState('');
  const [statusTone, setStatusTone] = useState('');
  const say = (text, tone = 'busy') => { setStatus(text); setStatusTone(text ? tone : ''); };
  const [input, setInput] = useState('');
  const inputRef = useRef(null);
  const sendSlot = useRef(null);

  // the agent session itself lives on the server; only the transcript is kept here
  useEffect(() => {
    const keep = messages.map(({ act, pending, ...m }) => m);
    const s = JSON.stringify(keep);
    local.set(LOG_KEY, s.length > 400000 ? '[]' : s);
  }, [messages]);

  const push = m => { const id = nid(); setMessages(cur => [...cur, { id, ...m }]); return id; };
  const patch = (id, fn) => setMessages(cur => cur.map(m => (m.id === id ? fn(m) : m)));

  // reads one SSE stream of turn events into a bubble; shared by a fresh turn and a reattached one
  const consume = useCallback(async (res, botId) => {
    let finished = false, buf = '';
    const finish = () => { finished = true; patch(botId, m => ({ ...m, pending: false, act: null })); setRunning(false); };
    const rd = res.body.getReader(), dec = new TextDecoder();
    let rest = '';
    for (;;) {
      const { value, done } = await rd.read();
      if (done) break;
      rest += dec.decode(value, { stream: true });
      let i;
      while ((i = rest.indexOf('\n\n')) >= 0) {
        const line = rest.slice(0, i); rest = rest.slice(i + 2);
        if (!line.startsWith('data: ')) continue;
        const ev = JSON.parse(line.slice(6));
        if (ev.type === 'text') {
          buf += ev.text + '\n';
          const t = buf;
          patch(botId, m => ({ ...m, text: t, act: '撰寫中…', orb: 'composing' }));
          say('撰寫中…');
        } else if (ev.type === 'tool') {
          const z = TOOL_ZH[ev.name] || ev.name;
          say(`${z}…`);
          patch(botId, m => ({ ...m, act: `${z}…`, orb: 'searching', steps: [...(m.steps || []), `${ev.name} ${ev.input}`] }));
        } else if (ev.type === 'note') {
          onNote(ev.note);
        } else if (ev.type === 'done') {
          finish();
          say(`完成 · ${ev.turns} turns`, ev.is_error ? 'err' : 'ok');
          sendSlot.current?.flash?.('完成');
          push({ kind: 'tool', tone: ev.is_error ? 'err' : 'ok', text: `${ev.turns} turns${ev.is_error ? ' · ERROR' : ''}` });
          const o = options(buf);
          if (o) push({ kind: 'opts', opts: o });
        } else if (ev.type === 'error') {
          finish();
          say('出錯', 'err');
          push({ kind: 'tool', tone: 'err', text: ev.text });
        }
      }
    }
    if (!finished) {
      finish();
      say('連線中斷，重新整理可接回進行中的回答', 'err');
      push({ kind: 'tool', tone: 'err', text: '串流在 done 之前結束（server 重啟？）' });
    }
  }, [onNote]);

  const send = useCallback(async text => {
    const t = String(text);
    openChat();                                   // a message from anywhere (the verify button included) needs the panel visible
    setRunning(true);
    say('agent 啟動中…');
    push({ kind: 'me', text: t, folded: t.length > 120 || t.includes('\n') });
    const botId = push({ kind: 'bot', text: '', steps: [], act: 'agent 啟動中…', orb: 'connecting', pending: true, t0: Date.now() });
    const res = await fetch('/api/chat', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ message: t }) });
    if (res.headers.get('content-type')?.includes('application/json')) {
      const r = await res.json();
      patch(botId, m => ({ ...m, pending: false, act: null }));
      setRunning(false);
      say(r.error, 'err');
      push({ kind: 'tool', tone: 'err', text: r.error });
      return;
    }
    await consume(res, botId);
  }, [consume, openChat]);

  // after a refresh the server may still be mid-turn: show a pending bubble and attach to its event stream
  const reattach = useCallback(async () => {
    let s;
    try { s = await (await fetch('/api/chat/status')).json(); } catch { return; }
    if (!s.running) return;
    openChat();
    setRunning(true);
    say('agent 處理中（接回）…');
    const botId = push({ kind: 'bot', text: '', steps: [], act: '接回進行中的回答…', orb: 'weaving', pending: true, t0: Date.now() });
    await consume(await fetch('/api/chat/stream'), botId);
  }, [consume, openChat]);

  const clear = () => {
    if (running) return;
    setMessages([]);
    say('');
    fetch('/api/chat/reset', { method: 'POST' });
  };
  const stop = () => { say('停止中…'); fetch('/api/chat/stop', { method: 'POST' }); };
  const note = text => push({ kind: 'tool', text });
  const prefillInput = text => { openChat(); setInput(text); setTimeout(() => inputRef.current?.focus(), 0); };
  const toggleFold = id => patch(id, m => ({ ...m, folded: !m.folded }));

  return { messages, running, status, statusTone, input, setInput, inputRef, sendSlot, send, stop, clear, reattach, note, prefillInput, toggleFold };
}

// Bash/Grep/… lines fold into one closed block per turn, placed before the bubble;
// the bubble already names the current tool
function Steps({ steps }) {
  if (!steps?.length) return null;
  return html`
    <details className="steps">
      <summary>執行細節 · ${steps.length} 步</summary>
      ${steps.map((s, i) => html`<div className="tool" key=${i}>${s}</div>`)}
    </details>`;
}

function Bubble({ m, theme }) {
  const t = useTicker(m.t0, m.pending);
  const body = html`
    <div className=${`msg${m.pending ? ' pending' : ''}`}>
      ${m.pending ? html`
        <div className="act">
          <${ThinkingOrb} state=${m.orb || 'working'} size=${20} className="orb" aria-label=${m.act || '處理中…'} />
          <${Slot} tag="span" className="a" text=${m.act || ''} />
          <span className="t">${t}</span>
        </div>` : null}
      ${m.text ? html`<div dangerouslySetInnerHTML=${mdHtml(m.text)}></div>` : null}
    </div>`;
  return html`
    <${Fragment}>
      <${Steps} steps=${m.steps} />
      ${m.pending
        // the beam reads the bubble's own border-radius, so it stays glued to the card as it grows
        ? html`<${BorderBeam} size="md" colorVariant="sunset" theme=${theme} strength=${0.85} className="beam">${body}<//>`
        : body}
    <//>`;
}

function Message({ m, theme, onFold, onOption }) {
  if (m.kind === 'me') return html`
    <div className=${`msg me${m.folded ? ' fold' : ''}`}>
      <span className="body"><b>你：</b>${m.text}</span>
      ${m.text.length > 120 || m.text.includes('\n')
        ? html`<button className="more" type="button" onClick=${() => onFold(m.id)}>${m.folded ? '展開' : '收合'}</button>`
        : null}
    </div>`;
  if (m.kind === 'tool') return html`
    <div className=${`tool${m.tone ? ' ' + m.tone : ''}`}>
      ${m.tone === 'ok' ? html`<${Check} />` : m.tone === 'err' ? html`<${Alert} />` : null}${m.text}
    </div>`;
  if (m.kind === 'opts') return html`
    <div className="opts">
      ${m.opts.map(([n, t]) => html`<button key=${n} onClick=${() => onOption(n)}>${n}. ${t}</button>`)}
    </div>`;
  return html`<${Bubble} m=${m} theme=${theme} />`;
}

export function Chat({ chat, theme, onGutterDown }) {
  const log = useRef(null);
  useEffect(() => { if (log.current) log.current.scrollTop = 1e9; }, [chat.messages]);
  const empty = chat.messages.length === 0;

  return html`
    <aside id="chat">
      <div id="gutter" title="拖曳調整寬度" onPointerDown=${onGutterDown}></div>
      <div className="chead">
        <span>agent 對話</span>
        <button type="button" id="clear" title="清空對話並重新開始 agent session" disabled=${chat.running} onClick=${chat.clear}>清除</button>
      </div>
      <div id="log" ref=${log}>
        ${chat.messages.map(m => html`<${Message} key=${m.id} m=${m} theme=${theme} onFold=${chat.toggleFold} onOption=${chat.send} />`)}
      </div>
      <div id="guide" hidden=${!empty}>
        <p><b>agent 可以做什麼</b></p>
        <p>問這段經文的任何問題，agent 會依 bible-buddy 流程查原文、背景與資料來源，並把關鍵發現標在左邊的經文上。</p>
        <p className="ex">
          ${[['第 1 節逐字原文分析', '第 1 節逐字原文分析'], ['第一世紀歷史處境', '這段的第一世紀歷史處境'],
             ['常見誤讀與翻譯偏差', '這段常見的誤讀與翻譯偏差'], ['相關經文', '這段的相關經文與引用脈絡']].map(([label, q]) =>
            html`<button type="button" key=${q} onClick=${() => chat.prefillInput(q)}>${label}</button>`)}
        </p>
        <p><b>其他入口</b></p>
        <p>反白經文可以加手動筆記或 ELI5 筆記。<br />「生成 ELI5 筆記」一次掃整段，寫成淺顯易懂的筆記；「未驗證」的可從卡片請 agent 驗證。<br />對話會保留到你按「清除」；換段經文會重新開始。</p>
      </div>
      <div id="status" className=${`tool${chat.statusTone ? ' ' + chat.statusTone : ''}`} role="status">
        ${chat.statusTone === 'ok' ? html`<${Check} />` : chat.statusTone === 'err' ? html`<${Alert} />` : null}
        <${Slot} tag="span" text=${chat.status} />
      </div>
      <form id="f" onSubmit=${e => {
        e.preventDefault();
        if (chat.running) { chat.stop(); return; }
        const t = chat.input.trim();
        if (!t) return;
        chat.setInput('');
        chat.send(t);
      }}>
        <input id="q" ref=${chat.inputRef} value=${chat.input} disabled=${chat.running}
               onChange=${e => chat.setInput(e.target.value)} placeholder="例：以賽亞書 7:14 原文分析" autoComplete="off" />
        <button className=${`primary${chat.running ? ' stop' : ''}`} id="send" type="submit">
          ${chat.running ? html`<${Stop} />` : null}<${Slot} text=${chat.running ? '停止' : '送出'} apiRef=${chat.sendSlot} />
        </button>
      </form>
    </aside>`;
}
